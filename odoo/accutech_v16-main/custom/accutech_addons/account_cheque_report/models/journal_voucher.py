# -*- coding: utf-8 -*-

#-*- coding:utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VoucherReport(models.AbstractModel):
    _name = 'journal.report'
    _description = 'Journal Voucher'

    @api.model
    def _get_report_values(self, docids, data=None):
        inv = self.env['account.move'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': inv,
            'data': data,
        }

