# Copyright (c) 2023 Sayed Hassan (sh-odoo@hotmail.com)

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    fixed_discount = fields.Float(string="Fixed Disc.", digits="Product Price", default=0.000)

    discount = fields.Float(string='% Disc.', digits='Discount', default=0.000)

    @api.onchange("discount")
    def _onchange_discount(self):
        for line in self:
            if line.discount != 0:
                self.fixed_discount = 0.0
                fixed_discount = (line.price_unit * line.product_qty) * (line.discount / 100.0)
                line.update({"fixed_discount": fixed_discount})
            if line.discount == 0:
                fixed_discount = 0.000
                line.update({"fixed_discount": fixed_discount})
            line._compute_amount()

    @api.onchange("fixed_discount")
    def _onchange_fixed_discount(self):
        for line in self:
            if line.fixed_discount != 0:
                self.discount = 0.0
                discount = ((self.product_qty * self.price_unit) - ((self.product_qty * self.price_unit) - self.fixed_discount)) / (self.product_qty * self.price_unit) * 100 or 0.0
                line.update({"discount": discount})
            if line.fixed_discount == 0:
                discount = 0.0
                line.update({"discount": discount})
            line._compute_amount()

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.taxes_id,
            price_unit=self.price_unit,
            discount=self.discount,
            quantity=self.product_qty,
            price_subtotal=self.price_subtotal,
        )

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        res = {
            'display_type': self.display_type or 'product',
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'purchase_line_id': self.id,
        }
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        return res


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    main_discount = fields.Float(string='Overall Discount', digits='Discount', default=0.000)

    def update_discount(self):
        for order in self:
            products_with_discount = self.env['product.product'].search([('is_discount', '=', True)])
            if not any(order.order_line.mapped('product_id').mapped('is_discount')):
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
            total_subtotal = sum(line.price_subtotal for line in order.order_line if not line.product_id.is_discount)

            for line in order.order_line:
                if line.product_id.is_discount:
                    # line.discount = order.main_discount
                    discount_amount = total_subtotal * (order.main_discount / 100)
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!11",discount_amount)

                    if total_subtotal > 0:
                        line.price_unit = -(discount_amount)


                    else:
                        line.price_unit = 0
                        line.price_subtotal = 0
            order.order_line._compute_amount()


