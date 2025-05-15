from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import tempfile
import binascii


class HrShiftMonthPlan(models.Model):
    _name = "hr.shift.month.plan"
    _description = "HR Shift Plan"

    def compute_shifts(self):
        for rec in self:
            rec.shift_count = self.env['hr.employee.shift'].search_count([('month_plan_id', '=', rec.id)])

    name = fields.Char("Plan Name", help="Provide name for this plan. Eg: January/2022 Shift for All department",
                       required=1)
    date = fields.Date("Month", required=1)
    xlsx_file = fields.Binary(string='XLSX File', required=1)
    file_name = fields.Char(string='File Name')
    shift_count = fields.Integer("Shifts", compute='compute_shifts')

    def action_view_shifts(self):
        return {
            'name': _('Employee Shift'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.shift',
            'views': [[self.env.ref('hr_shift.view_hr_employee_shift_calendar').id, 'calendar']],
            'domain': [('month_plan_id', '=', self.id)],
            'context': {
                'month_plan_id': self.id,
            },
        }

    def generate_shifts(self):
        existing_shifts = self.env['hr.employee.shift'].search_count([('month_plan_id', '=', self.id)])
        if existing_shifts:
            raise UserError(_("Shifts already generated."))
        if self.xlsx_file:
            try:
                fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.xlsx_file))
                fp.seek(0)
                df = pd.read_excel(fp.name)
                for index, row in df.iterrows():
                    employee_id = self.env['hr.employee'].search([('name', '=', row['Name'])], limit=1)
                    if not employee_id:
                        raise UserError(_("Employee %s not found in the system. Please check the name." % row['Name']))
                    for col in range(1, len(row)):
                        shift_id = self.env['hr.shift'].search([('code', '=', row[col])], limit=1)
                        if not shift_id:
                            raise UserError(_("Shift code %s does not exist. Please verify the shift code." % row[col]))
                        shift_date = self.date.replace(day=col)
                        shift_obj = self.env['hr.employee.shift'].create({
                            'employee_id': employee_id.id,
                            'shift_id': shift_id.id,
                            'date': shift_date,
                            'month_plan_id': self.id,
                        })
                        shift_obj.onchange_time()
                        shift_obj.compute_dates()
            except Exception as E:
                raise UserError(_(E))

