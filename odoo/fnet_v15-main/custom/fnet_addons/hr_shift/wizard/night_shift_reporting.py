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

class NightShiftReporting(models.TransientModel):
    _name = 'hr.night.shift.reporting'
    _rec_name = 'report_details'
    _description = ' Night Shift Reporting'

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    employee_level = fields.Selection([('l1', 'L1'),('l2', 'L2'),('l3', 'L3'),('l4', 'L4'),('db', 'DB')], string="Level")
    # check=fields.Boolean(default=True,invisible=1,compute='compute')
    report_details = fields.Binary('Night Shift Reporting', readonly=True)
    report_details_name = fields.Char('Filename', size=64, readonly=True)




    def action_night_shift_reporting(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Night Shift Reporting.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'valign': 'center','italic': True})
        format3 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center', 'italic': True,'font_color':'#D0312D'})
        format2 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'valign': 'center','italic': True,'bg_color':'#e6be8a'})
        format1.set_text_wrap()
        month_year_format = workbook.add_format({'bold': True, 'border': 1, 'font_color': 'black', 'bg_color': '#84B701', 'align': 'center', 'valign': 'vcenter'})
        heading=workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#84b701', 'align': 'center', 'valign': 'vcenter', 'font_color': 'white'})
        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter','font_size': 10})
        bold_1 = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter','italic': True})

        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 5)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 5)
        sheet.set_column('E:E', 5)
        sheet.set_column('F:F', 5)
        sheet.set_column('G:G', 5)
        sheet.set_column('H:H', 5)
        sheet.set_column('I:I', 5)
        sheet.set_column('J:J', 5)
        sheet.set_column('K:K', 5)
        sheet.set_column('L:L', 5)
        sheet.set_column('M:M', 5)
        sheet.set_column('N:N', 5)
        sheet.set_column('O:O', 5)
        sheet.set_column('P:P', 5)
        sheet.set_column('Q:Q', 5)
        sheet.set_column('R:R', 5)
        sheet.set_column('S:S', 5)
        sheet.set_column('T:T', 5)
        sheet.set_column('U:U', 5)
        sheet.set_column('V:V', 5)
        sheet.set_column('W:W', 5)
        sheet.set_column('X:X', 5)
        sheet.set_column('Y:Y', 5)
        sheet.set_column('Z:Z', 5)
        sheet.set_column('AA:AA', 5)
        sheet.set_column('AB:AB', 5)
        sheet.set_column('AC:AC', 5)
        sheet.set_column('AD:AD', 5)
        sheet.set_column('AE:AE', 5)
        sheet.set_column('AF:AF', 5)
        sheet.set_column('AG:AG', 5)
        sheet.set_column('AH:AH', 5)
        sheet.set_column('AI:AI', 5)
        sheet.set_column('AJ:AJ', 5)
        sheet.set_column('AK:AK', 5)
        sheet.set_column('AL:AL', 5)
        sheet.set_column('AM:AM', 5)
        sheet.set_column('AN:AN', 5)
        sheet.set_column('AO:AO', 5)
        sheet.set_column('AP:AP', 5)
        sheet.set_column('AQ:AQ', 5)


        sheet.merge_range('J2:O2','RIMS TEAM', heading )
        sheet.merge_range('B2:C2','Attendance',bold)
        start_date = self.date_from
        end_date = self.date_to
        date_from = datetime.combine(start_date, time.min)
        dates = []
        while start_date <= end_date:
            dates.append(start_date.isoformat())
            start_date += timedelta(days=1)
        domain = []
        if self.date_from and self.date_to:
            domain.append(('date', '>=', self.date_from))
            domain.append(('date', '<=', self.date_to))
        if self.employee_level:
            domain.append(('employee_level', '=', self.employee_level))
        if not self.employee_level:
            domain.append(('employee_level', '!=', False))
        emp_shift = self.env['hr.employee.shift'].sudo().search(domain)
        total_employees = len(emp_shift.mapped('employee_id'))
        emp2 = emp_shift.filtered(lambda x: x.employee_level == 'db').mapped('employee_id')
        total_emp2 = len(emp2.mapped('employee_id'))
        d_list_row = 2
        d_list_col = 2
        level_col=0
        level_row=0
        col=3
        row=2
        row_1=row+2
        employees = emp_shift.filtered(lambda x: x.employee_level).mapped('employee_id')
        for d_list in dates:
            sheet.write(d_list_row, d_list_col, str(date_from.strftime('%m/%Y')), month_year_format)
            sheet.merge_range(level_row + 2, level_col + 1, level_row + 3, level_col + 1, 'Level', bold)
            sheet.write(d_list_row + 1, d_list_col, 'NAME', bold)
            if self.employee_level:
                sheet.merge_range(d_list_row + 2, d_list_col - 1, d_list_row + 2 + total_employees - 1, d_list_col - 1,dict(self._fields['employee_level'].selection).get(self.employee_level), bold_1)
            datetime_obj = datetime.strptime(d_list, '%Y-%m-%d')
            sheet.write(d_list_row + 1, d_list_col, 'NAME', bold)
            days = datetime_obj.strftime('%a')
            if days in 'Sun & Sat':
                sheet.write(row, col, datetime_obj.strftime('%a'), format3)
            if days not in 'Sun & Sat':
                sheet.write(row, col, datetime_obj.strftime('%a'), format1)
            sheet.write(row + 1, col, datetime_obj.strftime('%d'), format2)
            if not self.employee_level:
                sheet.merge_range(level_row + 18, level_col + 10, level_row + 18, level_col + 15, 'DATABASE TEAM', heading)
                sheet.write(d_list_row+18, d_list_col, str(date_from.strftime('%m/%Y')), month_year_format)
                sheet.merge_range(level_row + 20, level_col + 1, level_row + 21, level_col + 1, 'Level', bold)
                sheet.write(d_list_row + 19, d_list_col, 'NAME', bold)
                for rec in employees:
                        if rec.employee_level =='db':
                            sheet.merge_range(d_list_row + 20, d_list_col - 1, d_list_row + 20 + total_emp2-1 ,d_list_col - 1,dict(self._fields['employee_level'].selection).get(rec.employee_level), bold_1)
                datetime_obj = datetime.strptime(d_list, '%Y-%m-%d')
                sheet.write(d_list_row + 1, d_list_col, 'NAME', bold)
                days = datetime_obj.strftime('%a')
                if days in 'Sun & Sat':
                    sheet.write(row+18, col, datetime_obj.strftime('%a'), format3)
                if days not in 'Sun & Sat':
                    sheet.write(row+18, col, datetime_obj.strftime('%a'), format1)
                sheet.write(row + 19, col, datetime_obj.strftime('%d'), format2)
            emp_row = d_list_row + 2
            emp_col = d_list_col + 0
            shift_row = level_row + 4
            for emp in employees:
                lev_row = emp_row
                lev_col = emp_col - 1
                if not self.employee_level:
                    if 'db' in emp.employee_level:
                        sheet.write(emp_row+5, emp_col, emp.name, bold_1)
                    if 'l1' in emp.employee_level:
                        sheet.write(lev_row, lev_col, "L1" if emp.employee_level == 'l1' else '', bold_1)
                        sheet.write(emp_row, emp_col, (emp.name)if emp.employee_level == 'l1' else '',bold_1)
                    if emp.employee_level == 'l2':
                        sheet.write(lev_row, lev_col,'L2' if emp.employee_level == 'l2' else '', bold_1)
                        sheet.write(emp_row, emp_col, (emp.name) if emp.employee_level == 'l2' else '', bold_1)
                if self.employee_level == emp.employee_level:
                    sheet.write(emp_row, emp_col, emp.name, bold_1)
                emp_row += 1
                shift_col = level_col + 3
                emp_records = emp_shift.filtered(lambda x: x.employee_id.id ==emp.id)
                for shift in emp_records:
                    if not self.employee_level:
                        if shift.employee_level == 'db' and shift.shift_id.code == 'N':
                            sheet.write(shift_row+5, shift_col,  'Night' if shift.shift_id.code else '', format1)
                        if shift.employee_level != 'db' and shift.shift_id.code == 'N':
                            sheet.write(shift_row, shift_col, 'Night' if shift.shift_id.code else '',format1)
                    if self.employee_level:
                        if shift.shift_id.code == 'N':
                            sheet.write(shift_row, shift_col,'Night' if shift.shift_id.code else '',format1)
                    shift_col += 1
                shift_row += 1
            col += 1
        col_1 = col + 1
        sheet.merge_range(row + 1, col, row, col + 1, 'Total Night Shift Days', format2)
        for emp in employees:
            emp_rec = emp_shift.filtered(lambda x: x.employee_id.id == emp.id and x.shift_id.code == 'N')
            if not self.employee_level:
                row_0=row+18
                col_0=col
                if 'db' in emp.employee_level:
                    sheet.merge_range(row_1+5, col_1 - 1, row_1+5, col_1, len(emp_rec), format1)
                    sheet.merge_range(row_0 + 1, col_0, row_0, col_0 + 1, 'Total Night Shift Days', format2)

                else:
                    sheet.merge_range(row_1, col_1 - 1, row_1, col_1, len(emp_rec), format1)
            if self.employee_level:
                sheet.merge_range(row_1, col_1 - 1, row_1, col_1, len(emp_rec), format1)
            row_1 += 1


        workbook.close()
        fo = open(url + 'Night Shift Reporting.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'report_details': out, 'report_details_name': 'Night Shift Reporting.xlsx'})
        return {
            'view_mode': 'form',
            'res_model': 'hr.night.shift.reporting',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
