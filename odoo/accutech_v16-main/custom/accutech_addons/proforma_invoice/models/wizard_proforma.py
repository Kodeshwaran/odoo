from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProformaWizard(models.TransientModel):
    _name = 'proforma.wizard'
    _description = 'Proforma Invoice Wizard'

    proforma_percentage = fields.Float(string="Proforma Percentage", required=True)

    def confirm_proforma(self):
        sale_order_id = self.env.context.get('active_id')
        if not sale_order_id:
            raise UserError(_("No sale order found in context"))

        sale_order = self.env['sale.order'].browse(sale_order_id)

        # Calculate the discount percentage to adjust the unit price
        discount_percentage = self.proforma_percentage / 100.0

        # Create the proforma invoice
        proforma = self.env['proforma.invoice'].create({
            'sale_order_id': sale_order.id,
            'proforma_percentage': self.proforma_percentage,
            'line_ids': [
                (0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'unit_price': line.price_unit *  discount_percentage,  # Apply the discount
                    'subtotal': line.price_subtotal * discount_percentage,  # Update subtotal
                    'item_no': line.display_name,
                    'product_name': line.product_id.name,
                    'tax_ids': [(6, 0, [tax.id for tax in line.tax_id])],
                }) for line in sale_order.order_line
            ],
        })

        # Return action to open the proforma invoice in form view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.invoice',
            'view_mode': 'form',
            'res_id': proforma.id,
        }
