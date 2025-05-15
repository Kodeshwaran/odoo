# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import fiscalyear
import base64
from datetime import date, datetime, time


class Partner(models.Model):
    _inherit = 'res.partner'

    def print_balance_report(self, date, name):
        move_lines = self.env['account.move'].search(
            [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', '!=', 'paid'),
             ('invoice_date', '<=', date), ('partner_id', '=', self.id)])
        credit = sum(move_lines.mapped('amount_residual'))
        data = {'ids': [],
                'model': 'ir.ui.menu',
                'form': {},
                'date': date,
                'balance': credit,
                'name': name,
                }
        return self.env.ref('balance_confirmation_letter.balance_letter_report')._render_qweb_pdf([self.id], data=data)[0]


class BalanceConfirmationWizard(models.TransientModel):
    _name = "balance.confirmation.wizard"
    _description = "Balance Confirmation Report Wizard"

    name = fields.Char(string='Auditor Name')
    street = fields.Char("street")
    street2 = fields.Char("street2")
    zip = fields.Char("Zip")
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state', "State")
    country_id = fields.Many2one('res.country', "Country")
    partner_ids = fields.Many2many('res.partner', string="Customer/Vendor", required=True,)
    date = fields.Date(string='Date', required=True, default=lambda self: fields.Date.to_string(date.today()))
    # hr_expense_sheet_id = fields.Many2one('hr.expense.sheet')

    def balance_mail_sent(self):
        for partner in self.partner_ids:
            report = partner.print_balance_report(self.date, self.name)
            att_val = {
                'name': 'Partner Balance.pdf',
                'datas': base64.encodestring(report),
                'res_model': 'res.partner',
                'res_id': partner.id
            }
            attachment = self.env['ir.attachment'].create(att_val)
            mail_values = {
                'email_from': 'accounts@futurenet.in ',
                'reply_to': 'accounts@futurenet.in ',
                'email_to': partner.email,
                'subject': 'Balance Confirmation Report',
                'body_html': "Dear Customer,<br/><p></p> Please find the attached document."
                             "<br/><p></p>Thanks & Regards,<br/>Administrator.",
                'is_notification': True,
                'attachment_ids': [(6, 0, [attachment.id])],
                'auto_delete': False,
            }
            self.env['mail.mail'].create(mail_values)._send()



