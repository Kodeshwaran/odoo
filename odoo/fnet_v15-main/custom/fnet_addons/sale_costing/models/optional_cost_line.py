from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


STATES = [('draft', 'Draft'),
          ('confirm', 'Confirmed'),
          ('done', 'Done'),
          ('reject', 'Rejected'),
          ('cancel', 'Cancelled')]

class UoM(models.Model):
    _inherit = 'uom.uom'

    is_default = fields.Boolean('Set as Default', default=False, store=True)
    is_default_set = fields.Boolean(compute="_compute_default_uom", store=True)
    company_id = fields.Many2one('res.company', 'Company', compute='_compute_fieldvalue', readonly=False, store=True)

    @api.depends('name')
    def _compute_fieldvalue(self):
        for record in self:
            record.company_id = self.env.user.company_id if self.env.user.company_id else ''

    @api.depends('is_default')
    def _compute_default_uom(self):
        for rec in self:
            if rec.is_default:
                rec.write({'is_default_set': True})
            else:
                rec.write({'is_default_set': False})

    @api.onchange('is_default')
    def onchange_select_one(self):
        selected_uom = self.env['uom.uom'].search([('company_id', '=', self.company_id.id), ('is_default', '!=', False), ('id', '!=', False)])
        if selected_uom:
            for uom in selected_uom:
                uom.is_default = False
                uom.is_default_set = False

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_default_uom(self):
        company_id = self.env.company.id
        company_default = self.env['uom.uom'].search([('is_default', '!=', False), ('company_id', '=', company_id)], limit=1)
        return company_default

    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True, default=_get_default_uom, help="Default unit of measure used for all stock operations.")

class OptionalCostLine(models.Model):
    _name = 'optional.cost.line'
    _description = 'Optional Costing Line'

    @api.depends('product_uom_qty', 'price_unit', 'margin_percentage')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * line.product_uom_qty
            margin_total = price * (line.margin_percentage / 100.0)
            line.update({
                'price_subtotal': price,
                'price_total': price + margin_total,
            })

    # @api.depends('price_subtotal', 'price_total', 'costing_id.other_lines.price_total', 'costing_id.conversion_rate',
    #              'costing_id.to_currency_id')
    # def get_selling_price(self):
    #     for line in self:
    #         other_charges = 0
    #         for charge in line.costing_id.other_lines:
    #             if charge.type == 'fixed':
    #                 if charge.include_margin:
    #                     percentage = (line.price_total/sum(line.costing_id.line_ids.mapped('price_total')))*100
    #                     price = charge.amount * (percentage/100)
    #                 else:
    #                     percentage = (line.price_subtotal/sum(line.costing_id.line_ids.mapped('price_subtotal')))*100
    #                     price = charge.amount * (percentage/100)
    #             else:
    #                 base_price_tot = line.price_total if charge.include_margin else line.price_subtotal
    #                 price = base_price_tot * (charge.amount / 100.0)
    #             other_charges += price
    #         line.amount_other_charge = other_charges
    #         line.base_sale_price = line.price_total + other_charges
    #         line.sale_price = line.base_sale_price * line.costing_id.conversion_rate
    #         line.unit_sale_price = ((line.base_sale_price * line.costing_id.conversion_rate) / (line.product_uom_qty or 1))

    costing_id = fields.Many2one('sale.costing', string='Costing Reference', required=True, ondelete='cascade',
                                 index=True)
    cost_line_id = fields.Many2one('sale.cost.line', string='Optional For', required=True, ondelete='cascade',
                                   index=True)
    add_costing = fields.Boolean(default=True, string="Add to Total")
    company_id = fields.Many2one(related='costing_id.company_id', string='Company', store=True, readonly=True,
                                 index=True)
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 ondelete='restrict', check_company=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    # currency_id = fields.Many2one(related='costing_id.currency_id', depends=['costing_id'], store=True,
    #                               string='Currency')

    margin_percentage = fields.Float("Margin(%)")
    # price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal Price', readonly=True, store=True)
    # price_total = fields.Monetary(compute='_compute_amount', string='Total Price', readonly=True, store=True)
    state = fields.Selection(STATES, related='costing_id.state', string='Status', readonly=True, copy=False, store=True,
                             default='draft')
    # Currency and Conversion
    # to_currency_id = fields.Many2one("res.currency", related='costing_id.to_currency_id', string="Selling Currency")
    # conversion_rate = fields.Float("Conversion Rate", related='costing_id.conversion_rate')
    # amount_other_charge = fields.Monetary(compute='get_selling_price', string='Other Charges', store=True)
    # base_sale_price = fields.Monetary(compute='get_selling_price', string='Base Sale Price', store=True)
    # sale_price = fields.Monetary(compute='get_selling_price', string='Sale Price', store=True)
    # unit_sale_price = fields.Monetary(compute='get_selling_price', string='Sale Price/Unit', store=True)

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0
        self.update(vals)

