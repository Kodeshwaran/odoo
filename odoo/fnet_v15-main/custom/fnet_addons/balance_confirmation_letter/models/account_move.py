from odoo import api, fields, models
import fiscalyear
import base64
from datetime import date, datetime, time,timedelta
from dateutil.relativedelta import relativedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    def check_due_bills(self):
        print("---", self.env.user.company_id.execution_date, "--self.env.user.company_id.execution_date--")
        print("---", fields.Date.today(), "--fields.Date.today()--")
        if self.env.user.company_id.execution_date and self.env.user.company_id.execution_date == fields.Date.today():
            print("---ddfgbbbbbbbbbbbbbbbb  ----")
            moves = self.env['account.move'].search(
                [('move_type', '=', 'in_invoice'), ('state', '=', 'posted'), ('payment_state', '!=', 'paid'),
                 ('invoice_date', '<=', self.env.user.company_id.execution_date)])
            print("---", moves, "--moves--")
            partners = moves.mapped('partner_id')
            for partner in partners:
                report = partner.print_balance_report(self.env.user.company_id.execution_date, name='')
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
            print("---", len(partners), "--partners--")
            self.env.user.company_id.execution_date = self.env.user.company_id.execution_date + \
                    timedelta(days=self.env.user.company_id.update_days) + relativedelta(months=self.env.user.company_id.update_month)