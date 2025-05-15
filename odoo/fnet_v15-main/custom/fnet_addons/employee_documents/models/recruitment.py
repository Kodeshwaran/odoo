from odoo import models, fields, api, _


class RecruitmentApplicant(models.Model):
    _name = 'recruitment.applicant'
    _description = 'Recruitment Applicants'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    @api.model
    def _get_department(self):
        department = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).department_id
        return department

    name = fields.Char('Reference', copy=False, default=lambda self: _('New'), required=True)
    user_id = fields.Many2one('res.users', string='Requested By', tracking=True, default=lambda self: self.env.user, required=True)
    department_id = fields.Many2one('hr.department', default=_get_department)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    date = fields.Date(required=True, states={'draft': [('readonly', False)]}, index=True, copy=False, default=fields.Date.context_today, string="Request Date")
    skills = fields.Char(string="Skills")
    experience = fields.Integer("Minimum Experience(Years)")
    description = fields.Html(string="Job Specification", render_engine='qweb', compute=False, default='',
                              sanitize_style=True)


    job_id = fields.Many2one('hr.job', string="Designation", required=1)
    leval = fields.Selection([
        ('senior', 'Senior'),
        ('middle', 'Middle'),
        ('junior', 'Junior'),
    ], defaults='true')
    qualification = fields.Char(string="Qualification")
    no_vacancy = fields.Integer(string="No of Vacancy", required=True)
    position = fields.Selection([
        ('new_position', 'New Position'),
        ('replacement', 'Replacement'),
    ], defaults='true', required=True)
    employee_name = fields.Many2one('hr.employee','Employee Name')
    # new_position = fields.Boolean(string='New Position')
    # replacement = fields.Boolean(string='Replacement')
    timing = fields.Selection([
        ('one', 'Immediate'),
        ('two', '1-2 Months'),
        ('three', '2-3 Months'),
    ], string='Notice Period')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('cancel', 'Cancel'),
        ('approve01', 'HOD Approved'),
        ('approve02', 'MD Approved'),
        ('approve03', 'HR Approved'),
        ('close', 'Closed'),
    ], default='draft', readonly=True, copy=False, tracking=True)
    is_hod = fields.Boolean(string='Boolean', compute="_compute_hod")
    ref_id = fields.Many2one('recruitment.applicant','Reference')
    location_id = fields.Many2one('hr.work.location','Location')
    file = fields.Binary("Attachment", attachment=False)
    file_name = fields.Char("Image Name")
    budget_amount = fields.Float("Budget")

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s / %s / %s' % (rec.job_id.name, rec.leval, rec.name)))
        return result

    @api.onchange('ref_id')
    def onchange_ref_id(self):
        if self.ref_id:
            self.skills = self.ref_id.skills
            self.experience = self.ref_id.experience
            self.description = self.ref_id.description
            self.leval = self.ref_id.leval
            self.qualification = self.ref_id.qualification
            self.timing = self.ref_id.timing
            self.job_id = self.ref_id.job_id
            self.department_id = self.ref_id.department_id

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('recruitment.applicant') or _('New')
        return super(RecruitmentApplicant, self).create(vals)

    def _compute_hod(self):
        if self.department_id.head_of_department.user_id == self.env.user:
            self.write({'is_hod': True})
        else:
            self.write({'is_hod': False})

    @api.onchange('job_id')
    def _description_onchange(self):
        for applicant in self:
            description = False
            if applicant.job_id:
                description = applicant.job_id.description
            applicant.description = description or ""

            if not applicant.job_id:
                applicant.description = ""

    def action_request(self):
        for rec in self:
            url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
            url += '/web#id=%d&view_type=form&model=%s' % (rec.id, rec._name)
            values = {
                'access_link': url,
            }
            template_id = self.env.ref('employee_documents.request_mail_template').id
            self.env['mail.template'].browse(template_id).with_context(values).send_mail(rec.id, force_send=True)
        self.state = 'request'

    def action_close(self):
        for rec in self:
            rec.state = 'close'

    def action_reject_document(self):
        self.state = 'cancel'

    def action_hod(self):
        for rec in self:
            url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
            url += '/web#id=%d&view_type=form&model=%s' % (rec.id, rec._name)
            values = {
                'access_link': url,
            }
            print(values)
            template_id = self.env.ref('employee_documents.hod_approve_mail_template').id
            self.env['mail.template'].browse(template_id).with_context(values).send_mail(rec.id, force_send=True)
        self.state = 'approve01'

    def action_md(self):
        for rec in self:
            url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
            url += '/web#id=%d&view_type=form&model=%s' % (rec.id, rec._name)
            values = {
                'access_link': url,
            }
            print(values)
            template_id = self.env.ref('employee_documents.md_approve_mail_template').id
            self.env['mail.template'].browse(template_id).with_context(values).send_mail(rec.id, force_send=True)
        self.state = 'approve02'

    def action_draft_document(self):
        self.state = 'draft'

    def action_cancel_document(self):
        self.state = 'cancel'

    def get_email_to_md(self):
        md = ''
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('mm_master.group_company_managing_director'):
                md += user.login
                md += ', '
        return md

    @api.depends('hr.group_hr_user')
    def get_email_to_hr(self):
        hr = ''
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('hr.group_hr_user'):
                hr += user.login
                hr += ', '
        return hr

    def no_vav(self):
        no = False
        for rec in self:
            if rec.no_vacancy:
                no = rec.no_vacancy + self.job_id.no_of_recruitment
        return no

    def action_hr(self):
        if self.job_id:
            self.job_id.write({'no_of_recruitment': self.no_vav()})
        for rec in self:
            url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
            url += '/web#id=%d&view_type=form&model=%s' % (rec.id, rec._name)
            values = {
                'access_link': url,
            }
            print(values)
            template_id = self.env.ref('employee_documents.manager_approve_mail_template').id
            self.env['mail.template'].browse(template_id).with_context(values).send_mail(rec.id, force_send=True)
        self.state = 'approve03'
        # self.write({'bool' : True})

# class HrJob(models.Model):
#     _inherit = 'hr.job'
#
#     employee01_id = fields.Many2one('recruitment.applicant')
#     job_id = fields.Many2one()
#     no_vacancy = fields.Many2one('recruitment.applicant', string="No of Vacancy")
#
#     @api.depends('job_id')
#     def _compute_company(self):
#         for applicant in self:
#             description = False
#             if applicant.job_id:
#                 description = applicant.job_id.description
#             applicant.description = description or ""
#
#             if not applicant.job_id:
#                 applicant.description = ""
