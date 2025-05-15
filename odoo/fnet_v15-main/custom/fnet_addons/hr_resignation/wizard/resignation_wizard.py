from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HrEmployeeNew(models.Model):
    _inherit = 'hr.employee'

    resignation_count = fields.Integer(compute="_compute_resignation_count")

    def _compute_resignation_count(self):
        for rec in self:
            count = self.env['hr.resignation'].search_count([('user_id', '=', rec.user_id.id)])
            rec.resignation_count = count

class Users(models.Model):
    _inherit = 'res.users'

    resignation_count = fields.Integer(compute="_compute_resignation_count")

    def _compute_resignation_count(self):
        for rec in self:
            count = self.env['hr.resignation'].search_count(['|', '|', ('user_id', '=', rec.id), ('employee_id.parent_id.user_id', '=', rec.id), ('department_id.head_of_department.user_id', '=', rec.id)])
            rec.resignation_count = count

    @property
    def SELF_READABLE_FIELDS(self):
        return super(Users, self).SELF_READABLE_FIELDS + ['resignation_count']


    def action_resignation_form(self):
        create = {
            'name': 'Resignation Form',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hr.resignation',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        return create

    def action_open_resignation_smt_btn(self):
        return {
            'name': _("Resignation Form"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'hr.resignation',
            'domain': ['|', '|', ('user_id', '=', self.env.uid), ('employee_id.parent_id.user_id', '=', self.env.uid), ('department_id.head_of_department.user_id', '=', self.env.uid)]
        }


class HrResignationRefusal(models.TransientModel):
    _name = 'hr.resignation.refusal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    refuse_reason = fields.Text("Refusal Reason")
    resignation_id = fields.Many2one('hr.resignation')

    def generate_message_post(self):
        subject = 'Notice of Resignation - Refusal/Rejected'
        employee = self.resignation_id.employee_id.work_email
        body = """<p>Dear %s,</p>
                          <br/>
                          <p><p>This is to inform you that we have received your statement titled “Resignation Request”.<br/>
                            We regret to inform you that your request for employment termination cannot be accommodated at this time.</p></br>
                          <p>Sincerely,<br/>
                             Team Manager & Human Resources</p>""" % (self.resignation_id.employee_id.name)
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.company_id.payslip_mail,
            'email_to': employee,
        }
        self.resignation_id.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        if self.resignation_id:
            self.resignation_id.write({'state': 'rejected'})
            self.resignation_id.sudo().message_post(body='%s' % self.refuse_reason, subject='Refusal Reason')


class RefusalConfirmation(models.TransientModel):
    _name = 'resignation.confirmation.refusal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    refusal_confirmation = fields.Text("Refusal Reason")
    resignation_withdraw_id = fields.Many2one('hr.resignation')

    def generate_message_post_refusal(self):
        if self.resignation_withdraw_id:
            self.resignation_withdraw_id.write({'state': 'done'})
            self.resignation_withdraw_id.sudo().message_post(body='%s' % self.refusal_confirmation, subject='Refusal Reason')
