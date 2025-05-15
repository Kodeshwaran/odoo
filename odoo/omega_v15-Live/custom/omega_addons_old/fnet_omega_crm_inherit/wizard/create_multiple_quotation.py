from odoo import api, fields, models, _
from odoo.exceptions import UserError,except_orm

class MultipleQuotationCretationWizard(models.TransientModel):
    _name = 'multiple.quotation.creation.wizard'
    _description = 'Create Multiple Quotation'

    @api.model
    def default_get(self, fields):
        res = super(MultipleQuotationCretationWizard, self).default_get(fields)
        sale_order_id = self.env['sale.order'].browse(self.env.context.get('active_id'))
        if 'product_id' in fields:
            res.update({'sale_order_id': sale_order_id.id, 'currency_id': sale_order_id.currency_id.id})
        result = []
        if 'multiple_quotation_lines' in fields:
            sale_order_search = self.env['sale.order.line'].search(
                [('order_id', '=', self.env.context.get('active_id'))])
            for li in sale_order_search:
                val = (0, 0, {'product_id': li.product_id.id, 'product_qty': li.product_uom_qty, 'price_total': li.price_total,
                              'multiple_quotation_id': self.id,
                              'name': li.name,
                              'product_uom_id': li.product_uom.id,
                              'price_unit': li.price_unit})
                result.append(val)
                res.update({'multiple_quotation_lines': result})
        return res

    @api.depends('multiple_quotation_lines.price_total', 'multiple_quotation_lines.price_unit',
                 'multiple_quotation_lines.product_qty', 'multiple_quotation_lines.tax_id')
    def _amount_all(self):
        for request in self:
            amount_untaxed = tax_amt = 0.0
            for line in request.multiple_quotation_lines:
                amount_untaxed += line.price_subtotal
                tax_amt += line.price_tax

            request.untaxed_amount = request.currency_id.round(amount_untaxed)
            request.tax_amount = request.currency_id.round(tax_amt)
            request.total_amount = request.currency_id.round(tax_amt)
            request.update({
                'untaxed_amount': request.currency_id.round(amount_untaxed),
                'tax_amount': request.currency_id.round(tax_amt),
                'total_amount': amount_untaxed + tax_amt,
            })

    partner_id = fields.Many2one('res.partner', 'Supplier', required=True)
    sale_order_id = fields.Many2one('sale.order', 'Sale Order Line')
    currency_id = fields.Many2one('res.currency', 'Currency')
    multiple_quotation_lines = fields.One2many('multiple.quotation.creation.line.wizard', 'multiple_quotation_id',
                                               'Product Lines')

    def create_purchase_requisition(self):
        for order in self:
            purchase_id = self.env['purchase.order'].create({'partner_id': self.partner_id.id,
                                                             'sale_id': self.env.context.get('active_id')})
            product_selection = False
            for line in order.multiple_quotation_lines:
                if line.select_product:
                    product_selection = True
                    requisition_id = self.env['purchase.order.line'].create(
                        {'product_id': line.product_id.id,
                         'name': line.name,
                         'product_qty': line.product_qty,
                         'price_unit': line.price_unit,
                         'currency_id': order.currency_id.id,
                         'product_uom': line.product_uom_id.id,
                         'order_id': purchase_id.id,
                         'date_planned': fields.datetime.now(),
                         })
            if not product_selection:
                raise UserError(_('Please select any product or close this form...'))

class multiple_quotation_creation_line_wizard(models.TransientModel):
    _name = 'multiple.quotation.creation.line.wizard'
    _description = 'Create Multiple Quotation line Wizard'

    @api.depends('product_qty', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.tax_id.compute_all(line.price_unit, line.multiple_quotation_id.currency_id,
                                            line.product_qty)
            line.update({
                'price_tax': sum(t.get('price_total', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
        return True

    @api.model
    def _default_qty(self):
        purchase_request_line = self.env['purchase.request.line'].browse(self.env.context.get('active_id'))
        return purchase_request_line.quantity

    multiple_quotation_id = fields.Many2one('multiple.quotation.creation.wizard', 'Multiple Quotation ID')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_id = fields.Many2one('product.uom', 'Product UOM')
    name = fields.Text('Description')
    product_qty = fields.Float('Product Qty', default=_default_qty, readonly=True)
    price_unit = fields.Float('Unit Price')
    price_tax = fields.Float(string='Tax', store=True, compute='_compute_amount')
    tax_id = fields.Many2many('account.tax','multi_quotation_creation_line_rel', 'multi_quote_id','tax_id', 'Tax')
    price_subtotal = fields.Float(string='Subtotal', store=True, compute='_compute_amount')
    price_total = fields.Float(string='Total', store=True, compute='_compute_amount')
    select_product = fields.Boolean('Choose Product')
