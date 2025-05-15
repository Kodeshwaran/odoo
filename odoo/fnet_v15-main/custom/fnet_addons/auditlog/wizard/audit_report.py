from odoo import _, api, fields, models
from odoo.exceptions import UserError


from odoo import models, fields, api, _
import base64
import xlsxwriter
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from time import gmtime, strftime
import string
import pytz
from itertools import accumulate
from io import BytesIO

def to_utc_naive(datetime, record):
    user_tz = record._context.get('tz') or self.env.user.tz
    local = pytz.timezone(user_tz)
    return pytz.utc.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(local).replace(tzinfo=None)


class AuditReport(models.TransientModel):
    _name = 'audit.report'
    rec_name = 'report_file'
    _description = 'Audit Report'

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    report_file = fields.Binary('Audit Report', readonly=True)
    report_file_name = fields.Char('Filename', size=64, readonly=True)

    def action_audit_reporting(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Audit Report.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'valign': 'center'})
        bold = workbook.add_format({'border': 1, 'bold': True, 'align': 'center', 'valign': 'vcenter'})
        bold_1 = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        bold_2 = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 25)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 15)
        sheet.set_column('O:O', 15)
        sheet.set_column('P:P', 15)
        sheet.set_column('Q:Q', 15)
        sheet.set_column('R:R', 15)
        sheet.set_column('S:S', 15)
        sheet.set_column('T:T', 15)
        sheet.set_column('U:U', 15)
        sheet.set_column('V:V', 15)
        sheet.set_column('W:W', 15)
        sheet.set_column('X:X', 15)
        sheet.set_column('Y:Y', 10)
        sheet.set_column('Z:Z', 10)

        start_date = self.date_from
        end_date = self.date_to
        date_from = datetime.combine(start_date, time.min)
        date_to = datetime.combine(end_date, time.max)

        sheet.merge_range('D2:F3', 'AUDIT REPORT(%s - %s)' % (self.date_from.strftime('%d/%m/%Y'), self.date_to.strftime('%d/%m/%Y')), bold)
        sheet.write(5, 0, 'S.No', bold)
        sheet.merge_range(5, 1, 5, 5, 'Original Data', bold)
        sheet.merge_range(5, 6, 5, 10, 'Changed Data', bold)
        sheet.write(6, 1, 'Date', bold)
        sheet.write(6, 2, 'Name', bold)
        sheet.write(6, 3, 'Field Name', bold)
        sheet.write(6, 4, 'Original Value', bold)
        sheet.write(6, 5, 'Created By', bold)
        sheet.write(6, 6, 'Modified On', bold)
        sheet.write(6, 7, 'Name', bold)
        sheet.write(6, 8, 'Field Name', bold)
        sheet.write(6, 9, 'Changed Value', bold)
        sheet.write(6, 10, 'Modified By', bold)

        moves = self.env['auditlog.log.line.view'].search([('model_model', '=', 'account.move'), ('create_date', '>=', date_from), ('create_date', '<=', date_to)])
        no=1
        rows = 7
        cols = 0
        for move in moves:
            move_id = self.env['account.move'].search([('id', '=', move.res_id)])
            print("--------", move_id,"----move_id---\n")
            sheet.write(rows, cols, no, format1)
            sheet.write(rows, cols + 1, (to_utc_naive(datetime.combine(move_id.date, time.min), move_id)).strftime("%d/%m/%Y") if move_id.date else '', format1)
            sheet.write(rows, cols + 2, move.name)
            sheet.write(rows, cols + 3, move.field_description, format1)
            sheet.write(rows, cols + 4, move.old_value_text, format1)
            sheet.write(rows, cols + 5, move_id.user_id.name, format1)
            sheet.write(rows, cols + 6, (to_utc_naive(move.create_date, move)).strftime("%d/%m/%Y"), format1)
            sheet.write(rows, cols + 7, move.name)
            sheet.write(rows, cols + 8, move.field_description, format1)
            sheet.write(rows, cols + 9, move.new_value_text, format1)
            sheet.write(rows, cols + 10, move.user_id.name, format1)
            rows += 1
            no += 1
        move_lines = self.env['auditlog.log.line.view'].search([('model_model', '=', 'account.move.line'), ('create_date', '>=', date_from), ('create_date', '<=', date_to)])
        for line in move_lines:
            move_line_id = self.env['account.move.line'].search([('id', '=', line.res_id)])
            move_id = move_line_id.move_id
            if not move_line_id.exclude_from_invoice_tab:
                sheet.write(rows, cols, no, format1)
                sheet.write(rows, cols + 1, (to_utc_naive(datetime.combine(move_id.date, time.min), move_id)).strftime("%d/%m/%Y") if move_id.date else '', format1)
                sheet.write(rows, cols + 2, move_id.display_name + line.name if move_id.display_name and line.name else line.name)
                sheet.write(rows, cols + 3, line.field_description, format1)
                sheet.write(rows, cols + 4, line.old_value_text, format1)
                sheet.write(rows, cols + 5, move_id.user_id.name, format1)
                sheet.write(rows, cols + 6, (to_utc_naive(line.create_date, line)).strftime("%d/%m/%Y"), format1)
                sheet.write(rows, cols + 7, move_id.display_name + line.name if move_id.display_name and line.name else line.name)
                sheet.write(rows, cols + 8, line.field_description, format1)
                sheet.write(rows, cols + 9, line.new_value_text, format1)
                sheet.write(rows, cols + 10, line.user_id.name, format1)
                rows += 1
                no += 1

        # fp = BytesIO()
        # workbook.save(fp)
        # fp.seek(0)
        # excel_file = base64.encodebytes(fp.getvalue())
        # fp.close()
        # self.write({'excel_file': excel_file})

        workbook.close()
        fo = open(url + 'Audit Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'report_file': out, 'report_file_name': 'Audit Report.xlsx'})
        return {
            'view_mode': 'form',
            'name': 'Audit Report',
            'res_model': 'audit.report',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }