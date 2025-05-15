from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    remarks = fields.Text('Remarks')
    issued_by = fields.Many2one('res.partner', 'Issued By')
    approved_by = fields.Many2one('res.partner', 'Approved By')
    verified_and_received = fields.Many2one('res.partner', 'Verified & Received By')

    def action_send_mail_wizard(self):
        return {
            'name': 'Send Delivery Mail',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'delivery.mail',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_delivery_id': self.id}
        }


