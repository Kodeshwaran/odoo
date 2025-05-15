from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('po_receive', 'Customer PO Recieved'),('sale',)])
    attachment = fields.Many2many('ir.attachment','customer_attachment_rel', string="Customer PO Attachment")
    vendor_attachment=fields.Many2many('ir.attachment','vendor_attachment_rel',string="Vendor PO Attachment")
    # vendor_attachment_file = fields.Char('Vendor PO Attachment')


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.opportunity_id and not self.opportunity_id.stage_id.is_won:
            raise ValidationError("Move the respective Opportunity to Won stage before confirming the quotation")
        return res

    def receive_po(self):
        if not self.attachment:
            raise ValidationError("Customer PO is not attached")
        else:
            self.write({'state': 'po_receive'})


