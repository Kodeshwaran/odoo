from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee'

    previous_organization_designation = fields.Char('Previous Designation')
    url_link = fields.Char('Url Link')
    employee_registration_id = fields.Many2one('employee.registration')
    private_email_id = fields.Char()


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    previous_organization_designation = fields.Char('Previous Designation')
    url_link = fields.Char('Url Link')
    employee_registration_id = fields.Many2one('employee.registration')
    private_email_id = fields.Char()

    def action_open_employee_document(self):
        for rec in self:
            if rec.employee_registration_id:
                action = {
                    'name': _('Documents'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'employee.registration',
                    'context': {'create': False},
                    'view_mode': 'tree,form',
                    'domain': [('id', '=', rec.employee_registration_id.id)],
                }
                return action

    def action_citrix_login(self):
        if not self.job_title:
            raise UserError(_('Please fill the JOB TITLE of the employee'))
        if not self.department_id:
            raise UserError(_('Please fill the Department of the employee'))

        if self.job_title and self.department_id:
            citrix_email = self.env['ir.config_parameter'].sudo().get_param('base.citrix_email')
            if not citrix_email:
                raise UserError(_('Please configure citrix email in employee settings'))
            mail_template = self.env.ref('employee_documents.email_template_request_citrix_login')
            template_values = {
                'email_to': citrix_email,
            }
            mail_template.write(template_values)
            mail_template.send_mail(self.id, force_send=True)

    def action_odoo_login(self):
        if not self.job_title:
            raise UserError(_('Please fill the JOB TITLE of the employee'))
        if not self.department_id:
            raise UserError(_('Please fill the Department of the employee'))

        if self.job_title and self.department_id:
            odoo_email = self.env['ir.config_parameter'].sudo().get_param('base.odoo_email')
            if not odoo_email:
                raise UserError(_('Please configure odoo email in employee settings'))
            mail_template = self.env.ref('employee_documents.email_template_request_odoo_login')
            template_values = {
                'email_to': odoo_email,
            }
            mail_template.write(template_values)

            mail_template.send_mail(self.id, force_send=True)

    def action_welcome_email(self):
        if not self.name:
            raise UserError(_('Please fill the Employee Name'))
        if not self.job_title:
            raise UserError(_('Please fill the employee Destination'))
        if not self.department_id:
            raise UserError(_('Please fill the Department'))
        if not self.certificate:
            raise UserError(_('Please fill the Degree/Certificate'))
        if not self.study_field:
            raise UserError(_('Please fill the field of the Degree'))
        if self.experience_previous_company:
            if not self.previous_organization_designation:
                raise UserError(_('Please fill the previous working designation'))
        if not self.work_email:
            raise UserError(_('Please fill the Employee Work Email'))

        department_id = self.env['hr.department'].search([])
        manager_emails = department_id.mapped('manager_id.work_email')
        print(manager_emails)
        if not manager_emails:
            raise UserError('No email id found to managers email')

        mail_template = self.env.ref('employee_documents.email_template_employee_welcome_email')
        template_values = {
            'email_to': ",".join(manager_emails),
            'email_cc': self.work_email,
        }
        mail_template.write(template_values)
        mail_template.send_mail(self.id, force_send=True)

    def action_accounts_alart(self):
        for rec in self:
            account_email = self.env['ir.config_parameter'].sudo().get_param('base.account_email')
            if not account_email:
                raise UserError(_('Please configure the accounts email in employee settings'))

            mail_template = self.env.ref('employee_documents.email_template_create_accounts_alert')
            template_values = {
                'email_to': account_email,
            }
            mail_template.write(template_values)
            mail_template.send_mail(self.id, force_send=True)
            return True


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    def _compute_recruitment_request_count(self):
        for rec in self:
            rec.recruitment_request_count = self.env['recruitment.applicant'].search_count(['|', ('user_id', '=', rec.user_id.id), ('department_id.head_of_department', '=', rec.user_id.id)])

    recruitment_request_count = fields.Integer(compute="_compute_recruitment_request_count")

    def action_recruitment_request(self):
        res = {
            'name': 'Recruitment Request',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'recruitment.applicant',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        return res


class Users(models.Model):
    _inherit = 'res.users'

    def _compute_recruitment_request_count(self):
        for rec in self:
            rec.recruitment_request_count = self.env['recruitment.applicant'].search_count(
                ['|', ('user_id', '=', rec.id), ('department_id.head_of_department.user_id', '=', rec.id)])

    recruitment_request_count = fields.Integer(compute="_compute_recruitment_request_count")
    can_recruitment_request = fields.Boolean(string="Can Recruitment Request", compute="_compute_can_recruitment_request")

    def _compute_can_recruitment_request(self):
        for rec in self:
            if rec.department_id.manager_id.user_id == self.env.user or rec.department_id.head_of_department.user_id == self.env.user:
                rec.can_recruitment_request = True
            else:
                rec.can_recruitment_request = False

    def view_recruitment_request(self):
        return {
            'name': _('Recruitment Request'),
            'type': 'ir.actions.act_window',
            'res_model':'recruitment.applicant',
            'view_mode': 'tree,form',
            'domain': ['|', ('user_id', '=', self.env.user.id), ('department_id.head_of_department.user_id', '=', self.env.user.id)],
            'context': {'create': 'False', 'delete': False}
        }

    def action_recruitment_request(self):
        res = {
            'name': 'Recruitment Request',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'recruitment.applicant',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        return res

    @property
    def SELF_READABLE_FIELDS(self):
        return super(Users, self).SELF_READABLE_FIELDS + ['recruitment_request_count', 'can_recruitment_request']
