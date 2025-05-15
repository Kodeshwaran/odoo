from odoo import api, fields, models
from datetime import datetime, time
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY

#
# class HolidaysRequest(models.Model):
#     _inherit = 'hr.leave'
#
#     def _get_number_of_days(self, date_from, date_to, employee_id):
#         """ Returns a float equals to the timedelta between two dates given as string."""
#         if employee_id:
#             employee = self.env['hr.employee'].browse(employee_id)
#             # We force the company in the domain as we are more than likely in a compute_sudo
#             domain = [('company_id', 'in', self.env.company.ids + self.env.context.get('allowed_company_ids', []))]
#             result = employee._get_work_days_data_batch(date_from, date_to, domain=domain)[employee.id]
#             if self.request_unit_half and result['hours'] > 0:
#                 result['days'] = 0.5
#             return result
#
#         today_hours = self.env.company.resource_calendar_id.get_work_hours_count(
#             datetime.combine(date_from.date(), time.min),
#             datetime.combine(date_from.date(), time.max),
#             False)
#
#         hours = self.env.company.resource_calendar_id.get_work_hours_count(date_from, date_to)
#         days = hours / (today_hours or HOURS_PER_DAY) if not self.request_unit_half else 0.5
#         return {'days': days, 'hours': hours}
#
#
#     @api.depends('date_from', 'date_to', 'employee_id')
#     def _compute_number_of_days(self):
#         for holiday in self:
#             if holiday.date_from and holiday.date_to:
#                 holiday.number_of_days = holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['days']
#             else:
#                 holiday.number_of_days = 0


