# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models
import logging
import pytz
from datetime import datetime, date
import fiscalyear
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import base64
import time
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def to_naive_user_tz(datetime, record):
    tz_name = record._context.get('tz') or record.env.user.tz
    tz = tz_name and pytz.timezone(tz_name) or pytz.UTC
    return pytz.UTC.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(tz).replace(tzinfo=None)


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"

    partner_ids = fields.Many2many('res.partner', 'partner_ledger_partner_rel', 'id', 'partner_id', string='Partners')
    currency = fields.Many2one('res.currency', string="Currency")

    def cron_ledger_mail_sent(self):
        journals = self.env['account.journal'].search([])
        mail_obj = self.env['mail.mail']
        company_ids = self.env['res.company'].search([])
        if company_ids:
            fiscalyear.setup_fiscal_calendar(start_month=4)
            from_date = fiscalyear.FiscalYear.current().start.date()
            if (date.today() - from_date).days < 10:
                from_date = from_date.replace(year=from_date.year - 1)
            to_date = (date.today() - relativedelta(months=1)).replace(
                day=monthrange(date.today().year, date.today().month - 1)[1])
            # opening Wizard with values
            data = {'ids': [],
                    'model': 'ir.ui.menu',
                    'form': {'date_from': str(from_date),
                             'date_to': str(to_date),
                             'journal_ids': journals.ids,
                             'target_move': 'posted',
                             'reconciled': True,
                             'currency': 20,
                             'used_context': {
                                 'journal_ids': journals.ids,
                                 'state': 'posted',
                                 'date_from': str(from_date),
                                 'date_to': str(to_date),
                                 'strict_range': True,
                                 'lang': 'en_US'
                             },
                             'result_selection': 'customer'}
                    }

            # all valid customers
            partner_ids = self.env['res.partner'].search(
                [('email', '!=', False)])

            # looping customer one by one
            for partner_id in partner_ids:
                amount_due = 0.00
                for am in partner_id.invoice_list:
                    if am.company_id == self.env.company:
                        amount = am.amount_residual
                        amount_due += amount
                if amount_due > 0:
                    # update customer in wizard
                    data['form'].update({'partner_ids': partner_id.ids})

                    # rendering pdf report
                    pdf = \
                        self.env.ref('base_accounting_kit.action_report_partnerledger')._render_qweb_pdf(self.id,
                                                                                                         data=data)[0]
                    # attach  pdf report create
                    att_val = {
                        'name': 'partner_ledger_report',
                        'datas': base64.encodestring(pdf),
                    }
                    attachment = self.env['ir.attachment'].create(att_val)
                    mail_values = {
                        'email_to': partner_id.email,
                        'subject': 'Futurenet - Partner Ledger Report From %s To %s' % (from_date, to_date),
                        'body_html': "Dear Customer,<br/><p></p> Please find the attached document.<br/><p></p>Thanks & Regards,<br/>Futurenet Private Limited,<br/>Administrator.",
                        # 'notification': True,
                        'attachment_ids': [(6, 0, [attachment.id])],
                        'auto_delete': False,
                    }
                    mail_obj += self.env['mail.mail'].create(mail_values)
                if mail_obj:
                    try:
                        mail_obj._send()
                        _logger.info('Partner Ledger: Mail successfully sent for all the customers')
                    except Exception as e:
                        _logger.exception('Error while sending mail: %s' % e)

    def _print_report(self, data):
        data = self.pre_print_report(data)
        if not self.date_from:
            data['form'].update({'date_from': '2000-01-01'})
        if not self.date_to:
            data['form'].update({'date_to': str(date.today())})
        data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency,
                             'partner_ids': self.partner_ids.ids, 'currency': self.currency.id})
        return self.env.ref('base_accounting_kit.action_report_partnerledger').report_action(self, data=data)
