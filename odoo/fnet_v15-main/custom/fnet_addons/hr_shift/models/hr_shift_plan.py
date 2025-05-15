# from calendar import monthrange
# from datetime import timedelta, datetime
# from dateutil.relativedelta import relativedelta
# from odoo import models, fields

#
# class HrShiftPlan(models.Model):
#     _name = "hr.shift.plan"
#     _description = "HR Shift Plan"
#
#     name = fields.Char("Plan Name", help="Provide name for this plan. Eg: January/2022 Shift for All department",
#                        required=1)
#     based_on = fields.Selection([('employee', 'Employees'), ('department', 'Department')], string="Based On",
#                                 default='department', required=1)
#     start_date = fields.Date("From", required=1)
#     end_date = fields.Date("From", required=1)
#     department_id = fields.Many2many('hr.department', string="Departments")
#     employee_ids = fields.Many2many('hr.employee', string="Employees")
#     shift_ids = fields.Many2many('hr.shift', string="Shifts & Order", required=1)
#     employee_shift_ids = fields.One2many('hr.employee.shift', 'plan_id', string="Employee Shift")
#     employee_level = fields.Selection([('0', 'L0'), ('1', 'L1'), ('2', 'L2'), ('3', 'L3'), ('4', 'L4'), ('5', 'L5')],
#                                       string="Engineer Level", multi=True)
#     number_of_leaves = fields.Integer(required=True, string="Total Number of leaves")
#
#     def default_get(self, fields_list):
#         defaults = super().default_get(fields_list)
#         today = fields.Date.today()
#         start_date = (today + relativedelta(months=1)).replace(day=1)
#         end_date = start_date.replace(day=monthrange(start_date.year, start_date.month)[1])
#         number_of_leaves = 2
#         defaults.update({
#             'start_date': start_date,
#             'end_date': end_date,
#             'number_of_leaves': number_of_leaves,
#         })
#         return defaults
#
#     @staticmethod
#     def daterange(start_date, end_date):
#         for n in range(int((end_date - start_date).days) + 1):
#             yield start_date + timedelta(n)
#
#     def generate_shifts(self):
#         l1_employees = self.employee_ids.filtered(lambda x: x.employee_level == 'L1')
#         number_of_leaves = self.number_of_leaves
#         # number_of_general_shift = monthrange(self.start_date.year, self.start_date.month)[1] - (
#         #         len(l1_employees) * number_of_leaves)
#         for employee in l1_employees:
#             shifts = self.allocate_shifts_for_employee(self.start_date, self.end_date+timedelta(days=1), employee,
#                                                        employee.last_shift_count, employee.last_shift)
#             shift_obj = self.env['hr.employee.shift']
#             for shift in shifts:
#                 shift.update({'plan_id': self.id})
#                 shift_obj += shift_obj.create(shift)
#             shift_obj.onchange_time()
#             shift_obj.compute_dates()
#
#     def allocate_shifts_for_employee(self, start_date, end_date, employee, last_shift_count, last_shift):
#         shift_order = ['Night', 'Second', 'First', 'Night', 'Second', 'First']
#         shifts = []
#         current_shift_index = 0
#         if last_shift == 'Night':
#             current_shift_index = 0
#         if last_shift in ['Second', 'WeekOff']:
#             current_shift_index = 1
#         if last_shift == 'First':
#             current_shift_index = 2
#         current_shift_end_time = start_date - timedelta(hours=1)
#         while current_shift_end_time < end_date:
#             shift_name = shift_order[current_shift_index]
#             shift_id = self.env['hr.shift'].search([('name', '=', shift_name)], limit=1)
#             for day in range(0, last_shift_count):
#                 shift_end_time = current_shift_end_time + timedelta(days=1) - timedelta(seconds=1)
#                 if shift_end_time > end_date:
#                     shift_end_time = end_date
#                 shift = {
#                     'employee_id': employee.id,
#                     'shift_id': shift_id.id,
#                     'date': current_shift_end_time,
#                 }
#                 shifts.append(shift)
#                 current_shift_end_time = shift_end_time
#                 if current_shift_end_time >= end_date:
#                     break
#             if current_shift_end_time >= end_date:
#                 break
#             current_shift_index = (current_shift_index + 1) % len(shift_order)
#             last_shift_count = 5
#             if shift_name == 'Night':
#                 for day in range(0, 2):
#                     shift_end_time = current_shift_end_time + timedelta(days=1) - timedelta(seconds=1)
#                     shift_id = self.env['hr.shift'].search([('name', '=', 'WeekOff')], limit=1)
#                     if shift_end_time > end_date:
#                         shift_end_time = end_date
#                     shifts.append({
#                         'employee_id': employee.id,
#                         'shift_id': shift_id.id,
#                         'date': current_shift_end_time,
#                     })
#                     current_shift_end_time = shift_end_time
#             else:
#                 shift_end_time = current_shift_end_time + timedelta(days=1) - timedelta(seconds=1)
#                 shift_id = self.env['hr.shift'].search([('name', '=', 'WeekOff')], limit=1)
#                 if shift_end_time > end_date:
#                     shift_end_time = end_date
#                 shifts.append({
#                     'employee_id': employee.id,
#                     'shift_id': shift_id.id,
#                     'date': current_shift_end_time,
#                 })
#                 current_shift_end_time = shift_end_time
#         return shifts

