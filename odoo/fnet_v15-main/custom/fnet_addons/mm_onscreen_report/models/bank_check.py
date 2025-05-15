# -*- coding: utf-8 -*-

#-*- coding:utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BankCheckReport(models.AbstractModel):
    _name = 'report.mm_onscreen_report.bank_check_template_report'
    _description = 'Bank Cheque'

    @api.model
    def _get_report_values(self, docids, data=None):
        inv = self.env['account.move'].browse(docids)
        print (inv.to_self, "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': inv,
            'data': data,
        }

