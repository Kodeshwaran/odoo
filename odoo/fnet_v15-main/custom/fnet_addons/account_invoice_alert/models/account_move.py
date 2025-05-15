# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    next_alert = fields.Date(string="Next Alert Date", store=True)
    # customer_name = fields.Char(related="partner_id.name", store=True, string='Customer ID')

    @api.model
    def _check_invoice_due(self):
        before_due_alert = datetime.now().date() + timedelta(days=3)
        after_due_alert = datetime.now().date() - timedelta(days=1)
        current_date = datetime.now().date()
        invoice_before = self.env['account.move'].search([('state', '=', 'posted'), ('invoice_date_due', '=', before_due_alert),
                                                          ('payment_state', '=', 'not_paid')])
        invoice_after = self.env['account.move'].search([('state', '=', 'posted'), ('invoice_date_due', '=', after_due_alert),
                                                         ('payment_state', '=', 'not_paid')])
        invoice_long_due = self.env['account.move'].search([('state', '=', 'posted'), ('next_alert', '=', current_date),
                                                            ('payment_state', '=', 'not_paid')])

        users = invoice_before.mapped('invoice_user_id')
        users += invoice_before.mapped('team_id.user_id')
        users_crossed = invoice_after.mapped('invoice_user_id')
        users_crossed += invoice_after.mapped('team_id.user_id')
        users_long_due = invoice_long_due.mapped('invoice_user_id')
        users_long_due += invoice_long_due.mapped('team_id.user_id')
        for user in users:
            invoices = invoice_before.filtered(lambda x: x.invoice_user_id == user or x.team_id.user_id == user)
            if invoices:
                dic_so = []
                for invoice in invoices:
                    dic_so.append({'url': '/mail/view?model=%s&res_id=%s' % ('account.move', invoice.id), 'invoice': invoice.name})
                ctx = {'records': dic_so,'email': user.login, 'name': user.name}
                print("---", ctx['records'],ctx['email'],ctx['name'], "--ctx['records']--")
                template = self.env.ref('account_invoice_alert.email_template_account_invoice_due_alert_before').id
                self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
        for user in users_crossed:
            invoices = invoice_after.filtered(lambda x: x.invoice_user_id == user or x.team_id.user_id == user)
            if invoices:
                dic_so = []
                for invoice in invoices:
                    dic_so.append({'url': '/mail/view?model=%s&res_id=%s' % ('account.move', invoice.id),
                                   'invoice': invoice.name})
                    invoice.next_alert = invoice.invoice_date_due + timedelta(days=invoice.company_id.long_due_alert)
                ctx = {'records': dic_so, 'email': user.login, 'name': user.name}
                print("---", ctx['records'], ctx['email'], ctx['name'], "--ctx['records']--")
                template = self.env.ref('account_invoice_alert.email_template_account_invoice_due_alert_after').id
                self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
        processed_invoice_list = []
        for user in users_long_due:
            invoices = invoice_long_due.filtered(lambda x: x.invoice_user_id == user or x.team_id.user_id == user)
            if invoices:
                dic_so = []
                for invoice in invoices:
                    if invoice.id not in processed_invoice_list:
                        invoice.next_alert += timedelta(days=5)
                        processed_invoice_list.append(invoice.id)
                    dic_so.append({'url': '/mail/view?model=%s&res_id=%s' % ('account.move', invoice.id),
                                   'invoice': invoice.name})
                ctx = {'records': dic_so, 'email': user.login, 'name': user.name}
                template = self.env.ref('account_invoice_alert.email_template_account_invoice_due_alert_after').id
                self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)
        if invoice_long_due:
            dic_so = []
            for invoice in invoice_long_due:
                dic_so.append({'url': '/mail/view?model=%s&res_id=%s' % ('account.move', invoice.id),
                               'invoice': invoice.name})
            ctx = {'records': dic_so, 'email': (self.env.user.company_id.accounts_mail,self.env.user.company_id.md_mail)}
            template = self.env.ref('account_invoice_alert.email_template_account_invoice_due_alert_long_due').id
            self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    accounts_mail = fields.Char(string="Accounts Mail",
                                           readonly=False, related='company_id.accounts_mail', store=True)
    md_mail = fields.Char(string="MD Mail",
                                          readonly=False, related='company_id.md_mail', store=True)
    long_due_alert = fields.Integer(string="Days for Final Alert",
                                    readonly=False,related='company_id.long_due_alert', store=True)

class ResCompany(models.Model):
    _inherit = 'res.company'

    accounts_mail = fields.Char(string="Accounts Mail")
    md_mail = fields.Char(string="MD Mail")
    long_due_alert = fields.Integer(string="Days for Final Alert")