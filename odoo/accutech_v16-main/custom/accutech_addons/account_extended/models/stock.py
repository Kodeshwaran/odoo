# -*- coding: utf-8 -*-

from odoo import models, fields, api



class StockPicking(models.Model):
    _inherit = "stock.picking"

    package_name = fields.Char("Package")
    package_dimension = fields.Char("Package Dimension")
    package_net = fields.Char("Net Weight")
    package_gross = fields.Char("Gross Weight")
    cardboard_box = fields.Char("Cardboard Box")
    shipping_point = fields.Char("Shipping Point")
    delivery_basis = fields.Char("Delivery Basis")
    mode_of_transport = fields.Char("Mode Of Transport")
    country_id = fields.Many2one('res.country',"Country of Final Destination")
    ref = fields.Char("Ref")
    invoice_no = fields.Char("Invoice Number")

class StockPickingLine1(models.Model):
    _inherit = "stock.move"

    item_no = fields.Char(
        string="Item Number",
        related='product_id.item_no',
        store=True
    )
    country_id = fields.Many2one(
        'res.country',
        related='product_id.origin_country_id',
        store=True,
        readonly=True,
        string="Country/Region of Origin",
        help="Select the country associated with this record."
    )
    model = fields.Char(
        string="Model",
        related='product_id.model',
        store=True,
        readonly=True
    )
    make = fields.Char(
        string="Make",
        related='product_id.make',
        store=True,
        readonly=False
    )
    parameter_1 = fields.Text(
        string='Parameter 1',
        related='product_id.parameter_1',
        readonly=True,
        store=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set the item_no field based on the selected product_id."""
        if self.product_id:
            self.item_no = self.product_id.item_no

    @api.onchange('item_no')
    def _onchange_item_no(self):
        """Update product fields based on the entered item_no."""
        if self.item_no:
            product = self.env['product.product'].search([('item_no', '=', self.item_no)], limit=1)
            if product:
                self.product_id = product.id
                # self.product_uom_id = product.uom_id.id  # Use `product_uom_id` for account.move.line
                self.price_unit = product.lst_price  # Default to the sales price
            else:
                self.product_id = False
                # self.product_uom_id = False
                self.price_unit = 0.0


class AccountMoveLine1(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"

    item_no = fields.Char(
            string="Item Number",
            store=True
        )
    country_id = fields.Many2one(
        'res.country',
        related='product_id.origin_country_id',
        store=True,
        readonly=True,
        string="Country/Region of Origin",
        help="Select the country associated with this record."
    )
    model = fields.Char(
        string="Model",
        related='product_id.model',
        store=True,
        readonly=True
    )
    make = fields.Char(
        string="Make",
        related='product_id.make',
        store=True,
        readonly=False
    )
    parameter_1 = fields.Text(
        string='Parameter 1',
        related='product_id.parameter_1',
        readonly=True,
        store=True
    )
    hsc = fields.Char("HSC Code")
    remark = fields.Char("Remarks")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set the item_no field based on the selected product_id."""
        if self.product_id:
            self.item_no = self.product_id.item_no

    @api.onchange('item_no')
    def _onchange_item_no(self):
        """Update product fields based on the entered item_no."""
        if self.item_no:
            product = self.env['product.product'].search([('item_no', '=', self.item_no)], limit=1)
            if product:
                self.product_id = product.id
                self.product_uom_id = product.uom_id.id  # Use `product_uom_id` for account.move.line
                self.price_unit = product.lst_price  # Default to the sales price
            else:
                self.product_id = False
                self.product_uom_id = False
                self.price_unit = 0.0


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    item_no = fields.Char(string="Item Number")
    country_id = fields.Many2one(
        'res.country',
        related='product_id.origin_country_id',
        store=True,
        readonly=True,
        string="Country/Region of Origin",
        help="Select the country associated with this record."
    )
    model = fields.Char(
        string="Model",
        related='product_id.model',
        store=True,
        readonly=True
    )
    make = fields.Char(
        string="Make",
        related='product_id.make',
        store=True,
        readonly=True
    )
    parameter_1 = fields.Text(
        string="Parameter 1",
        related='product_id.parameter_1',
        readonly=True,
        store=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set the item_no field based on the selected product_id."""
        if self.product_id:
            self.item_no = self.product_id.item_no

    @api.onchange('item_no')
    def _onchange_item_no(self):
        """Update product fields based on the entered item_no."""
        if self.item_no:
            product = self.env['product.product'].search([('item_no', '=', self.item_no)], limit=1)
            if product:
                self.product_id = product.id
                self.product_uom_id = product.uom_id.id  # Use `product_uom_id` for account.move.line
                # self.price_unit = product.lst_price  # Default to the sales price
            else:
                self.product_id = False
                self.product_uom_id = False
                # self.price_unit = 0.0

    @api.model
    def _get_inventory_fields_create(self):
        res = super()._get_inventory_fields_create()
        res.append('item_no')
        return res