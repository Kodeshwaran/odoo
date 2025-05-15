# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang


class SalePo(models.TransientModel):
    _name = "sale.po"
    _description = 'Sale Po'

    # partner_id = fields.Many2one('res.partner', string="Vendor", required=True)
    sale_id = fields.Many2one('sale.order', "Sale")
    sale_line = fields.One2many('sale.po.line', 'sale_po_id', 'Sale')

    @api.model
    def default_get(self, fields):
        res = super(SalePo, self).default_get(fields)
        sale = self.env['sale.order'].browse(self.env.context.get('active_id'))
        res['sale_id'] = sale.id
        lines = []
        for line in sale.order_line:
            line_dict = {}
            line_dict['item_no'] = line.item_no
            line_dict['model'] = line.model
            line_dict['make'] = line.make
            line_dict['country_id'] = line.country_id.id
            line_dict['product_id'] = line.product_id.id
            line_dict['qty'] = line.product_uom_qty
            line_dict['sale_line_id'] = line.id
            line_dict['price_unit'] = line.price_unit
            line_dict['product_uom'] = line.product_uom.id
            lines.append((0, 0, line_dict))
        res['sale_line'] = lines
        return res

    def create_po(self):
        vendors = self.sale_line.mapped('vendor_ids')

        for vendor in vendors:
            lines = self.sale_line.filtered(lambda x: vendor.id in x.vendor_ids.ids)

            if lines:
                fpos = self.env['account.fiscal.position'].sudo()._get_fiscal_position(vendor)

                existing_pos = self.env['purchase.order'].search([
                    ('sale_id', '=', self.sale_id.id),
                    ('partner_id', '=', vendor.id),
                    ('order_line.product_id', 'in', lines.mapped('sale_line_id.product_id').ids),
                    ('state', 'in', ['draft', 'sent'])
                ])

                if existing_pos:
                    raise ValidationError(
                        "A purchase order for the same vendor and product already exists for this sale order.")

                po_creation = {
                    'partner_id': vendor.id,
                    'fiscal_position_id': fpos.id if fpos else False,
                    'payment_term_id': vendor.property_supplier_payment_term_id.id or False,
                    'sale_id': self.sale_id.id,
                    'opportunity_id': self.sale_id.opportunity_id.id,
                }
                order = self.env['purchase.order'].create(po_creation)

                for line in lines:
                    val_line = {
                        'name': line.sale_line_id.name,
                        'item_no':line.sale_line_id.item_no,
                        'model':line.sale_line_id.model,
                        'make':line.sale_line_id.make,
                        'country_id':line.sale_line_id.country_id.id,
                        'order_id': order.id,
                        'product_id': line.sale_line_id.product_id.id,
                        'sale_line_id': line.sale_line_id.id,
                        'product_qty': line.qty,
                        'price_unit': line.price_unit,
                        'product_uom': line.sale_line_id.product_uom.id,
                        'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        # 'price_unit': 1.0,  # You may want to use the actual price here
                        'display_type': False
                    }
                    self.env['purchase.order.line'].create(val_line)


class SalePoLine(models.TransientModel):
    _name = "sale.po.line"
    _description = 'Sale Po'


    vendor_ids = fields.Many2many('res.partner', string="Vendor")
    sale_po_id = fields.Many2one('sale.po', 'Sale Po')
    # select_line = fields.Boolean('Select')
    sale_line_id = fields.Many2one('sale.order.line', "Sale")
    # deepak
    item_no = fields.Char("Item no")
    model = fields.Char("Model")
    country_id = fields.Many2one('res.country',string="Model")
    make = fields.Char("Make")
    # end
    product_id = fields.Many2one('product.product', 'Product')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    qty = fields.Float('Quantity')
    price_unit = fields.Float('Unit Price')





