# -*- coding: utf-8 -*-

from odoo import fields, models
import time
from datetime import datetime
from dateutil import relativedelta

import xlsxwriter
from io import StringIO
import base64


class FunnelReport(models.TransientModel):
    _name = "funnel.report"
    _description = 'Funnel'

    date_from = fields.Date(string="Date From", required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string="Date To", required=True, default=lambda *a: str(
        datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    filedata = fields.Binary('Download file', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)

    def excel_report(self):
        output = StringIO()
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Funnel.xlsx')
        worksheet = workbook.add_worksheet()

        merge_format1 = workbook.add_format(
            {'bold': 1, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Liberation Serif', })
        merge_format2 = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'underline': 'underline',
             'font_name': 'Liberation Serif', })
        merge_format3 = workbook.add_format({'border': 1, 'align': 'left', 'font_name': 'Liberation Serif'})
        merge_format4 = workbook.add_format(
            {'border': 1, 'align': 'left', 'font_name': 'Liberation Serif', 'num_format': 'd-m-yyyy'})
        merge_format5 = workbook.add_format(
            {'border': 1, 'align': 'left', 'font_name': 'Liberation Serif', 'num_format': '#,##0,0.00'})
        merge_format6 = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Liberation Serif'})
        merge_format7 = workbook.add_format(
            {'border': 1, 'align': 'center', 'font_name': 'Liberation Serif', 'fg_color': 'gray'})

        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:G', 20)
        worksheet.set_column('G:G', 20)
        worksheet.merge_range('A1:E1', self.env.user.company_id.name, merge_format1)
        worksheet.merge_range('A2:E2', 'FUNNEL REGISTER', merge_format1)
        worksheet.merge_range('A3:E3',
                              str(self.date_from).split('-')[2] + '-' + str(self.date_from).split('-')[1] + '-' +
                              str(self.date_from).split('-')[0] + ' to ' + str(self.date_to).split('-')[2] + '-' +
                              str(self.date_to).split('-')[1] + '-' + str(self.date_to).split('-')[0], merge_format1)
        worksheet.write('A5', "S.No", merge_format7)
        worksheet.write('B5', "AM", merge_format7)
        worksheet.write('C5', "Customer", merge_format7)
        worksheet.write('D5', "Opportunity", merge_format7)
        worksheet.write('E5', "Responsible", merge_format7)
        worksheet.write('F5', "Value TL", merge_format7)
        worksheet.write('G5', "Value BL", merge_format7)
        worksheet.write('H5', "B(Budget)", merge_format7)
        worksheet.write('I5', "A(Authority)", merge_format7)
        worksheet.write('J5', "N(Need)", merge_format7)
        worksheet.write('K5', "T(Time)", merge_format7)
        worksheet.write('L5', "%", merge_format7)
        worksheet.write('M5', "Month", merge_format7)
        worksheet.write('N5', "Quarter", merge_format7)
        worksheet.freeze_panes(5, 0)
        self.env.cr.execute("""
                    SELECT cl.date_deadline AS am, rp.name AS customer, cl.name AS opport, expected_revenue As valur_tl, value_bl, pru.name AS user,
                    CASE WHEN budget = 't' THEN 'Yes' ELSE 'No' END As budget,
                    CASE WHEN authority = 't' THEN 'Yes' ELSE 'No' END As authority,
                    CASE WHEN need = 't' THEN 'Yes' ELSE 'No' END As need,
                    CASE WHEN time_lead = 't' THEN 'Yes' ELSE 'No' END As time_lead,
                    TO_CHAR(cl.date_deadline, 'Month') AS month,
                    CASE WHEN TO_CHAR(cl.date_deadline, 'mm') in ('04','05','06') THEN 'Q1'
                    WHEN TO_CHAR(cl.date_deadline, 'mm') in ('07','08','09') THEN 'Q2'
                    WHEN TO_CHAR(cl.date_deadline, 'mm') in ('10','11','12') THEN 'Q3'
                    WHEN TO_CHAR(cl.date_deadline, 'mm') in ('01','02','03') THEN 'Q4'
                    ELSE ' ' END AS quarter
                    FROM crm_lead cl
                    JOIN res_partner rp ON (rp.id = cl.partner_id)
                    JOIN res_users ru ON (ru.id = cl.user_id)
                    JOIN res_partner pru ON (pru.id = ru.partner_id)
                    WHERE cl.type = 'opportunity' AND cl.date_deadline >= '%s' AND cl.date_deadline <= '%s'
                     """ % (self.date_from, self.date_to))
        line_data = [i for i in self.env.cr.dictfetchall()]
        n = 6
        c = 1
        for line in line_data:
            worksheet.write('A' + str(n), str(c), merge_format6)
            worksheet.write('B' + str(n), line['am'], merge_format4)
            worksheet.write('C' + str(n), line['customer'], merge_format3)
            worksheet.write('D' + str(n), line['opport'], merge_format3)
            worksheet.write('E' + str(n), line['user'], merge_format3)
            worksheet.write('F' + str(n), line['valur_tl'], merge_format3)
            worksheet.write('G' + str(n), line['value_bl'], merge_format3)
            worksheet.write('H' + str(n), line['budget'], merge_format5)
            worksheet.write('I' + str(n), line['authority'], merge_format3)
            worksheet.write('J' + str(n), line['need'], merge_format3)
            worksheet.write('K' + str(n), line['time_lead'], merge_format3)
            worksheet.write('L' + str(n), '', merge_format3)
            worksheet.write('M' + str(n), line['month'], merge_format3)
            worksheet.write('N' + str(n), line['quarter'], merge_format3)
            n = n + 1
            c = c + 1

        workbook.close()
        fo = open(url + 'Funnel.xlsx', "rb+")
        data = fo.read()
        out = base64.encodebytes(data)
        self.write({'filedata': out, 'filename': 'Funnel.xlsx'})
        return {'name': 'DSR Report',
                'res_model': 'funnel.report',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'nodestroy': True,
                'res_id': self.id, }
