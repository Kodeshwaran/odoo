from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta, datetime, time
from dateutil import relativedelta


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'
    _description = "Resignation Form"

    def _default_employee(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', readonly=True, string="Employee Name", default=_default_employee)
    user_id = fields.Many2one('res.users', related="employee_id.user_id")
    job_title = fields.Char(string="Job Position", related="employee_id.job_title")
    department_id = fields.Many2one(string="Department", related="employee_id.department_id")
    parent_id = fields.Many2one(string='Manager', related="employee_id.parent_id")
    leaving_date = fields.Date('Requested Last Date')
    submitted_date = fields.Date('Submitted Date')
    actual_date = fields.Date('Actual Date', track_visibility='always')
    work_email = fields.Char('Work Email', related="employee_id.work_email")
    date_join = fields.Date(string="Joining Date", related="employee_id.date_join")
    work_mobile = fields.Char('Work Phone', related="employee_id.work_phone")
    leaving_reason = fields.Text('Reason for Leaving')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('submitted', 'To Approve'),
        ('manager_approve', 'Manager Approved'),
        ('hod_approve', 'HOD Approved'),
        ('rejected', 'Rejected'),
        ('done', 'Confirmed'),
        ('withdraw', 'Withdraw Requested'),
        ('manager_cancel_approve', 'Manager Approved (Withdraw)'),
        ('resignation_cancel', 'Resignation Withdrawn'),
    ], default="draft", tracking=True, string="Status")
    is_manager = fields.Boolean(compute="check_user")
    is_employee = fields.Boolean(compute="check_user")
    is_hod = fields.Boolean(compute="check_user")
    is_nd_clicked = fields.Boolean()
    is_ei_clicked = fields.Boolean()
    manager_remarks = fields.Text("Manager Remarks")
    manager_cancel_remarks = fields.Text("Manager Withdraw Remarks")
    exit_int_id = fields.Many2one('exit.interview')
    no_due_id = fields.Many2one('no.due')
    no_due_count = fields.Integer(compute='_compute_no_due_count')
    exit_int_count = fields.Integer(compute='_compute_exit_int_count')
    exit_interview_id = fields.Many2one('exit.interview', string='resignation')
    no_due_id = fields.Many2one('no.due', string='resignation')

    def unlink(self):
        # if self.state != 'draft':
        #     raise ValidationError(_("You cannot delete the following Resignation form"))
        return super(HrResignation, self).unlink()

    def check_user(self):
        for rec in self:
            rec.is_manager = True if rec.parent_id.user_id.id == self.env.uid else False
            rec.is_hod = True if rec.department_id.head_of_department.user_id.id == self.env.uid else False
            rec.is_employee = True if rec.employee_id.user_id.id == self.env.uid else False
            # if (rec.parent_id.user_id.id == self.env.uid) and (rec.department_id.head_of_department.user_id.id == self.env.uid) and (rec.employee_id.user_id.id == self.env.uid):
            #     rec.is_manager = True
            #     rec.is_hod = True
            #     rec.is_employee = True
            # elif rec.parent_id.user_id.id == self.env.uid:
            #     rec.is_manager = True
            #     rec.is_employee = False
            # elif rec.employee_id.user_id.id == self.env.uid:
            #     rec.is_employee = True
            #     rec.is_manager = False
            # else:
            #     rec.is_employee = False
            #     rec.is_manager = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for employee in self:
            employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
            employee.employee_id = employee_rec.id

    def action_manager_refuse(self):
        res_form = {
            'name': 'Refusal',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hr.resignation.refusal',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_resignation_id': self.id},
        }
        return res_form

    def action_hod_refuse(self):
        res_form = {
            'name': 'Refusal',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hr.resignation.refusal',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_resignation_id': self.id},
        }
        return res_form

    def action_submit(self):
        # if not self.parent_id:
        #     self.write({'state': 'submitted',
        #                 'submitted_date': fields.Date.today()})
        #     subject = 'Resignation Request'
        #     body = """<p>Dear Team HR,</p>
        #               <br/>
        #               <p>Kindly accept this letter as my formal resignation from my position as "%s", applied on %s.<br/>
        #               Furthermore, Please let me know how I can be of any help during the transition period. </br>Thank You.</p>
        #               <div style="padding: 16px 8px 16px 8px;">
        #                 <a t-att-href= %s
        #                    style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
        #                     View Resignation Form
        #                 </a>
        #               </div>
        #               <p>Sincerely,<br/>
        #                  %s</p>""" % (
        #     self.employee_id.job_title, self.submitted_date.strftime('%d-%m-%Y'), self.get_mail_url(),
        #     self.employee_id.name)
        #     template_data = {
        #         'subject': subject,
        #         'body_html': body,
        #         'email_from': self.employee_id.work_email,
        #         'email_to': self.env.user.company_id.payslip_mail,
        #     }
        #     self.message_post(body=body, subject=subject)
        #     template_id = self.env['mail.mail'].sudo().create(template_data)
        #     template_id.sudo().send()

        if self.employee_id == self.parent_id or not self.parent_id:
            self.write({'state': 'manager_approve',
                        'submitted_date': fields.Date.today()})
            subject = 'Resignation Request'
            body = """<p>Dear Team HR,</p>
                      <br/>
                      <p>Kindly accept this letter as my formal resignation from my position as "%s", applied on %s.<br/>
                      Furthermore, Please let me know how I can be of any help during the transition period. </br>Thank You.</p>
                      <div style="padding: 16px 8px 16px 8px;">
                        <a t-att-href= %s
                           style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                            View Resignation Form
                        </a>
                      </div>
                      <p>Sincerely,<br/>
                         %s</p>""" % (
            self.employee_id.job_title, self.submitted_date.strftime('%d-%m-%Y'), self.get_mail_url(),
            self.employee_id.name)
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_from': self.employee_id.work_email,
                'email_to': self.env.user.company_id.payslip_mail,
            }
            self.message_post(body=body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

        else:
            self.write({'state': 'submitted',
                        'submitted_date': fields.Date.today()})
            subject = 'Resignation Request'
            manager = self.employee_id.parent_id.work_email
            body = """<p>Dear Mr/Mrs %s,</p>
                              <br/>
                              <p>Kindly accept this letter as my formal resignation from my position as "%s", applied on %s.<br/>
                              Furthermore, Please let me know how I can be of any help during the transition period. Thank You.</p>
                              <div style="padding: 16px 8px 16px 8px;">
                                <a t-att-href= %s
                                   style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                    View Resignation Form
                                </a>
                              </div>
                              <p>Sincerely,<br/>
                                 %s</p>""" % (
            self.employee_id.parent_id.name, self.employee_id.job_title, self.submitted_date.strftime('%d-%m-%Y'),
            self.get_mail_url(), self.employee_id.name)
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.employee_id.work_email,
                'email_to': manager,
            }
            print(template_data, '\n')
            self.message_post(body=message_body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_hod_approve(self):
        self.write({'state': 'hod_approve'})

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url

    def action_approve(self):
        self.write({'state': 'manager_approve'})
        subject = "'%s' - Resignation Request Approved" % self.employee_id.name
        body = """<p>Dear Team,</p>
                  <br/>
                  <p>The resignation request from "%s - %s" on "%s" has been approved. Kindly proceed further.</br>
                     Manager Remarks: %s</br>
                  </p>
                  <div style="padding: 16px 8px 16px 8px;">
                    <a t-att-href= %s
                       style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                        View Resignation Form
                    </a>
                  </div>
                  <p>Sincerely,<br/>
                     %s</p>""" % (
        self.employee_id.name, self.employee_id.job_title, self.leaving_date, self.manager_remarks, self.get_mail_url(),
        self.parent_id.name)
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': self.employee_id.parent_id.work_email,
            'email_to': self.env.user.company_id.payslip_mail,
        }
        self.message_post(body=body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    def action_confirm(self):
        if self.employee_id.user_id.id == self.env.uid:
            raise UserError(_("You cannot Confirm your own resignation form."))
        self.write({'state': 'done'})

        group = self.env.ref('hr_resignation.group_restrict_leave_apply')
        users = self.env['res.users'].search([('id', '=', self.user_id.id)])
        group.sudo().write({'users': [(4, user.id) for user in users]})

        # if self.actual_date:
        #     my_date = self.actual_date
        #     date_from = datetime.combine(my_date, time.min)
        #     date_to = datetime.combine(my_date, time.max)
        #     working_days = self.env['hr.leave']._get_number_of_days(date_from, date_to, self.employee_id.id)['days']
        #     while (working_days != 0):
        #         date_from = date_from + timedelta(days=1)
        #         date_to = date_to + timedelta(days=1)
        #         working_days = self.env['hr.leave']._get_number_of_days(date_from, date_to, self.employee_id.id)['days']
        #         if working_days == 1:
        #             self.actual_date = date_to
        #             break
        #         else:
        #             continue
        subject = 'Resignation Acceptance'
        employee = self.employee_id.work_email
        body = """<p>Dear %s,</p>
                          <br/>
                          <p>Your resignation from your position "%s" has been accepted. As discussed, %s is your last working day.</p>
                          <p>Sincerely,<br/>
                             Human Resources</p>""" % (self.employee_id.name, self.job_title, self.actual_date)
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.company_id.payslip_mail,
            'email_to': employee,
        }
        self.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    def action_cancel_withdraw(self):
        if self.actual_date and self.actual_date < fields.Date.today():
            raise ValidationError('You cannot withdraw your resignation after your last working day.')
        self.write({'state': 'withdraw'})
        subject = 'Resignation Withdrawal Request'
        employee = self.employee_id.work_email
        submitted_date_str = self.submitted_date.strftime('%d-%m-%Y') if self.submitted_date else ''
        body = """<p>Dear Sir/Ma'am,</p>
                      <br/>
                      <p>I would like to withdraw my resignation, which I had applied for on '%s'. I have been reconsidering my decision and wish to continue working. </br>
                      So I kindly request that you please withdraw my resignation request. Thank You.</p>
                      <div style="padding: 16px 8px 16px 8px;">
                        <a t-att-href= %s
                           style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                            View Resignation Withdrawal Request
                        </a>
                      </div>
                      <p>Sincerely,<br/>
                         %s</p>""" % (submitted_date_str, self.get_mail_url(), self.employee_id.name)
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': employee,
            'email_to': '%s, %s' % (self.employee_id.parent_id.work_email, self.env.user.company_id.payslip_mail),
        }

        self.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    @api.model
    def create(self, vals):
        resignation = self.env['hr.resignation'].search(
            [('user_id', '=', self.env.uid), ('state', 'not in', ['cancel', 'rejected', 'resignation_cancel'])])
        if resignation:
            raise ValidationError(
                _('You cannot create a new resignation form until the previous one is under process or completed.'))
        return super(HrResignation, self).create(vals)

    def write(self, vals):
        res = super(HrResignation, self).write(vals)
        if 'actual_date' in vals:
            mail_template = self.env.ref('hr_resignation.actual_date_change_mail_template')
            for record in self:
                mail_template.with_context(docs=self).send_mail(record.id, force_send=True)
        return res

    def action_create_no_due(self):
        now = fields.Date.today()
        # if self.actual_date != now:
        #     raise ValidationError('You cannot create No Due as today is not actual date.')
        # self.write({'is_nd_clicked': True})
        if self.actual_date:
            no_due = self.env['no.due'].create({
                'name': self.employee_id.id,
                'date_of_resignation': self.actual_date,
                'hr_resign_id': self.id,
                'employeeid': self.employee_id.employeeid,
                'select_department': self.employee_id.department_id.id,
                'manager': self.employee_id.parent_id.id,
            })
            get_actual = self.env['hr.resignation'].search([('state', '=', 'done'), ('actual_date', '=', now)], limit=1)
            no_due_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            no_due_url += '/web#id=%s&model=no.due&view_type=form' % (no_due.id)
            subject = 'No Due Created'
            employee = get_actual.employee_id.work_email
            body = """<p>Dear %s,</p>
                      <br/>
                      <p>As today(%s) is your last day of service, we kindly request you to Submit No Due form for further validation.</p>
                        <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View No Due
                            </a>
                        </div>
                      <p>Sincerely,<br/>
                         Human Resources</p>""" % (self.employee_id.name, str(now), no_due_url)
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.env.user.company_id.payslip_mail,
                'email_to': employee,
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
            return no_due

    def action_create_exit_interview(self):
        now = fields.Date.today()
        # if self.actual_date != now:
        #     raise ValidationError('You cannot create Exit Interview as today is not actual date.')
        self.write({'is_ei_clicked': True})
        if self.actual_date:
            exit_interview = self.env['exit.interview'].create({
                'name': self.employee_id.id,
                'date_of_resignation': self.actual_date,
                'hr_resign_id': self.id,
                'employeeid': self.employee_id.employeeid,
                'department': self.employee_id.department_id.id,
                'reporting_manager': self.employee_id.parent_id.id,
            })
            get_actual = self.env['hr.resignation'].search([('state', '=', 'done'), ('actual_date', '=', now)], limit=1)
            exit_interview_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            exit_interview_url += '/web#id=%s&model=exit.interview&view_type=form' % (exit_interview.id)
            subject = 'Exit Interview Created'
            employee = get_actual.employee_id.work_email
            body = """<p>Dear %s,</p>
                      <br/>
                      <p>As today(%s) is your last day of service, we kindly request you to Submit Exit Interview form for further validation.</p>
                        <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View Exit Interview
                            </a>
                        </div>
                      <p>Sincerely,<br/>
                         Human Resources</p>""" % (self.employee_id.name, str(now), exit_interview_url)
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.env.user.company_id.payslip_mail,
                'email_to': employee,
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
            return exit_interview

    def _emp_last_day_mail(self):
        now = fields.Date.today()
        get_actual = self.env['hr.resignation'].search([('state', '=', 'done'), ('actual_date', '=', now)])
        for actual in get_actual:
            if not actual.exit_int_id:
                actual.action_create_exit_interview()
            if not actual.no_due_id:
                actual.action_create_no_due()
            if actual.exit_int_id and actual.no_due_id:
                exit_interview_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                exit_interview_url += '/web#id=%s&model=exit.interview&view_type=form' % (actual.exit_int_id.id)
                no_due_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                no_due_url += '/web#id=%s&model=no.due&view_type=form' % (actual.no_due_id.id)
                subject = 'No Due & Exit Interview'
                employee = actual.employee_id.work_email
                body = """<p>Dear %s,</p>
                          <br/>
                          <p>As part of our relieving process, we kindly request you to complete the following forms:</p><br/><br/>
                          <p><strong>Exit Interview Form:</strong> Your feedback is highly valuable to us and will help us improve our workplace for current and future employees.</p>
                            <div style="padding: 16px 8px 16px 8px;">
                                <a t-att-href= %s
                                   style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                    View No Due
                                </a>
                            </div><br/><br/>
                            <p><strong>No Due Form:</strong> Please ensure all your pending tasks and dues are cleared before your departure.</p>
                            <div style="padding: 16px 8px 16px 8px;">
                                <a t-att-href= %s
                                   style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                    View Exit Interview
                                </a>
                            </div>
                          <p>Best Regards<br/>
                             HR <br/>
                             9566003012</p>""" % (self.employee_id.name, no_due_url, exit_interview_url)
                message_body = body
                template_data = {
                    'subject': subject,
                    'body_html': message_body,
                    'email_from': self.env.user.company_id.payslip_mail,
                    'email_to': employee,
                }
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()




    def action_view_no_due(self):
        no_due_form = self.env['no.due'].search([('hr_resign_id', '=', self.id)])
        return {
            'name': _('No Due'),
            'type': 'ir.actions.act_window',
            'res_model': 'no.due',
            'view_mode': 'form',
            'res_id': no_due_form.id
        }

    @api.depends('no_due_count')
    def _compute_no_due_count(self):
        count_no_due = self.env['no.due'].search_count([('hr_resign_id', '=', self.id)])
        for rec in self:
            rec.no_due_count = count_no_due

    def action_view_exit_int(self):
        exit_int_form = self.env['exit.interview'].search([('hr_resign_id', '=', self.id)])
        return {
            'name': _('Exit Interview'),
            'type': 'ir.actions.act_window',
            'res_model': 'exit.interview',
            'view_mode': 'form',
            'res_id': exit_int_form.id
        }

    def _compute_exit_int_count(self):
        count_exit_int = self.env['exit.interview'].search_count([('hr_resign_id', '=', self.id)])
        for rec in self:
            rec.exit_int_count = count_exit_int

    def action_manager_approve(self):
        self.write({'state': 'manager_cancel_approve'})
        subject = 'Resignation Withdrawal Request - Approval'
        body = """<p>Dear Team HR,</p>
                  <br/>
                  <p>Approval on %s's Resignation Withdrawal Request: </br>
                  Resignation Withdraw Remarks, %s</p>
                  <div style="padding: 16px 8px 16px 8px;">
                    <a t-att-href= %s
                       style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                        View Resignation Withdrawal Request
                    </a>
                  </div>
                  <p>Sincerely,<br/>
                     %s</p>""" % (
            self.employee_id.name, self.manager_cancel_remarks, self.get_mail_url(), self.parent_id.name)
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': self.employee_id.parent_id.work_email,
            'email_to': self.env.user.company_id.payslip_mail,
        }
        self.message_post(body=body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    def action_hr_approve(self):
        if self.actual_date:
            my_date = self.actual_date
            date_from = datetime.combine(my_date, time.min)
            date_to = datetime.combine(my_date, time.max)
            working_days = self.env['hr.leave']._get_number_of_days(date_from, date_to, self.employee_id.id)['days']
            while (working_days != 0):
                date_from = date_from + timedelta(days=1)
                date_to = date_to + timedelta(days=1)
                working_days = self.env['hr.leave']._get_number_of_days(date_from, date_to, self.employee_id.id)['days']
                if working_days == 1:
                    self.actual_date = date_to
                    break
                else:
                    continue
        self.write({'state': 'resignation_cancel'})
        self.no_due_id.write({'state': 'cancel'})
        self.exit_int_id.write({'state': 'cancel'})
        subject = 'Resignation Withdrawal Request Acceptance'
        employee = self.employee_id.work_email
        body = """<p>Dear %s,</p>
                  <br/>
                  <p>Your request for resignation withdrawal has been accepted. Thank You.</p>
                  <p>Sincerely,<br/>
                     Human Resources</p>""" % (self.employee_id.name)
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.company_id.payslip_mail,
            'email_to': employee,
        }
        self.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    def action_hod_approve(self):
        self.write({'state': 'hod_approve'})
        subject = 'Resignation HOD Approval Request'
        body = """<p>Dear %s,</p>
                  <br/>
                  <p>Your request for HOD Approval has been sent to HOD.</p>
                  <p>Sincerely,<br/>
                     Human Resources</p>""" % (self.employee_id.name)
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.company_id.payslip_mail,
            'email_to': self.employee_id.work_email,
        }
        self.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    def action_refuse_confirmation(self):
        subject = 'Resignation Withdrawal Request Refusal'
        employee = self.employee_id.work_email
        body = """<p>Dear %s,</p>
                  <br/>
                  <p>Your request for resignation withdrawal has been refused.</p>
                  <p>Sincerely,<br/>
                     Human Resources</p>""" % (self.employee_id.name)
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.company_id.payslip_mail,
            'email_to': employee,
        }
        self.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        return {
            'name': 'Refusal',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'resignation.confirmation.refusal',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_resignation_withdraw_id': self.id}
        }




class ExitInt(models.Model):
    _inherit = 'exit.interview'

    hr_resign_id = fields.Many2one('hr.resignation')


class NoDue(models.Model):
    _inherit = 'no.due'

    hr_resign_id = fields.Many2one('hr.resignation')
