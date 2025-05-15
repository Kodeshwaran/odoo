# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SubscriptionProduct(models.Model):
    _inherit = 'product.product'

    subscription_product = fields.Boolean(string="Subscription", related='recurring_invoice')


class AccountMove(models.Model):
    _inherit = 'account.move'

    # def _subscription_count(self):
    #     for rec in self:
    #         count = self.env['sale.subscription'].search_count([('invoice_ids', '=', rec.id)])
    #         rec.subscription_count = count

    # def open_subscription(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Sale Subscription',
    #         'view_mode': 'tree,form',
    #         'res_model': 'sale.subscription',
    #         'domain': [('invoice_ids', '=', self.id)],
    #     }

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    # subscription_product = fields.Boolean(string="Subscription", default=False)
    # subscription_template = fields.Many2one('sale.subscription.template', string="Subscription Template")
    # subscription_count = fields.Integer("Subscription Count", compute='_subscription_count')
    # renewal_days_type = fields.Many2one('renewal.days', string="Renewal Type")
    #
    # @api.onchange('invoice_line_ids')
    # def _onchange_subscription_id(self):
    #     subscription_product = []
    #     for rec in self:
    #         for line in rec.invoice_line_ids:
    #             if line.subscription_product:
    #                 rec.subscription_template = line.product_id.subscription_template_id
    #                 subscription_product.append(line.product_id.id)
    #                 print("---", subscription_product, "--subscription_product--")
    #             else:
    #                 continue
    #         if subscription_product:
    #             rec.subscription_product = True
    #         else:
    #             rec.subscription_product = False

    def action_create_subscription(self):
        subscription_obj = self.env['sale.subscription']

        subscription = subscription_obj.sudo().create({
            'partner_id': self.partner_id.id or False,
            'date_start': self.invoice_date or False,
            'invoice_ids': self.ids,
            'template_id': self.subscription_template.id,
            'renewal_days_type': self.renewal_days_type.id,
            'sale_type_id':self.sale_type_id.id,
            'sales_sub_types': self.sales_sub_types.id
        })
        subscription.start_subscription()
        new_date = subscription._get_recurring_next_date(subscription.recurring_rule_type,
                                                         subscription.recurring_interval, subscription.date_start,
                                                         subscription.recurring_invoice_day)
        subscription.update({'date': new_date, 'recurring_next_date': new_date})
        for line in self.invoice_line_ids.filtered(lambda x: x.subscription_product == True):
            values = {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'uom_id': line.product_uom_id.id,
                'analytic_account_id':subscription.id,
            }
            lines = subscription.env['sale.subscription.line']
            lines.create(values)
            line.subscription_id = subscription.id

        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.subscription",
            "views": [[False, "form"]],
            "res_id": subscription.id,
        }


