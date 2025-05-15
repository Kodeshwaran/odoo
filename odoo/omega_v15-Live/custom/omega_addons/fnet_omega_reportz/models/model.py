from odoo import api, models, fields

#
# class Product(models.Model):
#     _inherit = 'product.product'
#
#     hs_code = fields.Char("HSN Code")


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.depends('invoice_origin')
    def _compute_shipment(self):
        for rec in self:
            order = self.env['sale.order'].search([('name', '=', rec.invoice_origin)], limit=1)
            if order:
                rec.shipment_mode = order.shipment_mode.id
                rec.delivery_term = order.delivery_term if order.delivery_term else False
                rec.po_number = order.po_number if order.po_number else False
                rec.po_date = order.po_date if order.po_date else False
            else:
                rec.shipment_mode = False
                rec.delivery_term = False
                rec.po_number = False
                rec.po_date = False

    shipment_mode = fields.Many2one('shipment.mode', string="Shipment Method", compute='_compute_shipment')
    delivery_term = fields.Char('Delivery Term', compute='_compute_shipment')
    po_date = fields.Date(string="PO date", compute='_compute_shipment', store=True)
    po_number = fields.Char('PO Number', compute='_compute_shipment', store=True)
    package_name = fields.Char("Package")
    package_dimension = fields.Char("Package Dimension")
    package_net = fields.Char("Net Weight")
    package_gross = fields.Char("Gross Weight")


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    cost_origin = fields.Char("COO")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def get_line_note(self, line):
        notes = line.note or line.product_id.name
        if notes:
            notes.replace('<p>', '')
            notes.replace('</p>', '')
            return notes
        return notes
