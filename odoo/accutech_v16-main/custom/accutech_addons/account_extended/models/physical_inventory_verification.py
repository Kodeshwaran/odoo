from odoo import models, fields, api, _
from datetime import datetime


class PhysicalInventoryVerification(models.Model):
    _name = 'physical.inventory.verification'
    _description = 'Physical Inventory Verification'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product')
    inventory_datetime = fields.Datetime(
        string='Inventory at Date',
        help="Choose a date to get the inventory at that date",
        default=fields.Datetime.now
    )
    verification_lines = fields.One2many(
        'physical.inventory.verification.line',
        'verification_id',
        string='Verification Lines'
    )

    @api.model
    def default_get(self, fields):
        res = super(PhysicalInventoryVerification, self).default_get(fields)
        print(res)
        if not res['inventory_datetime']:
            return

        stock_history = self.env['stock.quant']
        domain = [('quantity', '>', 0)]
        stock_histories = stock_history.sudo().with_context(to_date=res['inventory_datetime']).search(domain)

        verification_lines_data = []
        added_products = set()  # Track product IDs already added

        for stock in stock_histories:
            product = stock.product_id

            if product.id in added_products:
                # Skip if the product is already added
                continue

            added_products.add(product.id)  # Add product ID to the set
            verification_lines_data.append({
                'product_id': product.id,
                'verified_qty': stock.quantity,
                'uom_id': product.uom_id.id,
                'counted_qty': 0,
            })

        # Clear existing verification lines and add new ones
        res['verification_lines'] = [(5, 0, 0)] + [(0, 0, line) for line in verification_lines_data]
        return res

    # @api.onchange('inventory_datetime')
    # def _onchange_submit_inventory(self):
    #     if not self.inventory_datetime:
    #         return
    #
    #     stock_history = self.env['stock.quant']
    #     domain = [('quantity', '>', 0)]
    #     stock_histories = stock_history.with_context(to_date=self.inventory_datetime).search(domain)
    #
    #     verification_lines_data = []
    #     added_products = set()  # Track product IDs already added
    #
    #     for stock in stock_histories:
    #         product = stock.product_id
    #
    #         if product.id in added_products:
    #             # Skip if the product is already added
    #             continue
    #
    #         added_products.add(product.id)  # Add product ID to the set
    #         verification_lines_data.append({
    #             'product_id': product.id,
    #             'verified_qty': stock.quantity,
    #             'uom_id': product.uom_id.id,
    #             'counted_qty': 0,
    #         })
    #
    #     # Clear existing verification lines and add new ones
    #     self.verification_lines = [(5, 0, 0)] + [(0, 0, line) for line in verification_lines_data]

    def _get_years(self):
        current_year = datetime.now().year
        return [(str(year), str(year)) for year in range(current_year - 10, current_year + 11)]

    fiscal_year = fields.Selection(selection='_get_years', default=str(datetime.now().year), string='Fiscal Year')
    storage_location_id = fields.Many2one(comodel_name='stock.location', string='Storage Location')
    qty_available = fields.Float('On Hand', related='product_id.qty_available')
    inventory_quantity = fields.Float('Verified Qty')
    state = fields.Selection([('draft', 'Draft'),
                              ('to_validate', 'To Validate'),
                              ('verify', 'Verified'),
                              ('reject', 'Rejected')], default='draft', string='Status')

    def action_send_for_approval(self):
        self.write({'state': 'to_validate'})

    def action_validate(self):
        """
        Creates and applies inventory adjustment records for each product in verification_lines.
        """
        inventory_adjustment_model = self.env['stock.quant']

        for rec in self.verification_lines:
            # Create an inventory adjustment record
            inventory_adjustment = inventory_adjustment_model.create({
                'name': f"Adjustment for {rec.product_id.name}",
                'location_id': rec.storage_location_id.id or False,
                'product_id': rec.product_id.id,
                'line_ids': [(0, 0, {
                    'product_id': rec.product_id.id,
                    'product_uom_id': rec.uom_id.id,
                    'product_qty': rec.counted_qty,
                    'location_id': rec.location_id.id or False,
                })],
            })

            # Apply the inventory adjustment
            inventory_adjustment.action_validate()

        # Update the state of the record
        self.write({'state': 'verify'})
        return True

    def action_reject(self):
        self.write({'state': 'reject'})


class PhysicalInventoryVerificationLine(models.Model):
    _name = 'physical.inventory.verification.line'
    _description = 'Physical Inventory Verification Line'

    verification_id = fields.Many2one(
        'physical.inventory.verification',
        string='Verification',
        ondelete='cascade', invisible=True
    )
    location_id = fields.Many2one('stock.location', 'Location')
    product_id = fields.Many2one('product.product', 'Product')
    verified_qty = fields.Float('On Hand Quantity')
    counted_qty = fields.Float('Counted Quantity', readonly=False)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    difference = fields.Float('Difference', compute="_compute_diff_quantity")
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

    @api.depends('counted_qty')
    def _compute_diff_quantity(self):
        for quant in self:
            quant.difference = quant.counted_qty - quant.verified_qty

class InventoryDateWizard(models.TransientModel):
    _name = 'inventory.date.wizard'
    _description = 'Inventory Date Wizard'

    inventory_datetime = fields.Datetime(string='Inventory Date')

    def open_at_date(self):
        """Handle the confirmation logic."""
        return True
