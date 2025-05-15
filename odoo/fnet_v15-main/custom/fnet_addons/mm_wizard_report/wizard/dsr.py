# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import time
from datetime import datetime, date, timedelta
from dateutil import relativedelta
import xlsxwriter
from io import StringIO
import base64


class DsrReport(models.TransientModel):
    _name = "dsr.report"
    _description = 'Attendnace Register'

    date_from = fields.Date(string="Date From", required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string="Date To", required=True, default=lambda *a: str(
        datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    filedata = fields.Binary('Download file', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)

    def excel_report(self):
        output = StringIO()
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'DSR.xlsx')
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
        worksheet.merge_range('A2:E2', 'DSR REGISTER', merge_format1)
        worksheet.merge_range('A3:E3',
                              str(self.date_from).split('-')[2] + '-' + str(self.date_from).split('-')[1] + '-' +
                              str(self.date_from).split('-')[0] + ' to ' + str(self.date_to).split('-')[2] + '-' +
                              str(self.date_to).split('-')[1] + '-' + str(self.date_to).split('-')[0], merge_format1)
        worksheet.write('A5', "S.No", merge_format7)
        worksheet.write('B5', "Date", merge_format7)
        worksheet.write('C5', "Type of Activity", merge_format7)
        worksheet.write('D5', "Customer Name", merge_format7)
        worksheet.write('E5', "Phone Number", merge_format7)
        worksheet.write('F5', "Responsible", merge_format7)
        worksheet.write('G5', "Brief Discussion of Activity", merge_format7)
        worksheet.write('H5', "Duration", merge_format7)
        worksheet.write('I5', "Outcome", merge_format7)
        worksheet.write('J5', "Product", merge_format7)
        worksheet.write('K5', "Value", merge_format7)
        worksheet.freeze_panes(5, 0)
        self.env.cr.execute("""
        SELECT vp.name, call_date,  vp.product, vp.value, vp.outcome, pru.name AS sale_person, vp.phonecall_type,  rp.name AS customer, vp.note AS call_summary, vp.state, duration, vp.phone
        FROM voip_phonecall vp
        LEFT JOIN res_partner rp ON (rp.id = vp.partner_id)
        JOIN res_users ru ON (ru.id = vp.user_id)
        JOIN res_partner pru ON (pru.id = ru.partner_id)
        WHERE call_date >= '%s' AND call_date <= '%s'
         """ % (self.date_from, self.date_to))
        line_data = [i for i in self.env.cr.dictfetchall()]
        n = 6
        c = 1
        for line in line_data:
            worksheet.write('A' + str(n), str(c), merge_format6)
            worksheet.write('B' + str(n), line['call_date'], merge_format4)
            worksheet.write('C' + str(n), line['phonecall_type'], merge_format3)
            worksheet.write('D' + str(n), line['customer'], merge_format3)
            worksheet.write('E' + str(n), line['phone'], merge_format3)
            worksheet.write('F' + str(n), line['sale_person'], merge_format3)
            worksheet.write('G' + str(n), line['call_summary'], merge_format3)
            worksheet.write('H' + str(n), line['duration'], merge_format5)
            worksheet.write('I' + str(n), line['outcome'], merge_format3)
            worksheet.write('J' + str(n), line['product'], merge_format3)
            worksheet.write('K' + str(n), line['value'], merge_format3)
            n = n + 1
            c = c + 1

        workbook.close()
        fo = open(url + 'DSR.xlsx', "rb+")
        data = fo.read()
        out = base64.encodebytes(data)
        self.write({'filedata': out, 'filename': 'DSR.xlsx'})
        return {'name': 'DSR Report',
                'res_model': 'dsr.report',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'nodestroy': True,
                'res_id': self.id}
