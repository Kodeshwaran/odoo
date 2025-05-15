# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def check_delivery_expiry(self):
        current_date = datetime.now().date()
        saleperson_due = current_date + timedelta(days=7)
        saleshead_due = current_date + timedelta(days=3)
        md_due = current_date - timedelta(days=7)

        salesperson_order_lines = self.env['sale.order.line'].search([('state', 'in', ['sale', 'done']),
                                                                      ('ordered_delivery_date', '>=', current_date),
                                                                      ('ordered_delivery_date', '<', saleperson_due)]).filtered(lambda x: x.qty_delivered < x.product_uom_qty)
        saleshead_order_lines = self.env['sale.order.line'].search([('state', 'in', ['sale', 'done']),
                                                                      ('ordered_delivery_date', '>=', current_date),
                                                                      ('ordered_delivery_date', '<', saleshead_due)]).filtered(lambda x: x.qty_delivered < x.product_uom_qty)
        md_order_lines = self.env['sale.order.line'].search([('state', 'in', ['sale', 'done']),
                                                                    ('ordered_delivery_date', '<', current_date),
                                                                    ('ordered_delivery_date', '>=', md_due)]).filtered(lambda x: x.qty_delivered < x.product_uom_qty)
        print("---", salesperson_order_lines, "--salesperson_order_lines--")
        print("---", saleshead_order_lines, "--saleshead_order_lines--")
        print("---", md_order_lines, "--md_order_lines--")
        salespersons = salesperson_order_lines.mapped('order_id.user_id')
        print("---", salespersons, "--salespersons--")
        for user in salespersons:
            sales_orders_lines = salesperson_order_lines.filtered(lambda x: x.order_id.user_id == user)
            if sales_orders_lines:
                dic_so = []
                for line in sales_orders_lines:
                    dic_so.append({'url': '/mail/view?model=%s&res_id=%s' % ('sale.order', line.order_id.id), 'so': line.order_id.name,
                                   'product': line.product_id.name, 'quantity': int(line.product_uom_qty - line.qty_delivered)})
                ctx = {'records': dic_so, 'email': user.login, 'name': user.name}
                print("---", ctx['records'], ctx['email'], ctx['name'], "--ctx['records']--")
                template = self.env.ref('sale_delivery_alert.email_template_sale_order_delivery_alert_salesperson').id
                self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
        so_head = []
        if saleshead_order_lines:
            for line in saleshead_order_lines:
                so_head.append({'url': '/mail/view?model=%s&res_id=%s' % ('sale.order', line.order_id.id),
                               'so': line.order_id.name,
                               'product': line.product_id.name,
                               'quantity': int(line.product_uom_qty - line.qty_delivered)})
        ctx = {'records': so_head,'email': self.env.user.company_id.sales_head.login, 'name': self.env.user.company_id.sales_head.name}
        print("---", ctx['records'], "--ctx['records']--")
        template = self.env.ref('sale_delivery_alert.email_template_sale_order_delivery_alert_saleshead_md').id
        self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
        so_md = []
        if md_order_lines:
            for line in md_order_lines:
                so_md.append({'url': '/mail/view?model=%s&res_id=%s' % ('sale.order', line.order_id.id),
                                'so': line.order_id.name,
                                'product': line.product_id.name,
                                'quantity': int(line.product_uom_qty - line.qty_delivered)})
        ctx = {'records': so_md, 'email': self.env.user.company_id.md_person.login,
               'name': self.env.user.company_id.md_person.name}
        print("---", ctx['records'], "--ctx['records']--")
        template = self.env.ref('sale_delivery_alert.email_template_sale_order_delivery_alert_saleshead_md').id
        self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
