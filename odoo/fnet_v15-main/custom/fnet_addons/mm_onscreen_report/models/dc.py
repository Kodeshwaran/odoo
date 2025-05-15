# -*- coding: utf-8 -*-

#-*- coding:utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class DCReport(models.AbstractModel):
    _name = 'report.mm_onscreen_report.dc_template_report'
    _description = 'DC'

    def _get_serial(self, obj):
        self.env.cr.execute('''
        SELECT string_agg(spl.name, ', ') AS lot
        FROM stock_move sm
        JOIN stock_move_line sml ON (sml.move_id = sm.id)
        JOIN stock_production_lot spl ON (spl.id = sml.lot_id)
        WHERE sm.id = %s GROUP BY sml.move_id ''', (obj.id,))
        res = self.env.cr.fetchall()
        if res:
            return res[0][0]

    @api.model
    def _get_report_values(self, docids, data=None):
        inv = self.env['stock.picking'].browse(docids)
        print (inv)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': inv,
            'data': data,
            'get_serial': self._get_serial,
        }

