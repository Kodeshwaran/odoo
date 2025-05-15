from odoo import models, api, fields, _
from datetime import datetime
from dateutil import relativedelta
import xlsxwriter
import decimal
import base64
import string

class MarginReport(models.TransientModel):
    _name = 'sale.margin.report'
    _description = 'Margin Report'

    partner_id = fields.Many2one('res.partner', string="Customer")
    date_from = fields.Date(string="From",required=True)
    date_to = fields.Date(string="To",required=True)
    sales_person = fields.Many2one('res.users', string="Sales Person")
    sale_type = fields.Many2one('sale.type', string="Sale Type")
    report = fields.Binary('Download file', filters='.xls', readonly=True)
    name = fields.Char('File Name', size=32)

    def generate_xls_report(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Sale Margin Report.xlsx')
        sheet = workbook.add_worksheet()
        domain = [('move_type', '=', 'out_invoice'),('state', '=', 'posted'),
                                                    ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to)]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.sales_person:
            domain.append(('invoice_user_id', '=', self.sales_person.id))
        if self.sale_type:
            domain.append(('sale_type_id', '=', self.sale_type.id))
        invoices = self.env['account.move'].search(domain)
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center', 'color': 'red', 'bold': True})
        format1.set_text_wrap()
        format2 = workbook.add_format({'font_size': 12, 'align': 'center'})
        format3 = workbook.add_format({'font_size': 12, 'align': 'center', 'num_format': 'dd-mm-yyyy'})
        sheet.set_row(0, 40)
        sheet.set_column(0, 11, 20)

        row = 0
        col = 0
        sheet.write(row, col, 'NAME', format1)
        sheet.write(row, col + 1, 'CUSTOMER', format1)
        sheet.write(row, col + 2, 'INVOICE DATE', format1)
        sheet.write(row, col + 3, 'SALES PERSON', format1)
        sheet.write(row, col + 4, 'DUE DATE', format1)
        sheet.write(row, col + 5, 'SALE TYPE', format1)
        sheet.write(row, col + 6, 'SALE SUB-TYPE', format1)
        sheet.write(row, col + 7, 'UNTAXED AMOUNT', format1)
        sheet.write(row, col + 8, 'AMOUNT DUE', format1)
        sheet.write(row, col + 9, 'MARGIN', format1)
        sheet.write(row, col + 10, 'MARGIN PERCENTAGE', format1)
        for inv in invoices:
            row += 1
            sheet.write(row, col, inv.name, format2)
            sheet.write(row, col + 1, inv.partner_id.name, format2)
            sheet.write(row, col + 2, inv.invoice_date, format3)
            sheet.write(row, col + 3, inv.invoice_user_id.name, format3)
            sheet.write(row, col + 4, inv.invoice_date_due, format3)
            sheet.write(row, col + 5, inv.sale_type_id.name if inv.sale_type_id else '', format2)
            sheet.write(row, col + 6, inv.sales_sub_types.name if inv.sales_sub_types else '', format2)
            sheet.write(row, col + 7, inv.amount_untaxed, format2)
            sheet.write(row, col + 8, inv.amount_residual, format2)
            sheet.write(row, col + 9, inv.margin_amount, format2)
            sheet.write(row, col + 10, round(inv.margin_amt_percent * 100, 2), format2)

        workbook.close()
        fo = open(url + 'Sale Margin Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodebytes(data)
        self.write({'report': out, 'name': 'Sale Margin Report.xlsx'})
        return {
            'name': 'Margin Report',
            'res_model': 'sale.margin.report',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'nodestroy': True,
            'res_id': self.id,
        }

