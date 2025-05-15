from odoo import models, fields, api, _


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.depends('check_in', 'employee_id')
    def _get_shift_id(self):
        for rec in self:
            shift = self.env['hr.employee.shift'].search([('employee_id', '=', rec.employee_id.id), ('date', '=', rec.check_in.date())], limit=1)
            rec.shift_id = shift.id or False

    shift_id = fields.Many2one('hr.employee.shift', compute='_get_shift_id')


class Employee(models.Model):
    _inherit = 'hr.employee'

    employee_level = fields.Selection([('l1', 'L1'),('l2', 'L2'),('l3', 'L3'),('l4', 'L4'), ('db', 'DB')], string="Level / Database")
    # employee_shift = fields.Many2one('hr.employee.shift')

#     leave_based = fields.Selection([('standard', 'Standard'), ('shift', 'Shift')], string="Leave Based on", default='standard')


class PublicEmployee(models.Model):
    _inherit = 'hr.employee.public'

    employee_level = fields.Selection([('l1', 'L1'), ('l2', 'L2'), ('l3', 'L3'), ('l4', 'L4'), ('db', 'DB')], string="Level / Database", related='employee_id.employee_level')