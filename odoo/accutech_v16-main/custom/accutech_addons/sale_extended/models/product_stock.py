from odoo import fields, models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_stock_record_created = fields.Boolean(string="Stock Record Created", default=False)


class ProductStockCompany(models.Model):
    _name = 'product.stock.company'
    _description = 'Product Stock by Company'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    company_1_qty = fields.Integer(string="Accutech Middle East FZCO", compute="_compute_stock_quantities")
    company_2_qty = fields.Integer(string="ABDULLA BIN HAMID TRADING LLC", compute="_compute_stock_quantities")
    company_3_qty = fields.Integer(string="ACCOM TECHNOLOGIES LLC", compute="_compute_stock_quantities")

    def _compute_stock_quantities(self):
        company_ids = self.env['res.company'].search([]).sorted(lambda c: c.id)[:3]
        company_mapping = {company.id: f"company_{i + 1}_qty" for i, company in enumerate(company_ids)}
        stock = self.env['stock.location'].search([
        ])
        for rec in stock:
            print('\n------------', rec.name,rec.company_id.name, '-------rec.name--------')
        for record in self:
            for company_id, field_name in company_mapping.items():
                print('\n------------', company_id, '-------company_id--------')
                output_location = self.env['stock.location'].search([
                    ('name', '=', 'Output'),
                    ('company_id', '=', company_id)
                ], limit=1)
                stock = self.env['stock.location'].search([
                    ('company_id', '=', company_id)
                ])
                print('------------', stock, '-------stock--------')
                stock_location = self.env['stock.location'].search([
                    ('name', '=', 'Stock'),
                    ('company_id', '=', company_id)
                ], limit=1)
                print('------------', output_location, '-------output_location--------')
                print('------------', stock_location, '-------stock_location--------')
                print('------------', record.product_id.name, '-------record.product_id.name--------')

                if output_location and stock_location:
                    output_stock_quant = self.env['stock.quant'].search([
                        ('product_id', '=', record.product_id.id),
                        ('location_id', '=', output_location.id),
                        ('company_id', '=', company_id),
                    ], limit=1)
                    stock_stock_quant = self.env['stock.quant'].search([
                        ('product_id', '=', record.product_id.id),
                        ('location_id', '=', stock_location.id),
                        ('company_id', '=', company_id),
                    ], limit=1)

                    output_qty = output_stock_quant.inventory_quantity_auto_apply or 0.0
                    stock_qty = stock_stock_quant.inventory_quantity_auto_apply or 0.0
                    print('------------', output_qty,stock_qty, '-------output_qty, stock_qty--------')
                    setattr(record, field_name, output_qty - stock_qty)
                elif stock_location:
                    stock_stock_quant = self.env['stock.quant'].search([
                        ('product_id', '=', record.product_id.id),
                        ('location_id', '=', stock_location.id),
                        ('company_id', '=', company_id),
                    ], limit=1)

                    stock_qty = stock_stock_quant.inventory_quantity_auto_apply or 0.0
                    print('------------', stock_qty, '-------stock_qty--------')
                    setattr(record, field_name, stock_qty)
                else:
                    print('------------', "NOTHING", '-------"NOTHING"--------\n')
                    setattr(record, field_name, 0)

    @api.model
    def sync_product_stock(self):

        products = self.env['product.product'].search([('is_stock_record_created', '=', False)])

        for product in products:
            self.create({'product_id': product.id})

            product.is_stock_record_created = True

