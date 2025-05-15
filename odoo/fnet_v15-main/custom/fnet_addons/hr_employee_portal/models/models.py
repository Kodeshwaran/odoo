from odoo import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    def action_open_my_profile(self):
        employee = self.env['hr.employee.public'].search([('user_id', '=', self.env.uid)])
        if employee:
            action = {
                "name": "Profile",
                "type": "ir.actions.act_window",
                "res_model": "hr.employee.public",
                "views": [[self.env.ref('hr.hr_employee_public_view_form').id, "form"]],
                "res_id": employee.id,
                'target': 'inline',
            }
            return action


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups="base.group_user  ", tracking=True)


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups="base.group_user  ", tracking=True, related="employee_id.gender")