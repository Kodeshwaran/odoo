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


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


class NewAttendanceRimsReport(models.TransientModel):
    _name = 'new.attendance.report'
    _description = 'New Attendance Report'

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    report_details = fields.Binary(' Attendance Reporting', readonly=True)
    report_details_name = fields.Char('Filename', size=64, readonly=True)
    # team_id = fields.Many2one('hr.department','Department')
    # team = fields.Selection([('new', 'New')], 'Department')
    team=fields.Many2one('hr.department','Department')

    def action_attendance_report(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Attendance Reporting.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'valign': 'center', 'italic': True})
        format2 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center', 'italic': True})
        format4 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'valign': 'center', 'italic': True,'bg_color': '#ffff00'})
        format5 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'valign': 'center', 'italic': True,'bg_color': '#ea9999'})
        format6= workbook.add_format({'font_size': 8, 'align': 'vcenter', 'valign': 'center', 'italic': True,'bg_color': '#f79646'})

        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'vcenter', 'valign': 'center', 'italic': True, 'font_color': '#D0312D'})
        # format1.set_text_wrap()
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:AP', 5)
        start_date = self.date_from
        end_date = self.date_to
        dates = []
        months = {}
        while start_date <= end_date:
            dates.append(start_date.isoformat())
            start_date += timedelta(days=1)
            if start_date.month not in months:
                months[start_date.month] = []
            months[start_date.month] += [start_date.day]
        col_start = 6
        col_end = 6
        for month, days in months.items():
            col_end += len(days)
            sheet.merge_range(0, col_start+1, 0, col_end, '%s/%s' %(month, self.date_to.year), format2)
            col_start = col_end + 1
        employees = self.env['hr.employee'].sudo().search([('department_id', '=', self.team.id), ('employee_level', '!=', False)])
        row = 2
        sheet.write(row, 0, 'S.No', format1)
        sheet.write(row, 1, 'EMP ID', format1)
        sheet.write(row, 2, 'Name', format1)
        sheet.write(row,3,'Level',format1)
        sheet.write(row, 4, 'Reporting Head', format1)
        sheet.write(row, 5, 'Department', format1)
        sheet.write(row, 6, 'Site Name', format1)
        row_date = 1
        col_date = 7
        for d_list in dates:
            datetime_obj = datetime.strptime(d_list, '%Y-%m-%d')
            days = datetime_obj.strftime('%a')
            month = datetime_obj.strftime('%m')
            if self.date_from.strftime('%a') in month:
                sheet.merge_range(row_date-1, col_date,row_date,col_date, datetime_obj.strftime('%a'), format1)

            sheet.write(row_date, col_date, datetime_obj.strftime('%a'), format1)
            if days in 'Sun & Sat':
                sheet.write(row_date, col_date, datetime_obj.strftime('%a'), format3)
            sheet.write(row_date+1, col_date, datetime_obj.strftime('%d'), format1)
            col_date += 1
        row += 1
        s_no = 1
        for employee in employees:
            sheet.write(row, 0, s_no, format1)
            sheet.write(row, 1, employee.employeeid, format1)
            sheet.write(row, 2, employee.name, format1)
            sheet.write(row,3,employee.employee_level.upper(),format1)
            sheet.write(row, 4, employee.coach_id.name, format1)
            sheet.write(row, 5, employee.department_id.name, format1)
            sheet.write(row, 6, 'Headoffice', format1)
            shift_col = 7
            nil_count = 0
            for d_list in dates:
                datetime_obj = datetime.strptime(d_list, '%Y-%m-%d')
                shift = self.env['hr.employee.shift'].sudo().search(
                    [('date', '=', datetime_obj), ('employee_id', '=', employee.id)])
                shift_leave = self.env['hr.leave'].sudo().search([
                    ('request_date_from', '<=', datetime_obj),
                    ('request_date_to', '>=', datetime_obj),
                    ('employee_id', '=', employee.id),
                ])
                if shift:
                    if shift.actual_date_start:
                        sheet.write(row, shift_col, " P", format1)
                    elif shift.shift_id.name == 'WeekOff':
                        sheet.write(row, shift_col, " WO", format5)
                    else:
                        sheet.write(row, shift_col, " Ab", format4)
                        nil_count += 1

                    if shift_leave:
                        leave_types = shift_leave.mapped('holiday_status_id.code')
                        for leave in leave_types:
                             sheet.write(row, shift_col,leave, format6)

                shift_col += 1
            last_shift_count=shift_col
            sheet.merge_range(row_date+1,col_date+1,row_date,col_date,'Total Leave Taken',format1)
            sheet.merge_range(row, last_shift_count , row,last_shift_count+1, nil_count, format1)
            row += 1
            s_no += 1
        workbook.close()
        fo = open(url + 'Attendance Reporting.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'report_details': out, 'report_details_name': 'Attendance Reporting.xlsx'})
        return {
            'view_mode': 'form',
            'res_model': 'new.attendance.report',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

