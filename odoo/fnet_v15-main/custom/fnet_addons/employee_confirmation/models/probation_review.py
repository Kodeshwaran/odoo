# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import base64
import logging


_logger = logging.getLogger(__name__)


class ProbationReview(models.Model):
    _name = 'probation.review'
    _rec_name = 'employee_id'
    _description = 'Probation Review Form'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Requested'),
        ('manager_approve', 'Manager Approved'),
        ('hod_approve', 'HOD Approved'),
        ('hr_approve', 'HR Approved'),
        ('md_approve', 'MD Approved'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
        ], default='draft', tracking=True)

    job_designation = fields.Char(compute="_compute_fieldvalues", string="Job Designation", readonly=False)
    employee_id = fields.Many2one('hr.employee', string="Employee Name", required=True)
    date_join = fields.Date(compute="_compute_fieldvalues", string="Date of Joining", readonly=False)
    probation_end_date = fields.Date(compute="_compute_fieldvalues", string="Probation End Date", readonly=False)
    manager_id = fields.Many2one('hr.employee', compute="_compute_fieldvalues", string="Manager",
                                        readonly=False)
    form_date = fields.Date(string="Date", default=datetime.today())
    assessment_detail = fields.One2many('assessment.details', 'probation_id', string="assessment details")
    probation_review_action = fields.Selection([('me', 'Meets Expectations-Successful Completion of Probationary Period'), ('dm', 'Does not meet Expectations'), ('ri', 'Requires Improvement')])
    employee_message = fields.Html(string='Message to Employee')
    probation_extension = fields.Char(string="Probation Extension")
    review_action_hr = fields.Selection([('cs', 'Confirmation letter on successful completion of probationary period to be issued'),
                                                ('pe', 'Confirmation extension letter to be issued'), ('nc', 'No need to issue Confirmation letter')])
    confirmation_date = fields.Date(string="Confirmation Date")
    date_of_relieving = fields.Date(string="Date of Relieving")
    is_ctc_revised = fields.Boolean(string='Is CTC Revised?', default=False)
    new_ctc = fields.Char(string="New CTC")
    hr_comments = fields.Html(string="HR Comments")
    hr_sign = fields.Many2one('res.users', string="Sign")
    hr_sign_date = fields.Datetime(string="Date")
    manager_comments = fields.Text(string="Manager Comments")
    hod_comments = fields.Text(string="HOD Comments")
    manager_sign = fields.Many2one('res.users', string="Sign")
    hod_sign = fields.Many2one('res.users', string="Sign")
    manager_sign_date = fields.Datetime(string="Date")
    hod_sign_date = fields.Datetime(string="Date")
    is_manager = fields.Boolean(string='Is Manager?', compute='check_user')
    is_hod = fields.Boolean(string='Is HOD?', compute='check_user')
    is_hr_approved = fields.Boolean(string='Is Hr Approved?')
    md_comments = fields.Html(string="MD Comments")
    md_sign = fields.Many2one('res.users', string="Sign")
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id')
    md_sign_date = fields.Datetime(string="Date")
    date_of_relieving = fields.Date('Date of Relieving')

    def check_user(self):
        for rec in self:
            if (rec.employee_id.department_id.head_of_department.user_id.id == self.env.user.id) and (rec.manager_id.user_id.id == self.env.user.id):
                rec.is_hod = True
                rec.is_manager = True
            elif rec.employee_id.department_id.head_of_department.user_id.id == self.env.user.id:
                rec.is_hod = True
                rec.is_manager = False
            elif rec.manager_id.user_id.id == self.env.user.id:
                rec.is_manager = True
                rec.is_hod = False
            else:
                rec.is_hod = False
                rec.is_manager = False


    @api.model
    def default_get(self, fields):
        res = super(ProbationReview, self).default_get(fields)
        res['assessment_detail'] = [(0, 0, {'performance_description': 'Technical Skills /Job Knowledge'}),
                                    (0, 0, {'performance_description': 'Work plan implementation'}),
                                    (0, 0, {'performance_description': 'Time Management'}),
                                    (0, 0, {'performance_description': 'Adherence to deadlines'}),
                                    (0, 0, {'performance_description': 'Planning'}),
                                    (0, 0, {'performance_description': 'Attention to Detail'}),
                                    (0, 0, {'performance_description': 'Teamwork'}),
                                    (0, 0, {'performance_description': 'Communication / cooperation'}),
                                    (0, 0, {'performance_description': 'Knowledge Sharing'}),
                                    (0, 0, {'performance_description': 'Presentation / Accuracy of Work'}),
                                    (0, 0, {'performance_description': 'Dependability / Responsibility'}),
                                    (0, 0, {'performance_description': 'Interpersonal Skills'}),
                                    (0, 0, {'performance_description': 'Creativity'}),
                                    (0, 0, {'performance_description': 'Project Management'}),
                                    (0, 0, {'performance_description': 'Customer / Client Focus'}),
                                    (0, 0, {'performance_description': 'General Attitude'}),
                                    (0, 0, {'performance_description': 'Time keeping'}),
                                    ]
        return res

    @api.depends('employee_id')
    def _compute_fieldvalues(self):
        for record in self:
            record.job_designation = record.employee_id.job_title
            record.date_join = record.employee_id.date_join
            record.manager_id = record.employee_id.parent_id
            record.probation_end_date = record.employee_id.date_probation

    def action_request(self):
        for rec in self:
            rec.state = 'request'
            dic_emp = [{'url': '/mail/view?model=%s&res_id=%s' % ('probation.review', rec.id),
                        'email_cc': self.env.user.company_id.probation_hr_mail}]
            ctx = {'records': dic_emp}
            temp_id = self.env.ref('employee_confirmation.email_template_probation_review_alert_manager').id
            self.env['mail.template'].browse(temp_id).with_context(ctx).send_mail(rec.id, force_send=True)

    def action_manager_approve(self):
        for rec in self:
            if not rec.probation_review_action:
                raise UserError(_('Select the correct option for the probation review so that required action can be taken'))
            # if rec.probation_review_action == 'ri' and not rec.manager_comments:
            #     raise UserError(_("Please enter reason for extension of probation period for %s month(s) in the comments box") % (rec.probation_extension))
            # if not rec.manager_comments:
            #     raise UserError("Share your message to the employee in the comments box")
            #Send Mail to HOD for approval
            subject = "%s's Probation Review" % self.employee_id.name
            body = """<p>Dear <strong>%s</strong>,</p>
                      <p>The Probation Review for %s has been approved. </br>
                      Further confirmation needed on approval for the probation period which ended on %s, Kindly confirm as soon as possible.</br></br>
                      Thank You.</br>
                      </p>
                      <div style="padding: 16px 8px 16px 8px;">
                        <a t-att-href= %s
                           style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                            View Probation Review
                        </a>
                      </div>
                      <p>Sincerely,<br/>
                         %s</p>""" % (self.employee_id.department_id.head_of_department.name, self.employee_id.name, self.probation_end_date, self.get_mail_url(), self.employee_id.parent_id.name)
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_from': self.employee_id.parent_id.work_email,
                'email_to': self.employee_id.department_id.head_of_department.work_email,
            }
            self.message_post(body=body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
            rec.write({
                'state': 'manager_approve',
                'manager_sign': self.env.user.id,
                'manager_sign_date': fields.Datetime.now(),
            })

    def action_reject(self):
        md_group = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('mm_master.group_company_managing_director'):
                md_group.append(user.login)
        reject_reason = {
            'name': 'Reason for Rejection',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'probation.review.refusal',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_probation_id': self.id},
        }
        for rec in self:
            if not rec.probation_review_action:
                raise UserError(_('Select the correct option for the probation review so that required action can be taken'))
            if rec.is_manager and rec.is_hod:
                # Send Mail to HR & MD
                subject = "%s's Probation Review Rejected" % self.employee_id.name
                body = """</br>
                          <p>The Probation Review for %s has been rejected. </br>
                          </br>
                          </p>
                          <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View Probation Review
                            </a>
                          </div>
                          <p>Sincerely,<br/>
                             %s</p>""" % (self.employee_id.name, self.get_mail_url(),
                                          self.employee_id.department_id.head_of_department.name)
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.employee_id.department_id.head_of_department.work_email,
                    'email_to': ('%s, %s') % (self.env.user.company_id.payslip_mail,
                                              str(md_group).strip('[]').strip("''"))
                }
                self.message_post(body=body, subject=subject)
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                return reject_reason
            elif rec.is_manager:
                # Send Mail to HOD & HR & MD
                subject = "%s's Probation Review Rejected" % self.employee_id.name
                body = """</br>
                          <p>The Probation Review for %s has been rejected. </br>
                          </br>
                          </p>
                          <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View Probation Review
                            </a>
                          </div>
                          <p>Sincerely,<br/>
                             %s</p>""" % (self.employee_id.name, self.get_mail_url(),
                                          self.employee_id.department_id.head_of_department.name)
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.employee_id.parent_id.work_email,
                    'email_to': ('%s, %s, %s') % (self.employee_id.department_id.head_of_department.work_email, self.env.user.company_id.payslip_mail,
                                              str(md_group).strip('[]').strip("''"))
                }
                self.message_post(body=body, subject=subject)
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                return reject_reason
            elif rec.is_hod:
                # Send Mail to Manager & HR & MD
                subject = "%s's Probation Review Rejected" % self.employee_id.name
                body = """</br>
                          <p>The Probation Review for %s has been rejected. </br>
                          </br>
                          </p>
                          <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View Probation Review
                            </a>
                          </div>
                          <p>Sincerely,<br/>
                             %s</p>""" % (self.employee_id.name, self.get_mail_url(),
                                          self.employee_id.department_id.head_of_department.name)
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.employee_id.department_id.head_of_department.work_email,
                    'email_to': ('%s, %s, %s') % (self.employee_id.parent_id.work_email, self.env.user.company_id.payslip_mail,
                    str(md_group).strip('[]').strip("''"))
                }
                self.message_post(body=body, subject=subject)
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                return reject_reason


    def action_manager_and_hod_approve(self):
        for rec in self:
            if not rec.probation_review_action:
                raise UserError(_('Select the correct option for the probation review so that required action can be taken'))
            if rec.probation_review_action == 'ri':
                if not rec.hod_comments:
                    raise UserError(_("Please enter reason for extension of probation period for %s month(s) in HOD comments box") % (rec.probation_extension))
                # Send Mail to HR & MD
                subject = "%s's Probation Review Rejected" % self.employee_id.name
                body = """</br>
                          <p>The Probation Review for %s has been rejected. </br>
                          </br>
                          </p>
                          <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View Probation Review
                            </a>
                          </div>
                          <p>Sincerely,<br/>
                             %s</p>""" % (self.employee_id.name, self.get_mail_url(),
                                          self.employee_id.department_id.head_of_department.name)
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.employee_id.department_id.head_of_department.work_email,
                    'email_to': ('%s, %s') % (self.env.user.company_id.payslip_mail,
                                              str(md_group).strip('[]').strip("''"))
                }
                self.message_post(body=body, subject=subject)
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                rec.write({
                    'state': 'hod_approve',
                })
            else:
                # Send Mail to HR for Done
                subject = "%s's Probation Review" % self.employee_id.name
                body = """<p>Dear Team <strong>Human Resources</strong>,</p>
                          <p>The Probation Review for %s has been Confirmed on <strong>%s</strong>. </br>
                          Thank You.</br>
                          </p>
                          <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View Probation Review
                            </a>
                          </div>
                          <p>Sincerely,<br/>
                             %s</p>""" % (
                self.employee_id.name, fields.Date.today(), self.get_mail_url(),
                self.employee_id.department_id.head_of_department.name)
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.employee_id.department_id.head_of_department.work_email or rec.employee_id.parent_id.work_email,
                    'email_to': self.env.user.company_id.payslip_mail,
                }
                self.message_post(body=body, subject=subject)
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                rec.write({
                    'state': 'hod_approve',
                    'manager_sign': self.env.user.id,
                    'hod_sign': self.env.user.id,
                    'hod_sign_date': fields.Datetime.now(),
                    'manager_sign_date': fields.Datetime.now(),
                })


    def action_hod_approve(self):
        md_group = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('mm_master.group_company_managing_director'):
                md_group.append(user.login)
        for rec in self:
            if rec.probation_review_action == 'me':
                # Send Mail to HR for Done
                subject = "%s's Probation Review" % self.employee_id.name
                body = """<p>Dear Team <strong>Human Resources</strong>,</p>
                          <p>The Probation Review for %s has been Confirmed on <strong>%s</strong>. </br>
                          Thank You.</br>
                          </p>
                          <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View Probation Review
                            </a>
                          </div>
                          <p>Sincerely,<br/>
                             %s</p>""" % (self.employee_id.name, fields.Date.today(), self.get_mail_url(), self.employee_id.department_id.head_of_department.name)
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.employee_id.department_id.head_of_department.work_email,
                    'email_to': self.env.user.company_id.payslip_mail,
                }
                self.message_post(body=body, subject=subject)
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                rec.write({
                    'state': 'hod_approve',
                    'hod_sign': self.env.user.id,
                    'hod_sign_date': fields.Datetime.now(),
                })
            elif (rec.probation_review_action == 'dm' or 'ri'):
                # Send Mail to Manager, HR & MD
                subject = "%s's Probation Review Rejected" % self.employee_id.name
                body = """</br>
                          <p>The Probation Review for %s has been rejected. </br>
                          </br>
                          </p>
                          <div style="padding: 16px 8px 16px 8px;">
                            <a t-att-href= %s
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                View Probation Review
                            </a>
                          </div>
                          <p>Sincerely,<br/>
                             %s</p>""" % (self.employee_id.name, self.get_mail_url(),
                                          self.employee_id.department_id.head_of_department.name)
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.employee_id.department_id.head_of_department.work_email,
                    'email_to': ('%s, %s, %s') % (
                    self.employee_id.parent_id.work_email, self.env.user.company_id.payslip_mail,
                    str(md_group).strip('[]').strip("''"))
                }
                self.message_post(body=body, subject=subject)
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                rec.write({
                    'state': 'cancel',
                    'hod_sign': self.env.user.id,
                    'hod_sign_date': fields.Datetime.now(),
                })


    def action_hr_approve(self):
        for rec in self:
            if not rec.review_action_hr:
                raise UserError(_('Select the necessary action to be taken according to the review'))
            rec.write({
                'state': 'hr_approve',
                'is_hr_approved': True,
                'hr_sign': self.env.user.id,
                'hr_sign_date': fields.Datetime.now(),
               })

    def action_md_approve(self):
        for rec in self:
            if not rec.md_comments:
                raise UserError("Share your message to the employee in the comments box")
            rec.write({
                'state': 'md_approve',
                'md_sign': self.env.user.id,
                'md_sign_date': fields.Datetime.now(),
                       })

    def action_done(self):
        for rec in self:
            rec.write({'state': 'done'})
            if rec.probation_review_action == 'me' and rec.review_action_hr == 'cs':
                rec.employee_id.confirm_date = rec.confirmation_date
                rec.employee_id.write({'probation_status': 'done'})
                attachments = []
                attachment = self.env.ref('employee_confirmation.action_report_employee_confirmation_letter')._render_qweb_pdf(self.id)
                if attachment:
                    encoded_attachment = base64.b64encode(attachment[0])
                    name = "Employee Confirmation Letter"
                    if encoded_attachment:
                        attach_data = {
                                'name': name,
                                'type': 'binary',
                                'res_name': "Probation Review",
                                'datas':  encoded_attachment,
                                'res_model': 'probation.review',
                                'res_id': self.id,
                            }
                        attachments.append(self.env['ir.attachment'].sudo().create(attach_data))
                dic_emp = [{'email_cc': self.env.user.company_id.probation_hr_mail}]
                ctx = {'records': dic_emp}
                temp_id = self.env.ref('employee_confirmation.email_template_probation_confirmation')
                if attachments:
                    temp_id.attachment_ids = [(4, attachments[0].id)]
                self.env['mail.template'].browse(temp_id.id).with_context(ctx).send_mail(rec.id, force_send=True)
            elif rec.probation_review_action == 'ri' and rec.review_action_hr == 'pe':
                rec.employee_id.date_probation += relativedelta(months=int(rec.probation_extension))
                rec.employee_id.write({'probation_status': 'progress'})
                attachments = []
                attachment = self.env.ref('employee_confirmation.action_report_employee_probation_extension_letter')._render_qweb_pdf(self.id)
                if attachment:
                    encoded_attachment = base64.b64encode(attachment[0])
                    name = "Employee Probation Extension Letter"
                    if encoded_attachment:
                        attach_data = {
                            'name': name,
                            'type': 'binary',
                            'res_name': "Probation Review",
                            'datas': encoded_attachment,
                            'res_model': 'probation.review',
                            'res_id': self.id,
                        }
                        attachments.append(self.env['ir.attachment'].sudo().create(attach_data))
                dic_emp = [{'email_cc': self.env.user.company_id.probation_hr_mail}]
                ctx = {'records': dic_emp}
                temp_id = self.env.ref('employee_confirmation.email_template_probation_extension')
                if attachments:
                    temp_id.attachment_ids = [(4, attachments[0].id)]
                self.env['mail.template'].browse(temp_id.id).with_context(ctx).send_mail(rec.id, force_send=True)



    def _probation_review_reminder(self):
        # filter_date = fields.Date.today() - relativedelta(months=6) - timedelta(days=7)
        employees = self.env['hr.employee'].search([('probation_status', '=', 'progress'), ('date_probation', '=', fields.Date.today() + timedelta(days=7))])
        for emp in employees:
            review_form = self.env['probation.review'].create({
                'employee_id': emp.id,
                'state': 'request',
            })
            emp.write({'probation_status': 'review'})
            dic_emp = [{'url': '/mail/view?model=%s&res_id=%s' % ('probation.review', review_form.id),
                        'email_cc': self.env.user.company_id.probation_hr_mail}]
            ctx = {'records': dic_emp}
            temp_id = self.env.ref('employee_confirmation.email_template_probation_review_alert_manager').id
            self.env['mail.template'].browse(temp_id).with_context(ctx).send_mail(review_form.id, force_send=True)

    def _probation_review_requested_reminder(self):
        previous_month = fields.Date.today() - relativedelta(months=1)
        now = fields.Date.today()
        bu_heads_and_md = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('employee_confirmation.group_company_business_unit_heads'):
                bu_heads_and_md.append(user.login)
            if user.has_group('mm_master.group_company_managing_director'):
                bu_heads_and_md.append(user.login)
        requested_probation = self.env['probation.review'].search([('state', '=', 'request'), ('form_date', '<', now)])
        if requested_probation:
            url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', False) + '/web#model=%s&view_type=form&id=' % self._name
            ctx = {'records': requested_probation,
                   'url': url,
                   'email_from': self.env.user.company_id.payslip_mail,
                   'email_to': str(bu_heads_and_md).strip('[]')}
            temp_id = self.env.ref('employee_confirmation.email_template_probation_review_requested').id
            self.env['mail.template'].browse(temp_id).with_context(ctx).send_mail(self.id, force_send=True)

    def _probation_end_date_alert_remainder(self):
        employees = self.env['hr.employee'].search([('probation_status', '=', 'progress'), ('date_probation', '=', fields.Date.today() + timedelta(days=20))])
        for emp in employees:
            #send mail to Manager & HR
            subject = "Probation End Date Remainder"
            body = """</br>
                      <p> Probation period for following Employee is scheduled to end on:</br>
                      <b>%s:</b> %s 
                      </p>
                      </div>""" % (emp.name, emp.date_probation.strftime('%d-%m-%Y'))
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_to': '%s' % (emp.parent_id.work_email),
                'email_cc': self.env.user.company_id.probation_hr_mail,
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url


class AssessmentDetails(models.Model):
    _name = 'assessment.details'
    _description = 'Assessment Details'

    probation_id = fields.Many2one('probation.review', string="Probation ID")
    performance_description = fields.Text(string="Description", required=True)
    performance_rating = fields.Selection([('ee', 'Exceeding Expectations'), ('mr', 'Meets Requirements'),
                                           ('ftr', 'Further Training required'), ('ns', ' Not Satisfactory')], string="Rating")
    performance_remarks = fields.Text(string="Remarks")