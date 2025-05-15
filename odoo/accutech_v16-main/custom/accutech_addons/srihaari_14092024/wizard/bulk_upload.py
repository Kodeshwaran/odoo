
from odoo import api, fields, models, _


class QuotationBulkUpload(models.TransientModel):
    _name = "quotation.bulk.upload"
    _description = 'Bulk Upload'

    sale_id = fields.Many2one('sale.order', "Sale")
    sale_line_ids = fields.One2many('sale.quote.line', 'sale_quote_id', 'Sale')

    @api.model
    def default_get(self, fields):
        res = super(QuotationBulkUpload, self).default_get(fields)
        sale = self.env['sale.order'].browse(self.env.context.get('active_id'))
        res['sale_id'] = sale.id
        return res

    def button_upload_lines(self):
        products = self.sale_line_ids.mapped('product_ids')
        for product in products:
            lines = self.sale_line_ids.filtered(lambda x: product.id in x.product_ids.ids)
            if lines:
                sale = self.env['sale.order'].search([('id', '=', self.sale_id.id)])
                for line in lines:
                    sale_line_creation = {
                            'product_id': product.id,
                            'order_id': sale.id,
                            'product_uom_qty': line.qty if product in line.product_ids else False,
                        }
                    self.env['sale.order.line'].create(sale_line_creation)


class SaleQuoteLine(models.TransientModel):
    _name = "sale.quote.line"
    _description = 'Sale Quote Bulk Upload'


    product_ids = fields.Many2many('product.product', string='Product', required=True)
    sale_line_id = fields.Many2one('sale.order.line', "Sale")
    sale_quote_id = fields.Many2one('quotation.bulk.upload', 'Sale Quote Bulk Upload')
    qty = fields.Float('Quantity', default=1)
