# -*- coding: utf-8 -*-

#-*- coding:utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleReport(models.AbstractModel):
    _name = 'report.mm_onscreen_report.sale_quote_template_report'
    _description = 'GST Invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        inv = self.env['sale.order'].browse(docids)
        print (inv)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': inv,
            'data': data,
        }

