# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        tos = []
        tor = []
        for line in self.order_line:
            if line.product_id.product_takeover_type:
                if line.commencement_date and line.product_id.product_takeover_type == 'tos':
                    tos.append(line)
                if line.commencement_date and line.product_id.product_takeover_type == 'tor':
                    tor.append(line)
        if tos:
            dic_so = []
            for t in tos:
                dic_so.append({'product_name': t.product_id.name, 'commencement_date': t.commencement_date,
                               'service_date': t.service_date})
            ctx = {'records': dic_so, 'email_to': self.env.user.company_id.order_confirmation_tos_to,
                   'email_cc': self.env.user.company_id.order_confirmation_tos_cc}
            template = self.env.ref('takeover_alert.email_template_sale_order_confirmation_commencement_activity').id
            self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
        if tor:
            dic_so = []
            for t in tor:
                dic_so.append({'product_name': t.product_id.name, 'commencement_date': t.commencement_date,
                               'service_date': t.service_date})
            ctx = {'records': dic_so, 'email_to': self.env.user.company_id.order_confirmation_tor_to,
                   'email_cc': self.env.user.company_id.order_confirmation_tos_cc, 'name': self.name}
            template = self.env.ref('takeover_alert.email_template_sale_order_confirmation_commencement_activity').id
            self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
        return res


    @api.model
    def _check_commencement_activity_orders(self):
        prior_date = datetime.now().date() + timedelta(days=7)
        sale_order_lines = self.env['sale.order.line'].search([('state', '=', 'sale')]).filtered(lambda x:x.commencement_date == prior_date)
        print("---", sale_order_lines, "--sale_order_lines--")
        sale_orders = self.env['sale.order'].search([('state', '=', 'sale'), ('id', 'in', sale_order_lines.mapped('order_id.id'))])
        print("---", sale_orders, "--sale_orders--")
        for order in sale_orders:
            sale_order_lines_filtered = sale_order_lines.filtered(lambda x: x.order_id == order)
            print("---", sale_order_lines_filtered, "--sale_order_lines_filtered--")
            tos = []
            tor = []
            for line in sale_order_lines_filtered:
                if line.product_id.product_takeover_type:
                    if line.commencement_date and line.product_id.product_takeover_type == 'tos':
                        tos.append(line)
                    if line.commencement_date and line.product_id.product_takeover_type == 'tor':
                        tor.append(line)
            if tos:
                dic_so = []
                for t in tos:
                    dic_so.append({'product_name': t.product_id.name, 'commencement_date': t.commencement_date,
                                   'service_date': t.service_date})
                ctx = {'records': dic_so, 'email_to': self.env.user.company_id.before_days_tos_to,
                       'email_cc': self.env.user.company_id.before_days_tos_cc, 'name': order.name}
                template = self.env.ref(
                    'takeover_alert.email_template_sale_order_prior_commencement_activity').id
                self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
            if tor:
                dic_so = []
                for t in tor:
                    dic_so.append({'product_name': t.product_id.name, 'commencement_date': t.commencement_date,
                                   'service_date': t.service_date})
                ctx = {'records': dic_so, 'email_to': self.env.user.company_id.before_days_tor_to,
                       'email_cc': self.env.user.company_id.before_days_tor_cc, 'name': order.name}
                template = self.env.ref(
                    'takeover_alert.email_template_sale_order_prior_commencement_activity').id
                self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_takeover_type = fields.Selection([('tos', 'TOS'), ('tor', 'TOR')], string="Takeover Type",
                                             related='product_id.product_takeover_type')
    commencement_date = fields.Date(string="Commencement Date")
    service_date = fields.Date(string="Date of Start Service")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    order_confirmation_tos_to = fields.Char(string="Order Confirmation Mail",
                                        related='company_id.order_confirmation_tos_to', store=True, readonly=False)
    order_confirmation_tos_cc = fields.Char(string="Order Confirmation Mail(Cc)",
                                        related='company_id.order_confirmation_tos_cc', store=True, readonly=False)
    before_days_tos_to = fields.Char(string="Prior Mail(7 Days)",
                                        related='company_id.before_days_tos_to', store=True, readonly=False)
    before_days_tos_cc = fields.Char(string="Prior Mail(Cc)",
                                        related='company_id.before_days_tos_cc', store=True, readonly=False)
    order_confirmation_tor_to = fields.Char(string="Order Confirmation Mail",
                                        related='company_id.order_confirmation_tor_to', store=True, readonly=False)
    order_confirmation_tor_cc = fields.Char(string="Order Confirmation Mail(Cc)",
                                        related='company_id.order_confirmation_tor_cc', store=True, readonly=False)
    before_days_tor_to = fields.Char(string="Prior Mail(7 Days)",
                                 related='company_id.before_days_tor_to', store=True, readonly=False)
    before_days_tor_cc = fields.Char(string="Prior Mail(Cc)",
                                 related='company_id.before_days_tor_cc', store=True, readonly=False)



class ResCompany(models.Model):
    _inherit = 'res.company'

    order_confirmation_tos_to = fields.Char(string="Order Confirmation Mail(To)")
    order_confirmation_tos_cc = fields.Char(string="Order Confirmation Mail(Cc)")
    before_days_tos_to = fields.Char(string="Prior Mail")
    before_days_tos_cc = fields.Char(string="Prior Mail(Cc)")
    order_confirmation_tor_to = fields.Char(string="Order Confirmation Mail(To)")
    order_confirmation_tor_cc = fields.Char(string="Order Confirmation Mail(Cc)")
    before_days_tor_to = fields.Char(string="Prior Mail")
    before_days_tor_cc = fields.Char(string="Prior Mail(Cc)")