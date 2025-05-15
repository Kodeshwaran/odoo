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

def to_utc_naive(datetime, record):
    user_tz = record._context.get('tz') or self.env.user.tz
    local = pytz.timezone(user_tz)
    return pytz.utc.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(local).replace(tzinfo=None)

class ShiftReporting(models.TransientModel):
    _name = 'hr.shift.reporting'
    _rec_name = 'report_details'
    _description = 'Shift Reporting'

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    employee_level = fields.Selection([('l1', 'L1'),('l2', 'L2'),('l3', 'L3'),('l4', 'L4'),('db', 'DB')], string="Employee", required=True)
    report_details = fields.Binary('Shift Reporting', readonly=True)
    report_details_name = fields.Char('Filename', size=64, readonly=True)


    def action_shift_reporting(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Shift Reporting.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center'})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF66', 'border': 1, 'right': 1})
        sub_title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#90ee90', 'border': 1, 'right': 1})
        parent_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#F0CCB0'})
        sale_type_format = workbook.add_format({'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#D3D3D3'})
        total_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#FFCCCB'})
        format1.set_text_wrap()
        month_year_format = workbook.add_format({'bold': True, 'border': 1, 'font_color': 'white', 'bg_color': '#BF0000', 'align': 'center', 'valign': 'vcenter'})
        date_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#ffffbf', 'align': 'center', 'valign': 'vcenter'})
        shift_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#c8f7c8', 'align': 'center', 'valign': 'vcenter'})
        week_off_format = workbook.add_format({'border': 1, 'bg_color': '#FEBE00', 'align': 'center', 'valign': 'vcenter'})
        shift_swap_format = workbook.add_format({'border': 1, 'font_color': 'white', 'bg_color': '#2a9df4', 'align': 'center', 'valign': 'vcenter'})
        bold = workbook.add_format({'border': 1, 'bold': True, 'align': 'center', 'valign': 'vcenter'})
        bold_1 = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        bold_2 = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 10)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 10)
        sheet.set_column('K:K', 10)
        sheet.set_column('L:L', 10)
        sheet.set_column('M:M', 10)
        sheet.set_column('N:N', 10)
        sheet.set_column('O:O', 10)
        sheet.set_column('P:P', 10)
        sheet.set_column('Q:Q', 10)
        sheet.set_column('R:R', 10)
        sheet.set_column('S:S', 10)
        sheet.set_column('T:T', 10)
        sheet.set_column('U:U', 10)
        sheet.set_column('V:V', 10)
        sheet.set_column('W:W', 10)
        sheet.set_column('X:X', 10)
        sheet.set_column('Y:Y', 10)
        sheet.set_column('Z:Z', 10)
        sheet.set_column('AA:AA', 10)
        sheet.set_column('AB:AB', 10)
        sheet.set_column('AC:AC', 10)
        sheet.set_column('AD:AD', 10)
        sheet.set_column('AE:AE', 10)
        sheet.set_column('AF:AF', 10)
        sheet.set_column('AG:AG', 10)
        sheet.set_column('AH:AH', 10)
        sheet.set_column('AI:AI', 10)
        sheet.set_column('AJ:AJ', 10)
        sheet.set_column('AK:AK', 10)
        sheet.set_column('AL:AL', 10)
        sheet.set_column('AM:AM', 10)
        sheet.set_column('AN:AN', 10)
        sheet.set_column('AO:AO', 10)
        sheet.set_column('AP:AP', 10)
        sheet.set_column('AQ:AQ', 10)

        start_date = self.date_from
        end_date = self.date_to
        date_from = datetime.combine(start_date, time.min)
        date_to = datetime.combine(end_date, time.max)
        dates = []
        date_lists = list()
        length_to_split = 5
        while start_date <= end_date:
            dates.append(start_date.isoformat())
            start_date += timedelta(days=1)
        for i in range(0, len(dates), length_to_split):
            date_lists.append(dates[i:i+length_to_split])
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
        d_list_row = 1
        d_list_col = 0
        shift_row = 1
        for d_list in date_lists:
            shift_col = 0
            sheet.merge_range(d_list_row, d_list_col, d_list_row, d_list_col + 2, str(date_from.strftime('%m/%Y')), month_year_format)
            sheet.merge_range(d_list_row + 1, d_list_col, d_list_row + 1, d_list_col + 2, 'NAME', bold)
            sheet.merge_range(d_list_row + 2, d_list_col, d_list_row + 2 + total_employees - 1, d_list_col,dict(self._fields['employee_level'].selection).get(self.employee_level), bold_1)
            employees = emp_shift.filtered(lambda x: x.employee_level == self.employee_level).mapped('employee_id')
            emp_row = d_list_row + 2
            emp_col = d_list_col + 1
            for emp in employees:
                sheet.merge_range(emp_row, emp_col, emp_row, emp_col + 1, emp.name, bold_1)
                emp_row += 1
            for d in d_list:
                datetime_obj = datetime.strptime(d, '%Y-%m-%d')
                sheet.merge_range(shift_row, shift_col + 3, shift_row, shift_col + 5, datetime_obj.strftime('%d'), date_format)
                sheet.write(shift_row + 1, shift_col + 3, 'Shift', shift_format)
                sheet.write(shift_row + 1, shift_col + 4, 'Login', date_format)
                sheet.write(shift_row + 1, shift_col + 5, 'Logout', date_format)
                emp_val_row = shift_row + 2
                for emp in employees:
                    emp_val_col = shift_col + 3
                    emp_records = emp_shift.filtered(lambda x: x.employee_id.id == emp.id and x.date.strftime('%Y-%m-%d') == d)
                    for shift in emp_records:
                        if shift.shift_swapped:
                            sheet.write(emp_val_row, emp_val_col, shift.shift_id.code, shift_swap_format)
                            sheet.write(emp_val_row, emp_val_col + 1, (to_utc_naive(shift.actual_date_start, shift)).strftime("%I:%M %p") if shift.actual_date_start else '', bold_1)
                            sheet.write(emp_val_row, emp_val_col + 2, (to_utc_naive(shift.actual_date_end, shift)).strftime("%I:%M %p") if shift.actual_date_end else '', bold_1)
                        elif shift.shift_id.code != 'WO':
                            sheet.write(emp_val_row, emp_val_col, shift.shift_id.code, bold_1)
                        else:
                            sheet.merge_range(emp_val_row, emp_val_col, emp_val_row, emp_val_col + 2, shift.shift_id.code, week_off_format)
                        sheet.write(emp_val_row, emp_val_col + 1, (to_utc_naive(shift.actual_date_start, shift)).strftime("%I:%M %p") if shift.actual_date_start else '', bold_1)
                        sheet.write(emp_val_row, emp_val_col + 2, (to_utc_naive(shift.actual_date_end, shift)).strftime("%I:%M %p") if shift.actual_date_end else '', bold_1)
                        emp_val_col += 3
                    emp_val_row += 1
                shift_col += 3
            shift_row += 4 + total_employees
            d_list_row += (4 + total_employees)

        workbook.close()
        fo = open(url + 'Shift Reporting.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'report_details': out, 'report_details_name': 'Shift Reporting.xlsx'})
        return {
            'view_mode': 'form',
            'res_model': 'hr.shift.reporting',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }