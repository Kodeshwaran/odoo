# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta, time
import xlsxwriter
from io import StringIO
import base64
import pytz
import calendar


class HrAttendanceReportWizard(models.TransientModel):
    _name = 'hr.attendance.report.wizard'

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    attendance_filedata = fields.Binary('Download file', readonly=True)
    attendance_filename = fields.Char('Filename', size=64, readonly=True)

    def get_attendance_report(self):
        # output = StringIO()
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Overall Attendance Report.xlsx', {'remove_timezone': True})
        worksheet = workbook.add_worksheet()

        merge_format1 = workbook.add_format(
            {'bold': 1, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Liberation Serif', })
        merge_format2 = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'underline': 'underline',
             'font_name': 'Liberation Serif', })
        merge_format3 = workbook.add_format({'border': 1, 'align': 'left', 'font_name': 'Liberation Serif'})
        merge_format4 = workbook.add_format(
            {'border': 1, 'align': 'left', 'font_name': 'Liberation Serif', 'num_format': 'd-m-yyyy hh:mm:ss'})
        merge_format5 = workbook.add_format(
            {'border': 1, 'align': 'left', 'font_name': 'Liberation Serif', 'num_format': '#,##0,0.00'})
        merge_format6 = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Liberation Serif'})
        holiday_format = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Liberation Serif', 'bg_color': '#90EE90'})
        leave_format = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Liberation Serif', 'bg_color': 'yellow'})
        present_format = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Liberation Serif', 'bg_color': '#ADD8E6'})
        resign_format = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Liberation Serif', 'bg_color': 'red', 'color': 'white'})
        absent_format = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Liberation Serif', 'bg_color': '#FF7F7F'})
        merge_format7 = workbook.add_format(
            {'border': 1, 'align': 'center', 'font_name': 'Liberation Serif', 'bg_color': '#D3D3D3', 'text_wrap': True})

        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 7)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.merge_range('A1:E1', self.env.company.name, merge_format1)
        worksheet.merge_range('A2:E2', 'ATTENDANCE REPORT', merge_format1)
        worksheet.write('A4', "S.No", merge_format7)
        worksheet.write('B4', "EMP ID", merge_format7)
        worksheet.write('C4', "Employee Name", merge_format7)
        worksheet.write('D4', "Department", merge_format7)
        worksheet.write('E4', "Site Name", merge_format7)
        if self.date_from.month != self.date_to.month:
            date_from_last = self.date_from.replace(day=calendar.monthrange(self.date_from.year, self.date_from.month)[1])
            date_from_length = (date_from_last - self.date_from).days
            date_to_last = self.date_to.replace(day=1)
            date_to_length = (self.date_to - date_to_last).days
            worksheet.set_column(5, 5 + date_from_length + date_to_length + 1, 2)
            worksheet.merge_range(3, 5, 3, 5 + date_from_length, self.date_from.strftime('%B'), merge_format7)
            worksheet.merge_range(3, 5 + date_from_length + 1, 3, 5 + date_from_length + date_to_length + 1, self.date_to.strftime('%B'), merge_format7)
        else:
            date_length = (self.date_to - self.date_from).days
            worksheet.set_column(5, 5 + date_length + 1, 2)
            worksheet.merge_range(3, 5, 3, 5 + date_length, self.date_from.strftime('%B'), merge_format7)
        date_list = [self.date_from + timedelta(days=x) for x in range((self.date_to - self.date_from).days + 1)]
        date_col = 5
        for date in date_list:
            worksheet.write(4, date_col, date.strftime('%d'), merge_format6)
            date_col += 1
        worksheet.write(3, date_col, "No of leaves Taken", merge_format7)
        worksheet.write(3, date_col + 1, "Total CL Allocated", merge_format7)
        worksheet.write(3, date_col + 2, "CL Taken", merge_format7)
        worksheet.write(3, date_col + 3, "Balance of CL", merge_format7)
        worksheet.write(3, date_col + 4, "Total PL Allocated", merge_format7)
        worksheet.write(3, date_col + 5, "PL Taken", merge_format7)
        worksheet.write(3, date_col + 6, "Balance of PL", merge_format7)
        worksheet.write(3, date_col + 7, "LOP", merge_format7)
        n = 6
        c = 1
        employees = self.env['hr.employee'].sudo().search([('employee_categ', '=', 'employee')])
        for department in employees.mapped('department_id'):
            for location in employees.filtered(lambda x: x.department_id.id == department.id).mapped('work_location_id'):
                for employee in employees.filtered(lambda x: x.department_id.id == department.id and x.work_location_id.id == location.id):
                    worksheet.write('A' + str(n), str(c), merge_format6)
                    worksheet.write('B' + str(n), employee.employeeid, merge_format6)
                    worksheet.write('C' + str(n), employee.name, merge_format6)
                    worksheet.write('D' + str(n), employee.department_id.name, merge_format6)
                    worksheet.write('E' + str(n), employee.work_location_id.name if employee.work_location_id else '', merge_format6)
                    col = 5
                    for date in date_list:
                        day_from = datetime.combine(fields.Date.from_string(date), time.min)
                        day_to = datetime.combine(fields.Date.from_string(date), time.max)
                        work_data = employee.get_work_days_data(day_from, day_to, calendar=employee.emp_resource_calendar_id if employee.is_unique_calendar else employee.work_location_id.resource_calendar_id)
                        attendance = self.env['hr.attendance'].sudo().search([('employee_id', '=', employee.id)]).filtered(lambda x: x.check_in.date() == date)
                        shift = self.env['hr.employee.shift'].sudo().search([('employee_id', '=', employee.id), ('date', '=', date)], limit=1)
                        leave = self.env['hr.leave'].sudo().search([('employee_id', '=', employee.id), ('date_from', '>=', date), ('date_to', '<=', date), ('state',  '=', 'validate')],limit=1)
                        if employee.employee_level:
                            if employee.contract_id.state != 'open' and employee.contract_id.date_end and employee.contract_id.date_end < date:
                                date_length = (self.date_to - date).days
                                worksheet.merge_range(n - 1, col, n - 1, col + date_length, 'Exit', resign_format)
                                col += 1
                                continue
                            elif leave:
                                worksheet.write(n - 1, col, leave.holiday_status_id.code, leave_format)
                            elif shift and not attendance:
                                if shift.shift_id.code == 'WO':
                                    worksheet.write(n - 1, col, shift.shift_id.code, present_format)
                                else:
                                    worksheet.write(n - 1, col, 'AB', absent_format)
                            else:
                                worksheet.write(n - 1, col,shift.shift_id.code if shift.shift_id.code != 'WO' else 'P/WO',present_format)
                        elif work_data['days'] == 1:
                            if employee.contract_id.state != 'open' and employee.contract_id.date_end and employee.contract_id.date_end < date:
                                date_length = (self.date_to - date).days
                                worksheet.merge_range(n - 1, col, n - 1, col + date_length, 'Exit', resign_format)
                                col += 1
                                continue
                            elif leave:
                                worksheet.write(n - 1, col, leave.holiday_status_id.code, leave_format)
                            elif attendance:
                                worksheet.write(n - 1, col, 'P', present_format)
                            else:
                                worksheet.write(n - 1, col, 'AB', absent_format)
                        else:
                            worksheet.write(n - 1, col, 'H', holiday_format)
                        col += 1
                    total_leave_count = 0
                    cl_count = 0
                    pl_count = 0
                    lop_count = 0
                    cl_allocation = self.env['hr.leave.allocation'].sudo().search([('employee_id', '=', employee.id), ('holiday_status_id.code', '=', 'CL'), ('state',  '=', 'validate')])
                    pl_allocation = self.env['hr.leave.allocation'].sudo().search([('employee_id', '=', employee.id), ('holiday_status_id.code', '=', 'PL'), ('state',  '=', 'validate')])
                    for dat in date_list:
                        leave = self.env['hr.leave'].sudo().search([('employee_id', '=', employee.id), ('date_from',  '>=', dat), ('date_to',  '<=', dat), ('state',  '=', 'validate')])
                        if leave:
                            total_leave_count += 1
                            if leave.holiday_status_id.code == 'CL':
                                cl_count += 1
                            elif leave.holiday_status_id.code == 'PL':
                                pl_count += 1
                            else:
                                lop_count += 1
                    worksheet.write(n - 1, col, total_leave_count, merge_format6)
                    worksheet.write(n - 1, col + 1, sum(cl_allocation.mapped('number_of_days')), merge_format6)
                    worksheet.write(n - 1, col + 2, cl_count, merge_format6)
                    worksheet.write(n - 1, col + 3, sum(cl_allocation.mapped('number_of_days')) - sum(cl_allocation.mapped('leaves_taken')), merge_format6)
                    worksheet.write(n - 1, col + 4, sum(pl_allocation.mapped('number_of_days')), merge_format6)
                    worksheet.write(n - 1, col + 5, pl_count, merge_format6)
                    worksheet.write(n - 1, col + 6, sum(pl_allocation.mapped('number_of_days')) - sum(pl_allocation.mapped('leaves_taken')), merge_format6)
                    worksheet.write(n - 1, col + 7, lop_count, merge_format6)
                    n = n + 1
                    c = c + 1

        workbook.close()
        fo = open(url + 'Overall Attendance Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodebytes(data)
        filename = 'Overall Attendance Report(%s).xlsx' % (self.date_from.strftime('%d %B %Y') + ' ' + '-' + ' ' + self.date_to.strftime('%d %B %Y'))
        self.write({'attendance_filedata': out, 'attendance_filename': filename})
        return {
                'name': 'Overall Attendance Report',
                'res_model': 'hr.attendance.report.wizard',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'nodestroy': True,
                'res_id': self.id
                }
