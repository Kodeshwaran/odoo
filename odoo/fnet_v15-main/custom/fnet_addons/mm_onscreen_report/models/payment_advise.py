# -*- coding: utf-8 -*-

#-*- coding:utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError




class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    def get_client_ref(self, object_inv):
        self.env.cr.execute('''
            SELECT STRING_AGG(DISTINCT ai.ref, ',' ORDER BY ai.ref) As data
            FROM account_invoice_payment_rel air
            JOIN account_move ai ON (ai.id = air.invoice_id)
            WHERE air.payment_id = %s ''' % (object_inv.id,))
        res = self.env.cr.fetchall()
        if res:
            return res[0][0]
        else:
            return ''

    def get_account_no(self, object_inv):
        self.env.cr.execute('''
            SELECT STRING_AGG(DISTINCT acc_number, ',' ORDER BY acc_number) AS acc_no
            FROM res_partner_bank
            WHERE partner_id = %s ''' % (object_inv.partner_id.id,))
        res = self.env.cr.fetchall()
        if res:
            return res[0][0]
        else:
            return ''

    def get_account_ifsc(self, object_inv):
        self.env.cr.execute('''
            SELECT STRING_AGG(DISTINCT rb.bic, ',' ORDER BY rb.bic) AS acc_no
            FROM res_partner_bank rpb
            JOIN res_bank rb ON (rb.id = rpb.bank_id)
            WHERE partner_id = %s ''' % (object_inv.partner_id.id,))
        res = self.env.cr.fetchall()
        if res:
            return res[0][0]
        else:
            return ''

    def get_account_bank(self, object_inv):
        self.env.cr.execute('''
            SELECT STRING_AGG(DISTINCT rb.name, ',' ORDER BY rb.name) AS acc_no
            FROM res_partner_bank rpb
            JOIN res_bank rb ON (rb.id = rpb.bank_id)
            WHERE partner_id = %s ''' % (object_inv.partner_id.id,))
        res = self.env.cr.fetchall()
        if res:
            return res[0][0]
        else:
            return ''

    def get_inv_no(self, object_inv):
        self.env.cr.execute('''
            SELECT STRING_AGG(DISTINCT ai.name, ',' ORDER BY ai.name) As data
            FROM account_invoice_payment_rel air
            JOIN account_move ai ON (ai.id = air.invoice_id)
            WHERE air.payment_id = %s ''' % (object_inv.id,))
        res = self.env.cr.fetchall()
        if res:
            return res[0][0]
        else:
            return ''


class AdviseReport(models.AbstractModel):
    _name = 'report.mm_onscreen_report.payment_advise_template_report'
    _description = 'Journal Voucher'

    @api.model
    def _get_report_values(self, docids, data=None):
        inv = self.env['account.payment'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': inv,
            'data': data,
        }

