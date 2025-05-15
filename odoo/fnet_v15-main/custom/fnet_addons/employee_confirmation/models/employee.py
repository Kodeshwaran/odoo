# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    probation_status = fields.Selection([('progress', 'In Progress'), ('review', 'Being Reviewed'), ('done', 'Done'),
                                         ], string="Probation Status", default='progress', readonly=True)
    wedding_date = fields.Date(string="Wedding Date")
    is_intern = fields.Boolean('Is Intern')
    address_proof = fields.Boolean('Address Verified')
    date_internship = fields.Date('Internship End Date')
    last_name = fields.Char(string="Last Name")


class HrEmployeeInherited(models.Model):
    _inherit = 'hr.employee'

    birthday_image = fields.Binary('Birthday Image')
    birthday_filename = fields.Char('Filename', size=64, readonly=True)
    wedding_image = fields.Binary('Wedding Image')
    wedding_filename = fields.Char('Filename', size=64, readonly=True)

    def open_probation_review(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Probation Review Form',
            'view_mode': 'tree,form',
            'res_model': 'probation.review',
            'domain': [('employee_id', '=', self.id)],
            'context': "{'default_employee_id': active_id}"
        }

    def employee_wishes_alert(self):
        if self.env.user.company_id.birthday_wedding_wishes:
            # birthday_employees = self.env['hr.employee'].search([('birthday', '=', fields.Date.today())])
            birthday_employees = self.env['hr.employee'].search([]).filtered(lambda x: x.birthday and x.birthday.strftime('%d-%m') == fields.Date.today().strftime('%d-%m'))
            for emp in birthday_employees:
                dic_emp = [{'email_cc': self.env.user.company_id.wishes_mail_cc,
                            'birthday_message': self.env.user.company_id.birthday_message}]
                ctx = {'records': dic_emp}
                temp_id = self.env.ref('employee_confirmation.email_template_employee_birthday_wishes').id
                self.env['mail.template'].browse(temp_id).with_context(ctx).send_mail(emp.id, force_send=True)
            wedding_employees = self.env['hr.employee'].search([('marital', '=', 'married')]).filtered(lambda x: x.wedding_date and x.wedding_date.strftime('%d-%m') == fields.Date.today().strftime('%d-%m'))
            for emp in wedding_employees:
                dic_emp = [{'email_cc': self.env.user.company_id.wishes_mail_cc,
                            'wedding_message': self.env.user.company_id.wedding_message}]
                ctx = {'records': dic_emp}
                temp_id = self.env.ref('employee_confirmation.email_template_employee_wedding_wishes').id
                self.env['mail.template'].browse(temp_id).with_context(ctx).send_mail(emp.id, force_send=True)


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    birthday_image = fields.Binary('Birthday Image', related="employee_id.birthday_image")
    birthday_filename = fields.Char('Filename', size=64, readonly=True, related="employee_id.birthday_filename")
    wedding_image = fields.Binary('Wedding Image', related="employee_id.wedding_image")
    wedding_filename = fields.Char('Filename', size=64, readonly=True, related="employee_id.wedding_filename")
    address_proof = fields.Boolean('Address Verified', related="employee_id.address_proof")
    date_internship = fields.Date('Internship End Date', related="employee_id.date_internship")

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    head_of_department = fields.Many2one('hr.employee', string='HOD')
