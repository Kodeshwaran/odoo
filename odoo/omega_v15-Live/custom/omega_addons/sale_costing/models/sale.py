from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_costing_id = fields.Many2one('sale.costing', string="Costing")
    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="[('type', '!=', 'private'), ('company_id', 'in', (False, company_id))]", )
    contact_name_id = fields.Many2one('res.partner', 'Contact Name')
    sale_no = fields.Char('File No', copy=False,  default=lambda self: _('New'))

    # @api.onchange('sale_no')
    # def onchange_sale_no(self):
    #     self.tender_id.sale_no = self.sale_no


    @api.model
    def create(self, vals):
        if vals.get('sale_no', _('New')) == _('New'):
            vals['sale_no'] = self.env['ir.sequence'].next_by_code('sale.order.no') or _('New')
        return super(SaleOrder, self).create(vals)

    @api.onchange('partner_id')
    def onchange_partner_contact(self):
        self.contact_name_id = False
        if self.partner_id:
            contacts = self.partner_id.child_ids.ids
            if contacts:
                self.contact_name_id = contacts
            return {'domain': {'contact_name_id': [('id', 'in', contacts)]}}

    def action_revision(self):
        if self.sale_costing_id:
            raise UserError(_("Please revise the costing sheet to revise the quotation!"))
        return super(SaleOrder, self).action_revision()