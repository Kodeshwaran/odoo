from odoo import api, fields, models, _
# ~ import uuid
from odoo.exceptions import UserError, except_orm
import json
from odoo.tools import html2plaintext


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tender_id = fields.Many2one('purchase.requisition', 'Tender Reference')
    enquiry_id = fields.Many2one('crm.lead', 'Customer Enquiry')
    amendment_notes = fields.Text('Manager notes')
    state = fields.Selection([('draft', 'Draft'),
                              ('to approve', 'Waiting For Approve'),
                              ('approved', 'Approved'),
                              ('sent', 'Quotation Sent'),
                              ('won', 'Quotation Won'),
                              ('drop', 'Quotation Drop'),
                              ('lost', 'Quotation Lost'),
                              ('hold', 'Quotation Hold'),
                              ('amendmend', 'Amendmend'),
                              ('sale', 'Sale Order'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled'),
                              ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange',
                             default='draft')
    covering_notes = fields.Text(string='Covering Letter notes')
    tax_notes = fields.Text(string='Tax notes', default="Quoted prices are exclusive of VAT")
    quotation_notes = fields.Html('Notes')
    confirmation_date = fields.Date(string="Confirmation Date")
    delivery_term = fields.Char('Delivery Term')
    validity = fields.Integer("Validity(Days)")
    po_number = fields.Char('PO Number')
    po_date = fields.Date('PO Date')
    shipment_mode = fields.Many2one('shipment.mode', string='Shipment Mode')
    omega_trn_no = fields.Char("Omega TRN No.", related='company_id.vat', store=True, readonly=True)
    customer_trn_no = fields.Char("Customer TRN No.", related='partner_id.vat', store=True)
    bank_name = fields.Many2one("res.partner.bank", string="Bank Name")
    exchange_rate = fields.Float("Exchange Rate")
    quotation_name = fields.Char(string='Quotation Reference', required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _('New'))
    is_expiry_warning = fields.Boolean(compute='check_expiry_date_past')

    @api.depends('partner_id')
    def check_expiry_date_past(self):
        for rec in self:
            rec.is_expiry_warning = False
            today_date = fields.Date.today()
            if rec.partner_id.expiry_date:
                if rec.partner_id.expiry_date < today_date:
                    rec.is_expiry_warning = True
                else:
                    rec.is_expiry_warning = False
            else:
                rec.is_expiry_warning = False
    def name_get(self):
        result = []
        for sale in self:
            name = sale.name if sale.state in ['sale', 'done'] else sale.quotation_name
            result.append((sale.id, name))
        return result

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        seq_date = None
        if 'date_order' in vals:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
        if vals.get('quotation_name', 'New') == 'New':
            vals['quotation_name'] = self.env['ir.sequence'].next_by_code('sale.quotation', sequence_date=seq_date) or _('New')
        return res


    @api.onchange('currency_id')
    def onchange_currency_id(self):
        result = {}
        banks = self.env['res.partner.bank'].search([])
        for bank in banks:
            if bank.currency_id == self.currency_id:
                self.bank_name = bank
                self.update({'exchange_rate': self.currency_id.rate})

    def return_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.model
    def get_salesman_url(self):
        self.ensure_one()
        val = self.user_id.partner_id.with_context(signup_valid=True)._get_signup_url_for_action(
            action='/mail/view',
            model=self._name,
            res_id=self.id)[self.user_id.partner_id.id]

        return val

    def quote_reject(self):
        url_val = self.get_salesman_url()
        resl_id = self.env['res.partner'].search([('id', '=', self.user_id.partner_id.id)])
        body = _("Dear " + self.user_id.name + "\n")

        body += _("\t This (%s) Sale Quotation has been Rejected by %s. \n " % (self.name, self.env.user.name))
        body += _("\n Regards, \n %s." % (self.env.user.name))
        values = {
            'subject': "Sale Quote Rejected",
            'email_to': resl_id.email,
            'body_html': '<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>' % (
            body, url_val),
            'body': '<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>' % (body),
            'res_id': False
        }

        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)

        if msg_id:
            res = msg_id.send(self)
        val = self.env['ir.sequence'].next_by_code('salequote.amend')
        pre_name = self.name
        saleorder_name = val + ' (' + pre_name + ')'
        self.write({'name': saleorder_name})
        self.write({'state': 'amendmend'})

    def approve_quote(self):
        url_val = self.get_salesman_url()
        resl_id = self.env['res.partner'].search([('id', '=', self.user_id.partner_id.id)])
        body = _("Dear " + self.user_id.name + "\n")
        body += _("\t This (%s) Sale Quotation has been Approved by %s. \n " % (self.name, self.env.user.name))
        body += _("\n Regards, \n %s." % (self.env.user.name))
        values = {
            'subject': "Sale Quote Approved",
            'email_to': resl_id.email,
            'body_html': '<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>' % (
            body, url_val),
            'body': '<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>' % (body),
            'res_id': False
        }
        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)
        if msg_id:
            res = msg_id.send(self)
        self.write({'state': 'sent'})

    @api.model
    def get_url(self):
        self.ensure_one()
        val = self.team_id.user_id.partner_id.with_context(signup_valid=True)._get_signup_url_for_action(
            action='/mail/view',
            model=self._name,
            res_id=self.id)[self.team_id.user_id.partner_id.id]
        return val

    @api.model
    def approve_quote_by_team_leader(self):
        values = {}
        url_val = self.get_url()
        if self.team_id.user_id:
            resl_id = self.env['res.partner'].search([('id', '=', self.team_id.user_id.partner_id.id)])
            try:
                body = _("Dear " + resl_id.name + "\n")

                body += _("\t This (%s) Sale Quotation is waiting for your Approval. \n " % (self.name))
                body += _("\n Regards, \n %s." % (self.env.user.name))
                values = {
                    'subject': "Sale Quote Wait for Approval",
                    'email_to': resl_id.email,
                    'body_html': '<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>' % (
                    body, url_val),
                    'body': '<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>' % (body),
                    'res_id': False
                }

                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.create(values)

                if msg_id:
                    res = msg_id.send(self)
                    return res
            except Exception as z:
                print(z)
        return False

    def action_quote_won(self):
        ret_val = self.env['ir.attachment'].search(['|', ('res_id', '=', self.id), ('res_name', '=', self.name)])
        if ret_val:
            data = self.read()[0]
            data['partner_id'] = self._context.get('active_id', [])
            if data['state'] == 'sent':
                # self.env.cr.execute("""update crm_lead  set active = 'False'""")
                self.write({'state': 'won'})
        else:
            raise UserError(_('Please add the files in attachment.'))

    def action_quote_drop(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id', [])
        if data['state'] == 'sent':
            # self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'drop'})

    def action_quote_lost(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id', [])
        if data['state'] == 'sent':
            # self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'lost'})

    def action_quote_hold(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id', [])
        if data['state'] == 'sent':
            # self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'hold'})

    def action_draft(self):

        orders = self.filtered(lambda s: s.state in ['cancel', 'sent', 'hold', 'drop', 'lost'])
        orders.write({
            'state': 'draft',
            'procurement_group_id': False,
        })
        # orders.mapped('order_line').mapped('procurement_ids').write({'sale_line_id': False})

    def action_confirm_quote(self):
        self.write({'state': 'sent'})

    def print_quotation(self):
        if self.state == 'draft':
            ret = self.validate_profit_percentage()
            if ret:
                return True
            else:
                return super(SaleOrder, self).print_quotation()
        return super(SaleOrder, self).print_quotation()

    # def action_confirm(self):
    #     res = super(SaleOrder, self).action_confirm()
    #     for rec in self:
    #         if rec.tender_id:
    #             bids = self.order_line.mapped('bid_id').ids
    #             for bid in rec.tender_id.bid_received_line:
    #                 if bid.id not in bids:
    #                     bid.purchase_order_id.write({'state': 'cancel'})
    #             sales = self.env['sale.order'].search([('origin', '=', rec.tender_id.name), ('id', '!=', rec.id)])
    #             if sales:
    #                 for sale in sales:
    #                     sale.write({'state': 'cancel'})
    #     return res


class saleorder_approve(models.Model):
    _name = 'approve.limit'
    _description = 'saleorder_approve'

    name = fields.Char('Name', size=15)
    active = fields.Boolean('Active', default=True)
    values = fields.Float('Value')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_unit_price = fields.Float('Purchase Unit Price', readonly=True)
    purchase_total_price = fields.Float('Purchase Total Price', readonly=True)
    bid_id = fields.Many2one('bid.received.line', string="Bid")
    item_no = fields.Char('Item No')
    # note = fields.Html("Notes")
    name = fields.Html(string='Description', required=True)

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        # res.update({'product_note': self.note})
        res.update({'item_no': self.item_no})
        return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        price = self.price_unit
        res = super(SaleOrderLine, self).product_uom_change()
        self.price_unit = price
        return res

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        res.update({'product_description_variants': self.name, 'description_picking': self.name})
        return res

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def unlink(self):
        if self.res_model == 'sale.order':
            so = self.env['sale.order'].browse(self.res_id)
            print(so)
            if so.approval_state == 'approved':
                raise UserError('Cannot delete attachments once quotation is approved.')
            else:
                return super(IrAttachment, self).unlink()
        else:
            return super(IrAttachment, self).unlink()

