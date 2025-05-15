# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_id = fields.Many2one('sale.order', 'Sale')
    purchase_order_line = fields.One2many('purchase.order.line', 'order_id', string='Product Line', copy=True)
    po_type = fields.Selection(
        selection=[
            ('direct_po', 'Direct PO'),
            ('sale_po', 'Sale PO'),
        ],
        string='PO Type'
    )
    opportunity_id = fields.Many2one('crm.lead')
    is_purchase_approval = fields.Boolean(compute='_compute_purchase_approval')
    main_discount = fields.Float(string='Disc.', digits='Discount', default=0.000)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'RFQ Sent'),
        ('bid_received', 'Bid Received'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    purchase_reference = fields.Char("Reference")
    purchase_contact = fields.Char("Contact Person")

    def _get_next_number(self):
        """ Override this method if you want custom logic for number generation """
        # Call the super method or custom logic
        return super(PurchaseOrder, self)._get_next_number()

    @api.model
    def combine_rfqs(self):
        selected_orders = self.env['purchase.order'].browse(self._context.get('active_ids'))
        if not selected_orders:
            raise UserError("No RFQs selected.")

        # Validate that all selected RFQs have the same partner
        partners = selected_orders.mapped('partner_id')
        if len(partners) > 1:
            raise UserError("Please select RFQs for the same partner only.")

        grouped_orders = {}

        # Group RFQs by partner_id
        for order in selected_orders:
            if order.partner_id not in grouped_orders:
                grouped_orders[order.partner_id] = self.env['purchase.order']
            grouped_orders[order.partner_id] |= order

        for partner, orders in grouped_orders.items():
            if len(orders) > 1:
                # Combine lines into a new RFQ
                combined_lines = []
                for order in orders:
                    if not order.order_line:
                        continue  # Skip orders without lines
                    for line in order.order_line:
                        combined_lines.append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_qty': line.product_qty,
                            'price_unit': line.price_unit,
                            'name': line.name,
                            'date_planned': line.date_planned,
                        }))

                if not combined_lines:
                    raise UserError("No lines to combine for partner: {}".format(partner.name))

                # Generate the new RFQ number using the sequence
                seq = self.env['ir.sequence'].next_by_code('purchase.order.combined')
                if not seq:
                    raise UserError("The sequence for 'purchase.order.combined' is missing or not configured properly.")

                # Create the new combined RFQ
                new_order = self.env['purchase.order'].create({
                    'partner_id': partner.id,
                    'order_line': combined_lines,
                    'origin': ', '.join(orders.mapped('name')),
                    'name': seq,  # Use the generated sequence here
                })

                # Move the original RFQs to 'Cancelled' state
                orders.button_cancel()

                # Return an action to display the new RFQ in form view
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'purchase.order',
                    'view_mode': 'form',
                    'res_id': new_order.id,
                    'target': 'current',
                }

        # If no orders were combined, return to the list view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def action_bid_received(self):
        self.write({'state': 'bid_received'})

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'bid_received']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def update_discount(self):
        for order in self:
            products_with_discount = self.env['product.product'].search([('is_default', '=', True)])
            if not any(order.order_line.mapped('product_id').mapped('is_default')):
                for product in products_with_discount:
                    values = {
                        'product_id': product.id,
                        'name': product.name,
                        'product_qty': 1,
                        'price_unit': product.lst_price,
                        'discount': False,
                        'taxes_id': False,
                    }
                    order.write({'order_line': [(0, 0, values)]})
            total_subtotal = sum(line.price_subtotal for line in order.order_line if not line.product_id.is_default)

            for line in order.order_line:
                if line.product_id.is_default:
                    discount_amount = total_subtotal * (order.main_discount / 100)
                    if total_subtotal > 0:
                        line.price_unit = -(discount_amount)
                    else:
                        line.price_unit = 0
                        line.price_subtotal = 0
            order.order_line._compute_amount()

    @api.depends('is_purchase_approval', 'order_line', 'order_line.product_qty', 'order_line.price_unit')
    def _compute_purchase_approval(self):
        for rec in self:
            rec.is_purchase_approval = False
            if rec.order_line:
                po_quantities = sum(rec.order_line.mapped('product_qty'))
                po_price_units = sum(rec.order_line.mapped('price_unit'))
                if po_quantities == 0 and po_price_units == 0.0:
                    rec.write({'is_purchase_approval': True})
                else:
                    rec.write({'is_purchase_approval': False})

    def action_confirm_rfq(self):
        if not self.order_line:
            raise ValidationError('Please enter the product lines before confirming the RFQ.')
        self.write({'state': 'sent'})

    def create_sale_quotation(self):
        so_creation = {
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.company_id.currency_id.id,
            'origin': self.name,
            'order_id': self.id,
            'po_type': self.po_type,
        }
        sale = self.env['sale.order'].create(so_creation)
        for line in self.purchase_order_line:
            sale_lines = {
                'name': line.product_id.description or line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'price_unit': line.price_unit,
                'order_id': sale.id,
            }
            self.env['sale.order.line'].create(sale_lines)
            line.sale_order_id = sale.id

    def action_send_for_approval(self):
        self.write({'state': 'sent'})

    @api.model
    def create(self, vals):
        self._validate_zero_rate_lines(vals.get('order_line', []))
        return super(PurchaseOrder, self).create(vals)

    def write(self, vals):
        if 'order_line' in vals:
            self._validate_zero_rate_lines(vals.get('order_line', []))
        return super(PurchaseOrder, self).write(vals)

    def _validate_zero_rate_lines(self, order_lines):
        """
        Validates that no order lines have a zero price unit or zero subtotal.
        :param order_lines: List of order line data
        """
        for line in order_lines:
            if line[0] in [0, 1, 4] and len(line) > 2:
                # Ensure line[2] is a dictionary before accessing 'price_unit'
                if isinstance(line[2], dict) and line[2].get('price_unit', None) == 0:
                    raise ValidationError(
                        _("Zero-rate purchase orders are not allowed. Please review the order lines."))


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    sale_line_id = fields.Many2one('sale.order.line', 'Sale')
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
    model = fields.Char(string="Model",
                        related='product_id.model',
                        store=True,
                        readonly=True)
    make = fields.Char(string="Make",
                       related='product_id.make',
                       store=True,
                       readonly=False)
    parameter_1 = fields.Text(
        string='Parameter 1',
        related='product_id.parameter_1',
        readonly=False,
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
                self.product_uom = product.uom_id.id
                self.price_unit = product.standard_price  # Default to the cost price
            else:
                self.product_id = False
                self.product_uom = False
                self.price_unit = 0.0

    def cancel_quantity(self):
        for rec in self:
            rec.write({'product_qty': 0, 'price_unit': 0})

    @api.model
    def create(self, vals):
        if vals.get('price_unit', 0) == 0:
            raise ValidationError(_("Line items with a zero price unit are not allowed."))
        return super(PurchaseOrderLine, self).create(vals)


class Product(models.Model):
    _inherit = 'product.template'

    name = fields.Char('Name', index='trigram', required=False, translate=True)
    is_default = fields.Boolean('Discount', default=False, store=True)
    is_default_set = fields.Boolean(compute="_compute_default_uom", store=True)
    company_id = fields.Many2one('res.company', 'Company', compute='_compute_fieldvalue', readonly=False, store=True)
    detailed_type = fields.Selection(selection_add=[
        ('product', 'Storable Product')
    ], default='product', tracking=True, ondelete={'product': 'set consu'})
    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities')], default='delivery', string='Invoicing Policy',
        compute='_compute_invoice_policy', store=True, readonly=False, precompute=True,
        help='Ordered Quantity: Invoice quantities ordered by the customer.\n'
             'Delivered Quantity: Invoice quantities delivered to the customer.')



    @api.constrains('type', 'detailed_type')
    def _constrains_detailed_type(self):
        type_mapping = self._detailed_type_mapping()


    @api.model
    def create(self, vals):
        if vals.get('is_default') and vals.get('name') != 'Discount':
            raise UserError('If "Discount" is set to True, the "name" must be "Discount".')
        return super(Product, self).create(vals)

    def write(self, vals):
        if vals.get('is_default', self.is_default) and self.name != 'Discount':
            raise UserError('The "Discount" can only be selected if the name of the product is also "Discount". '
                            'Please correct the product name.')
        return super(Product, self).write(vals)

    @api.depends('name')
    def _compute_fieldvalue(self):
        for record in self:
            record.company_id = self.env.user.company_id if self.env.user.company_id else ''

    @api.depends('is_default')
    def _compute_default_uom(self):
        for rec in self:
            rec.is_default_set = rec.is_default


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_default = fields.Boolean(related="product_tmpl_id.is_default", string='Discount', readonly=False)
    is_default_set = fields.Boolean(related="product_tmpl_id.is_default_set")
    stock_keeping_unit = fields.Char(related="product_tmpl_id.stock_keeping_unit", string='Product ID (SKU)',
                                     readonly=False)
    model = fields.Char(related="product_tmpl_id.model", readonly=False, string='Model')
    make = fields.Char(related="product_tmpl_id.make", readonly=False, string='Make')
    origin_country_id = fields.Many2one(related="product_tmpl_id.origin_country_id", readonly=False,
                                        string="Country of Origin")


    @api.model
    def create(self, vals):
        if vals.get('name'):
            existing_product = self.search([('name', '=', vals['name'])])
            if existing_product:
                raise UserError('Same product "%s" already exists!' % vals['name'])
        return super(ProductProduct, self).create(vals)
