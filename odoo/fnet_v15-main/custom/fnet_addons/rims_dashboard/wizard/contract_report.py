from odoo import models, fields, api, _
from geopy.distance import great_circle as GC
import requests
import json
from datetime import datetime, timedelta, time
import xlsxwriter
from io import StringIO
import base64

import pytz
from odoo.exceptions import UserError, ValidationError





class RimsContractReport(models.TransientModel):
    _name = 'rims.contract.report'
    _description = 'Rims Contract Report'

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")

    def action_contract_report(self):
        url = '/tmp/'
        report_name = "Contract Report"
        workbook = xlsxwriter.Workbook(url + report_name + '.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_name': 'Arial'})
        format = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'bg_color': '#486646', 'font_color': 'white', 'bottom': 2})
        sheet.set_row(0, 20)
        sheet.set_column('B:B', 35)
        sheet.set_column('C:G', 20)
        sheet.set_column('H:H', 25)
        sheet.set_column('I:K', 20)



        sheet.write('A1', 'S.No', format)
        sheet.write('B1', 'Customer Name', format)
        sheet.write('C1', 'Contract Type', format)
        sheet.write('D1', 'EPO count', format)
        sheet.write('E1', 'Contract Start Date', format)
        sheet.write('F1', 'Contract End Date', format)
        sheet.write('G1', 'Contract Value', format)
        sheet.write('H1', 'Billing Cycle', format)
        sheet.write('I1', 'Billing Amount', format)
        sheet.write('J1', 'Total Bills', format)
        sheet.write('K1', 'Pending Bills', format)

        n = 2
        s_no = 1
        contracts = self.env['rims.customer.master'].search([])

        for rec in contracts:
            invoice_count = rec.invoice_count.split('/')
            if len(invoice_count) == 2:
                total_bills = int(invoice_count[1])
                bills = int(invoice_count[0])
                pending_bills = total_bills - bills
            else:
                total_bills = pending_bills = 0

            contract_value = total_bills * rec.subscription_id.recurring_total_company

            sheet.write('A' + str(n), s_no, format1)
            sheet.write('B' + str(n), rec.name, format1)
            sheet.write('C' + str(n), rec.contract_type.name, format1)
            sheet.write('D' + str(n), rec.epo_count, format1)
            sheet.write('E' + str(n), rec.date_start.strftime('%Y-%m-%d') if rec.date_start else '', format1)
            sheet.write('F' + str(n), rec.date_end.strftime('%Y-%m-%d') if rec.date_end else '', format1)
            sheet.write('G' + str(n), contract_value, format1)
            sheet.write('H' + str(n), rec.template_id.name, format1)
            sheet.write('I' + str(n), rec.subscription_id.recurring_total_company, format1)
            sheet.write('J' + str(n), total_bills, format1)
            sheet.write('K' + str(n), pending_bills, format1)

            n += 1
            s_no += 1

        workbook.close()

        fo = open(url + 'Contract Report' + '.xlsx', "rb+")
        values = {
            'name': 'Contract Report.xlsx',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'datas': base64.encodestring(fo.read()),
        }
        attachment_id = self.env['ir.attachment'].sudo().create(values)
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }