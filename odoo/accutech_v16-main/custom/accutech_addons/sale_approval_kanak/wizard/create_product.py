from odoo import fields, models, api, _



class CreateOTI(models.TransientModel):
    _name = 'create.oti'
    _description = 'Create OTI'

    order_id = fields.Many2one('sale.order', 'Sale Order')
    one_time_items = fields.One2many('one.time.items', 'sale_oti_id', string="OTI")
    tax_id = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        default=lambda self: self._get_default_tax()
    )

    def _get_default_tax(self):
        # Get the current active company
        active_company = self.env.company
        print("\n--- Active Company: ", active_company.name, "--\n")

        # Search for a tax in the current active company
        tax = self.env['account.tax'].search([
            ('company_id', '=', active_company.id),
            ('type_tax_use', '=', 'sale')  # Optional: Restrict to sales taxes
        ], limit=1)  # Get the first matching tax
        print("\n---", tax, "--tax--\n")

        if tax:
            # Return the tax ID in the correct format for Many2many field
            return [(6, 0, [tax.id])]

        # If no tax is found, return an empty list or handle the fallback logic
        return []

    @api.model
    def default_get(self, fields):
        res = super(CreateOTI, self).default_get(fields)
        order_id = self.env.context.get('default_order_id')
        sale_order = self.env['sale.order'].browse(order_id)
        lines = []
        for line in sale_order.order_line:
            if line.is_oti:
                line_dict = {}
                line_dict['int_id'] = int(line.id)
                line_dict['product_name'] = line.product_name
                line_dict['sale_line_id'] = line.id
                line_dict['price_unit'] = line.price_unit
                line_dict['product_uom'] = line.product_uom.id
                line_dict['description_short'] = line.description_short
                lines.append((0, 0, line_dict))
        res['one_time_items'] = lines
        return res

    def action_create(self):
        active_id = self.order_id
        if active_id:
            if self.env.context.get('sale_order'):
                sale_order = self.env['sale.order'].browse(active_id.id)
                lines = self.one_time_items
                if lines:
                    for line in lines:
                        # Ensure UoM defaults to 'Units' if not explicitly set
                        uom_units = self.env.ref('uom.product_uom_unit')  # Reference to 'Units' UoM

                        # Check if the product already exists
                        existing_product = self.env['product.product'].search([('name', '=', line.product_name)],
                                                                              limit=1)

                        if not existing_product:
                            # Create Product Template if product doesn't exist
                            product_creation = {
                                'name': line.product_name,
                                'categ_id': line.product_categ.id,
                                'uom_id': uom_units.id,  # Default UoM is 'Units'
                                'standard_price': line.price_unit,
                            }
                            template = self.env['product.template'].create(product_creation)
                            product = template.product_variant_ids[0]  # Get the first product from the template
                        else:
                            product = existing_product

                        # Create sale order line with the selected or newly created product
                        for sale in self.order_id.order_line:
                            if sale.id == line.sale_line_id.id:
                                sale.unlink()  # Remove the old sale order line
                                val_line = {
                                    'name': line.product_name,
                                    'order_id': self.order_id.id,
                                    'product_template_id': product.product_tmpl_id.id,
                                    'description_short': line.description_short,
                                    'product_id': product.id,
                                    'id': line.sale_line_id.id,
                                    'product_uom_qty': 1,
                                    'price_unit': line.price_unit,
                                    'product_uom': uom_units.id,  # Set UoM to 'Units'
                                    'display_type': False
                                }
                                self.env['sale.order.line'].create(val_line)

                    # Update sale order with the new state
                    sale_order.write({
                        'can_validate_quote': False,
                        'show_quote_sent_stage': True,
                        'confirm_button': False
                    })
                    sale_order.action_confirm()  # Confirm the sale order


class OneTimeItems(models.TransientModel):
    _name = 'one.time.items'
    _description = 'One Time Items'

    sale_oti_id = fields.Many2one('create.oti', 'Create OTI')
    product_name = fields.Char('OTI Name', store=True)
    product_categ = fields.Many2one('product.category', 'OTI/Product Category')
    sale_line_id = fields.Many2one('sale.order.line', "Sale")
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float('OTI Price')
    int_id = fields.Integer('ID')
    description_short = fields.Text(
        'SHORT DESCRIPTION')
    tax_id = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        default=lambda self: self._get_default_tax()
    )

    def _get_default_tax(self):
        # Get the current active company
        active_company = self.env.company
        print("\n--- Active Company: ", active_company.name, "--\n")

        # Search for a tax in the current active company
        tax = self.env['account.tax'].search([
            ('company_id', '=', active_company.id),
            ('type_tax_use', '=', 'sale')  # Optional: Restrict to sales taxes
        ], limit=1)  # Get the first matching tax
        print("\n---", tax, "--tax--\n")

        if tax:
            # Return the tax ID in the correct format for Many2many field
            return [(6, 0, [tax.id])]

        # If no tax is found, return an empty list or handle the fallback logic
        return []


