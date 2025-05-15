from odoo import models, fields, _
from odoo import api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, except_orm
import json


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    @api.model
    def _get_picking_in(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])

        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])

        return types[:1]

    oppor_id = fields.Many2one('crm.lead', 'Enquiry Reference', required=True)
    bid_received_line = fields.One2many('bid.received.line', 'tender_id', 'Sale Quotes')
    quote_count = fields.Integer(compute='get_count', readonly=True)
    customer_id = fields.Many2one('res.partner', 'Customer Name')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=False, default=_get_picking_in)
    # confirm_date = fields.Date('In Progress Date')

    @api.model
    def create(self, vals):
        record = super(PurchaseRequisition, self).create(vals)
        record['name'] = self.env['ir.sequence'].next_by_code('new.purchase.requisition') or _('New')
        return record

    def action_open(self):
        if self.quote_count:
            return super(PurchaseRequisition, self).action_open()
        else:
            raise UserError(_('You cannot validate agreement because there is no sale quote.'))

    def get_count(self):
        self.quote_count = len(self.env['sale.order'].search([('tender_id', '=', self.id)]))

    def open_quotation(self):
        """
        This is used for view the sale quotation against the current tender
        """
        return {
            'name': _('Sale Quotes'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'domain': [('tender_id', '=', self.id)],
        }

    # def action_in_progress(self):
    #     self.write({'confirm_date': fields.Date.today()})
    #     res = super(PurchaseRequisition, self).action_in_progress()
    #     return res

    def make_quotation(self):
        """
        This function is used to create the quotation from purchase tender.
        That quotation is create against the selected sale quotes
        """
        count_value = 0
        test_val = []
        # if self.quote_count > 0:
        #     raise UserError(_('You can create only one Quotation!. Please delete the existing sale quotation.'))
        if not self.bid_received_line or not self.bid_received_line.filtered(lambda x: x.valid_qoute == True):
            raise UserError(_('Please process the RFQ and select any RFQ in sale quotes!'))
        if not self.customer_id:
            raise UserError(_("Please select customer to create quotation."))
        for ch in self.bid_received_line:
            if ch.valid_qoute is True:
                test_val.append(ch.product_id.id)
        check = set([x for x in test_val if test_val.count(x) > 1])
        if check:
            raise UserError(_('More than one times you selected the same product '))
        sale_quotation = self.env['sale.order']
        purchase = self.env['purchase.order']
        crm_obj = self.env['crm.lead'].search([('id', '=', self.oppor_id.id)], limit=1)
        quotation = sale_quotation.create({
                                            'partner_id': self.customer_id.id or False,
                                            'source_id': crm_obj.source_id.id or False,
                                            'campaign_id': crm_obj.campaign_id.id or False,
                                            'note': crm_obj.description or False,
                                            'medium_id': crm_obj.medium_id.id or False,
                                            'user_id': crm_obj.user_id.id or False,
                                            'team_id': crm_obj.team_id.id or False,
                                            'opportunity_id': crm_obj.id or False,
                                            'enquiry_id': crm_obj.id or False,
                                            'tender_id': self.id or False,

                                        })
        for len_val in self.bid_received_line.filtered(lambda x: x.valid_qoute == True):
            ret_value = {
                'order_id': quotation.id,
                'product_id': len_val.product_id.id,
                'product_uom_qty': len_val.quantity,
                'price_unit': len_val.unit_price,
                'product_uom': len_val.unit_measure.id,
                'purchase_unit_price': len_val.purchase_unit_price,
                'purchase_total_price': len_val.purchase_total_price,
                'bid_id': len_val.id,
            }
            line = sale_quotation.env['sale.order.line']
            line.create(ret_value)
            # not_quotes = purchase.search([('origin', '=', self.name)])
            # for val in not_quotes:
            #     unbid_id = self.env['bid.received.line'].search([('purchase_order_id', '=', val.id)])
            #     bid_id = self.env['bid.received.line'].search(
            #         [('purchase_order_id', '=', val.id), ('valid_qoute', '=', True)])
            #     if not unbid_id:
            #         val.write({'state': 'cancel'})
            #     elif not bid_id:
            #         val.write({'state': 'cancel'})
        # unquote_line = self.bid_received_line.filtered(lambda x: x.valid_qoute == False)
        # for clear_value in unquote_line:
        #     clear_value.unlink()

    def create_rfq(self):
        if not self.line_ids:
            raise UserError("No Products Found..!")
        vendors = self.line_ids.mapped('vendor_ids')
        for vendor in vendors:
            lines = self.line_ids.filtered(lambda x: vendor.id in x.vendor_ids.ids)
            if lines:
                fpos = self.env['account.fiscal.position'].sudo().get_fiscal_position(vendor.id)
                po_creation = {
                    'partner_id': vendor.id,
                    'fiscal_position_id': fpos.id if fpos else False,
                    'payment_term_id': vendor.property_supplier_payment_term_id.id or False,
                    'company_id': self.company_id.id,
                    'currency_id': self.company_id.currency_id.id,
                    'origin': self.name,
                    'partner_ref': self.name,  # to control vendor bill based on agreement reference
                    'notes': self.description,
                    'date_order': self.date_end or fields.Datetime.now(),
                    'picking_type_id': self.picking_type_id.id,
                    'requisition_id': self.id,
                    'enquiry_id': self.oppor_id.id,
                }
                order = self.env['purchase.order'].create(po_creation)
                for line in lines:
                    seller = line.product_id.seller_ids.filtered(lambda s: s.name.id == vendor.id)
                    if seller:
                        price_unit = seller.price
                    else:
                        price_unit = 0.0
                    order_lines = {
                        'name': line.product_id.description or line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom_id.id,
                        'product_qty': line.product_qty,
                        'price_unit': price_unit,
                        'date_planned': self.schedule_date or fields.Date.today(),
                        'account_analytic_id': line.account_analytic_id.id,
                        'requisition_line_id': line.id,
                        'order_id': order.id,
                    }
                    self.env['purchase.order.line'].create(order_lines)


class BidReceivedLine(models.Model):
    _name = 'bid.received.line'
    _description = 'bid_received_line'

    tender_id = fields.Many2one('purchase.requisition', 'Tender Reference')
    valid_qoute = fields.Boolean('Select')
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Quotes', readonly=True)
    vender_id = fields.Many2one('res.partner', 'Supplier', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    unit_measure = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True)
    purchase_unit_price = fields.Float('Purchase Unit Price', readonly=True)
    unit_price = fields.Float('Unit Price', readonly=True)
    purchase_total_price = fields.Float('Purchase Price', readonly=True)
    sub_total = fields.Float('Sub Total', readonly=True)

    def update_price(self):
        line_id = self.env['purchase.requisition.line'].search([('product_id', '=', self.product_id.id)])
        if line_id:
            line_id.update({'price_unit': self.unit_price})


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    vendor_ids = fields.Many2many('res.partner', string="Vendor")
    product_description_variants = fields.Html("Description")

    # vendor_ids_domain = fields.Char(
    #
    #     readonly=True,
    #     store=False,
    # )

    @api.onchange('product_id')
    def vendor_ids_onchange(self):
        pricelist = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])
        self.product_description_variants = self.product_id.name
        if pricelist:
            return {'domain': {'vendor_ids': [('is_vendor', '!=', False), ('id', 'in', pricelist.mapped('name').ids)]}}
        else:
            return {'domain': {'vendor_ids': [('is_vendor', '!=', False)]}}

    # @api.depends('product_id')
    # def _compute_vendor_ids_domain(self):
    #     for rec in self:
    #         domain = []
    #         if rec.product_id:
    #             domain.append(('is_vendor', '!=', False))
    #             pricelist = self.env['product.supplierinfo'].search(
    #                 [('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id)])
    #             if pricelist:
    #                 domain.append(',')
    #                 domain.append(('id', 'in', pricelist.mapped('name').ids))
    #         rec.vendor_ids_domain = domain

