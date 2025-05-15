# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, except_orm


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

    oppor_id = fields.Many2one('crm.lead', 'Enquiry Ref', readonly=True)
    sale_line = fields.One2many('request.so.line', 'tender_id', 'Sale Quotes')
    offer = fields.Float('Offer', digits=(16, 0), readonly=True)
    date_end = fields.Datetime('Date')
    quote_count = fields.Integer(compute='get_count', readonly=True)
    customer_id = fields.Many2one('res.partner', 'Customer Name')
    ordering_date = fields.Date('Scheduled Ordering Date')
    date_end = fields.Datetime('Tender Closing Deadline')
    schedule_date = fields.Date('Scheduled Date', select=True,
                                help="The expected and scheduled delivery date where all the products are received")
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True, default=_get_picking_in)
    currency_id = fields.Many2one("res.currency", string="Currency")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required="1")

    def action_open(self):
        if self.quote_count:
            return super(PurchaseRequisition, self).action_open()
        else:
            raise UserError(_('You cannot validate agreement because there is no sale quote.'))

    def get_count(self):
        """
        This function is return the count of the sale quotations
        """
        count_quote = 0
        # crm_obj=self.env['crm.lead'].search([('oppor_order','=',self.origin)])
        # sale_id = self.env['sale.order'].search([('tender_id', '=', self.id)])
        #
        # for sale in sale_id:
        #     count_quote += 1

        self.quote_count = count_quote

    def open_quotation(self):
        """
        This is used for view the sale quotation against the current tender
        """
        var = []
        if self._context is None:
            context = {}
        res = self.env['ir.actions.act_window'].for_xml_id('sale', 'action_quotations')
        res['context'] = self._context
        # crm_obj=self.env['crm.lead'].search([('oppor_order','=',self.origin)])
        purchase_id = self.env['sale.order'].search([('tender_id', '=', self.id)])
        for i in purchase_id:
            var.append(i.id)
        res['domain'] = [('id', 'in', var)]
        return res

    def make_quotation(self):
        """
        This function is used to create the quotation from purchase tender.
        That quotation is create against the select sale quotes
        """
        result_val = []
        order_cn = []
        count_value = 0
        test_val = []
        desig = ""
        quote_val = self.env['request.so.line'].search([('tender_id', '=', self.id)])
        for ch in quote_val:
            if ch.valid_qoute is True:
                test_val.append(ch.product_id.id)
        chec = set([x for x in test_val if test_val.count(x) > 1])
        if chec:
            raise except_orm('Selection Mistake', 'More than one times you selected the same product ')
        for i in quote_val:
            if i.valid_qoute is True:
                count_value = 1
        if not quote_val:
            raise except_orm('Sale Quotes Missing',
                             'Please first you create RFQs then receive the bids on sale quotes!')
        elif count_value == 0:
            raise UserError(_('Please select any RFQ in sale quotes!'))
        sale_quotation = self.env['sale.order']
        purchase = self.env['purchase.order']
        crm_obj = self.env['crm.lead'].search([('oppor_order', '=', self.origin)], limit=1)
        quotation_count = sale_quotation.search([('opportunity_id', '=', crm_obj.id)])
        if quotation_count:
            raise UserError(_('You can create only one Quotation !'))
        # ~ crm_obj=self.env['crm.lead'].search([('oppor_order','=',self.origin)])
        # ~ self.env.cr.execute('''SELECT hr_job.name FROM hr_job
        # ~ LEFT JOIN hr_employee ON hr_job.id = hr_employee.job_id
        # ~ LEFT JOIN resource_resource ON resource_resource.id = hr_employee.resource_id
        # ~ WHERE resource_resource.user_id = %d'''%(crm_obj.user_id.id))
        # ~ fet_value=self.env.cr.fetchall()

        # ~ val=len(fet_value)
        # ~ if val != 0:
        # ~ desig=fet_value[0][0]

        addr = crm_obj.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'partner_id': crm_obj.partner_id.id or False,
            'source_id': crm_obj.source_id.id or False,
            'campaign_id': crm_obj.campaign_id.id or False,
            'note': crm_obj.env.user.company_id.sale_note or False,
            'medium_id': crm_obj.medium_id.id or False,
            'user_id': crm_obj.user_id.id or False,
            'designation': desig or False,
            'team_id': crm_obj.team_id.id or False,
            'opportunity_id': crm_obj.id or False,
            'enquiry_id': crm_obj.id or False,
            'tender_id': self.id or False,
            'pricelist_id': self.pricelist_id.id or False,
        }
        val = self.env['ir.sequence'].next_by_code('sale.quote')
        quotation = sale_quotation.create(values)

        if quotation:

            value_line = self.env['request.so.line'].search([('tender_id', '=', self.id), ('valid_qoute', '=', True)])
            for prod in value_line:
                ret_value = {
                    'order_id': quotation.id,
                    'sale_call_id': prod.id,
                    'item_no': prod.item_no,
                    'product_id': prod.product_id.id,
                    'product_uom_qty': prod.product_qty,
                    'purchase_id': prod.purchase_id.id,
                    'price_unit': prod.unit_price,
                    'price_subtotal': prod.margin_price,
                }
                line = sale_quotation.env['sale.order.line']
                valu = line.create(ret_value)
                """
                This hided line is used for if sale quotes are create then against purchase quote 
                was converted in purchase order state
                """
                # ~ purchase_res=purchase.search([('id','=',len_val.purchase_id.id)])
                # ~ for purchase_id in purchase_res:
                # ~ res=purchase_id.write({'state':'purchase'})
                not_quotes = purchase.search([('origin', '=', self.name)])
                for val in not_quotes:
                    unbid_id = self.env['request.so.line'].search([('purchase_id', '=', val.id)])
                    bid_id = self.env['request.so.line'].search(
                        [('purchase_id', '=', val.id), ('valid_qoute', '=', True)])
                    if not unbid_id:
                        rfe = val.write({'state': 'cancel'})

                    elif not bid_id:
                        val.write({'state': 'cancel'})
        unquote_line = self.env['request.so.line'].search([('tender_id', '=', self.id), ('valid_qoute', '=', False)])
        quote_line = self.env['request.so.line'].search([('tender_id', '=', self.id), ('valid_qoute', '=', True)])
        for clear_value in unquote_line:
            clear_value.unlink()
        valid_line = self.env['request.so.line'].search([('tender_id', '=', self.id)])

        for i in valid_line:
            order_cn.append(i.purchase_id.id)
            set_val = set(order_cn)
            result_val = list(set_val)
        for re in result_val:
            order_obj = self.env['purchase.order.line'].search([('order_id', '=', re)])
            for order in order_obj:
                val = self.env['request.so.line'].search(
                    [('purchase_id', '=', re), ('product_id', '=', order.product_id.id)])
                if not val:
                    order.unlink()

    def validate(self):
        for line in self.sale_line:
            percen = line.unit_price * line.margins
            percen_tot = percen + line.unit_price
            total = line.product_qty * percen_tot
            line.write({'margin': percen_tot, 'margin_price': total})
        return True

    def _so_create(self, obj, line):
        vals = {
            'partner_id': self.oppor_id.partner_id.id,
            # ~ 'client_order_ref':self.lead_seq_id.client_order_ref,
            'tender_id': self.id,
            'enquiry_id': self.oppor_id.id,
            'offer': 'OFFER ' + str(int(self.offer)),
        }
        sale_obj = self.env['sale.order'].create(vals)
        for prod in line:
            vals = {
                'order_id': sale_obj.id,
                'sale_call_id': prod.id,
                'product_id': prod.product_id.id,
                'product_uom_qty': prod.product_qty,
                'purchase_id': prod.purchase_id.id,
                'price_unit': prod.margin,
                'item_no': prod.item_no,
            }

            k = self.env['sale.order.line'].create(vals)
        self.offer += 1
        return sale_obj

    def so_quote(self):
        call_obj = self.browse()
        sale_sr = self.env['sale.order'].search([('tender_id', '=', self.id)])
        line = []
        for sale in self.sale_line:
            if sale.valid_qoute:
                line.append(sale)
        sale = self._so_create(call_obj, line)
        val = self.env['purchase.order'].search([('requisition_id', '=', self.id)])
        val.write({'po_sale_ids': [(6, 0, [sale])]})
        return True

    def po_confirm(self):
        pur_line = [pur.id for pur in self.purchase_ids]
        pro_line = [prodline.purchase_id.id for prodline in self.sale_line if prodline.valid_qoute]
        rm_list = [val for val in pur_line if val not in pro_line]
        if rm_list:
            for i in rm_list:
                po_obj = self.env['purchase.order'].browse(i)
                po_obj.button_cancel()
        pro1_line = [line_prod.purchase_line_id.id for line_prod in self.sale_line if line_prod.valid_qoute == False]
        if pro1_line:
            for rec in pro1_line:
                po_obbj = self.env['purchase.order.line'].browse(rec)
                po_obbj.unlink()
        pro1 = [line_prod.purchase_id.id for line_prod in self.sale_line if line_prod.valid_qoute == True]
        for produ in pro1:
            po = self.env['purchase.order'].browse(produ)
            po.draft()
            po.load_currency()
        ######## Sale line update ########
        sa_line = []
        sa = [sal for sal in self.sale_line if sal.valid_qoute == False]
        for s in sa:
            k = self.env['sale.order.line'].search([('sale_call_id', '=', s.id)])
            if k:
                sa_line.append(k[0])
        for i in sa_line:
            sol = self.env['sale.order.line'].browse(i)
            sol.unlink()
        return self.write({'state': 'done'})


class SoRequestLine(models.Model):
    _name = 'request.so.line'
    _order = 'product_id asc, partner_id asc'

    tender_id = fields.Many2one('purchase.requisition', 'Purchase requesting')
    valid_qoute = fields.Boolean('Select')
    purchase_id = fields.Many2one('purchase.order', 'Purchase Quote', readonly=True)
    purchase_line_id = fields.Many2one('purchase.order.line', 'Purchase Line')
    partner_id = fields.Many2one('res.partner', 'Supplier', readonly=True)
    purchase_cost_history_id = fields.Many2one('cost.history.line', 'Cost History')
    offer = fields.Char('Offer', size=64, readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_qty = fields.Float('Quantity', readonly=True)
    ot_unit_price = fields.Float('Unit Price', readonly=True)
    ot_total_price = fields.Float('Total Price', readonly=True)
    unit_price = fields.Float('AED Unit Price', readonly=True)
    total_price = fields.Float('AED Total Price', readonly=True)
    margins = fields.Float('Margin % ')
    margin = fields.Float('Margin Price', readonly=True)
    margin_price = fields.Float('Customer Price', readonly=True)
    item_no = fields.Char('Item No')
    currency_id = fields.Many2one("res.currency", string="Currency")
