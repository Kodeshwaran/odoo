from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_open_proforma_wizard(self):
        """ Opens the Proforma Invoice wizard """
        self.ensure_one()  # Ensures only one record is being processed
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.wizard',
            'view_mode': 'form',
            'target': 'new',  # Open the wizard in a new window
            'context': {
                'active_id': self.id,  # Pass the current Sale Order ID to the wizard
            }
        }

    def action_proforma_invoice(self):


        return {
            'name': 'Proforma Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.invoice',
            'view_mode': 'tree,form',
            'domain' : [('sale_order_id', '=', self.id)],
            'context': {
                'create': False,
              }
        }