from odoo import models, fields, api, _
from num2words import num2words
from odoo.exceptions import UserError, AccessError, ValidationError
import base64
import uuid
from time import gmtime, strftime
from datetime import datetime, time, timedelta
from datetime import date
from dateutil.relativedelta import relativedelta
import re


class EmployeeRegistration(models.Model):
    _name = "employee.registration"
    _description = "Employee Registration"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'create_date desc'

    report_date = fields.Date(string='Date', default=fields.Date.today())
    joining_date = fields.Date('Actual joining date')
    # web_enter_name = fields.Char('Web Entered Name')
    date = fields.Date(string="Date")
    name = fields.Char(string="Name")
    last_name = fields.Char(string="Last Name")
    job_id = fields.Many2one('hr.job', string="Designation")
    email = fields.Char(string="Email")
    hr_application_id = fields.Many2one('hr.applicant', string="Application ID")
    other_document_one = fields.Char('Other Document1')
    other_document_two = fields.Char('Other Document2')
    document_ids = fields.Many2many('ir.attachment')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
        ('request', 'request')
    ], default='draft', tracking=True)
    blood_group = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-')], string="Blood Group")
    department_id = fields.Many2one('hr.department')
    contact_number = fields.Char('Contact Number')
    emergency_contact_number = fields.Char('Emergency Contact Number')
    fathers_name = fields.Char("Father's Name")
    mothers_name = fields.Char("Mother's Name")
    street = fields.Char("street")
    street2 = fields.Char("street2")
    zip = fields.Integer("Zip")
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state', "State")
    country_id = fields.Many2one('res.country', "Country")
    p_street = fields.Char("street")
    p_street2 = fields.Char("street2")
    p_zip = fields.Integer("Zip")
    p_city = fields.Char("City")
    p_state_id = fields.Many2one('res.country.state', "State")
    p_country_id = fields.Many2one('res.country', "Country")
    tenth_marks = fields.Char('10th Standard Mark')
    twelfth_marks = fields.Char('12th Standard Marks')
    deg_marks = fields.Char('Degree/Dip Marks')
    no_of_year_experience = fields.Float('Year of Experience')
    total_previous_ctc = fields.Integer('Previous Organization CTC')
    company_ctc = fields.Integer('Current CTC')
    ctc_amount_in_word = fields.Char(compute="amount_in_words")
    educational_ids = fields.One2many('employee.education.qualification', 'register_id', string='Educational Qualifications',
        copy=True,
        domain=[('type', '=', 'educational')],
    )
    technical_ids = fields.One2many('employee.education.qualification', 'register_id', string='Educational Qualifications',
        copy=True,
        domain=[('type', '=', 'technical')],
    )
    # technical_ids = fields.One2many('employee.education.qualification', 'register_id', string="Technical Qualifications", domain="[('type', '=', 'technical')]", copy=True)
    # educational_ids = fields.One2many('employee.education.qualification', 'register_id', string="Educational Qualifications", domain="[('type', '=', 'educational')]", copy=True)
    education_qualif_ids = fields.Many2many('employee.education.qualification', 'rel_education_qualif_ids')
    checklist_ids = fields.One2many('documents.checklist', 'onboard_id')
    access_token = fields.Char('Access Token')
    document_url_expire = fields.Datetime('Document url expire')
    # expected_joining_date = fields.Date('Expected Joining Date')
    joining_date_proposed = fields.Date('Joining date Proposed')
    employment_type = fields.Selection([('regular', 'Regular'), ('internship', 'Internship')])
    website_url = fields.Char('URl link')
    type_id = fields.Many2one('hr.recruitment.degree', string='Degree')
    partner_id = fields.Many2one('res.partner', "Contact", copy=False)
    company_id = fields.Many2one('res.company', "Company", compute='_compute_company', store=True, readonly=False,
                                 tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    date_of_birth = fields.Date('Date Of Birth')
    previous_designation = fields.Char()
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], tracking=True)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups="hr.group_hr_user", default='single', tracking=True)
    certificate = fields.Selection([
        ('graduate', 'Graduate'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('doctor', 'Doctor'),
        ('other', 'Other'),
    ], 'Certificate Level', default='other', groups="hr.group_hr_user", tracking=True)
    study_field = fields.Char("Field of Study", groups="hr.group_hr_user", tracking=True)
    # visa_no = fields.Char('Visa No', groups="hr.group_hr_user", tracking=True)
    passport_id = fields.Char('Passport No', groups="hr.group_hr_user", tracking=True)
    pf_number = fields.Char("PF Number")
    uan_number = fields.Char("PF UAN Number")
    aadhar_number = fields.Char("Aadhar Number")
    pan_number = fields.Char("Pan Number")
    esi_number = fields.Char("ESI Number")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    employee_categ = fields.Selection(
        [('employee', 'Employee'), ('intern', 'Internship'), ('consultant', 'Consultant')], string="Employee Type",
        store=True)
    date_probation = fields.Date('Probation / Internship End Date')
    onroll_employment_date = fields.Date('Onroll Employment Date')
    manager_id = fields.Many2one('res.users', string="Manager")

    consolidated_pay = fields.Boolean(string='Consolidated Pay')
    send01 = fields.Boolean(string='Select')
    required_sim = fields.Boolean(string='Required Sim')
    sim = fields.Char(string="Sim Number")
    official_mail = fields.Char(string="Official mail")
    citrix_user = fields.Char(string="Citrix User")
    asset = fields.Char(string="Asset ID")
    citrix_email = fields.Char(compute="user_citrix_email")
    asset_email_boolean = fields.Boolean(string='Assest Email')
    asset_email_retrieve_boolean = fields.Boolean(string='Assest Retrieve')
    mail_server = fields.Char(string="Mail Server")
    citrix_login = fields.Char(string="Citrix Login")
    dl = fields.Char(string="DL")
    erp_login = fields.Char(string="ERP Login")
    assest_required = fields.Char(string="Asset Required")
    file_server_access = fields.Char(string="File server access")
    line_ids = fields.One2many('onboard.doc.line', 'line_id', string='Onboard Document')



    def user_citrix_email(self):
        for rec in self:
            rec.citrix_email = self.env['ir.config_parameter'].sudo().get_param('base.citrix_email')

    @api.model
    def default_get(self, fields_list):
        defaults = super(EmployeeRegistration, self).default_get(fields_list)
        res = [
            (0, 0, {'checklist2': 'induction', }),
            (0, 0, {'checklist2': 'name', }),
            (0, 0, {'checklist2': 'contact', }),
            (0, 0, {'checklist2': 'doj', }),
            (0, 0, {'checklist2': 'edoc', }),
            (0, 0, {'checklist2': 'card', }),
            (0, 0, {'checklist2': 'pan', }),
            (0, 0, {'checklist2': 'sslc', }),
            (0, 0, {'checklist2': 'hslc', }),
            (0, 0, {'checklist2': 'marksheet', }),
            (0, 0, {'checklist2': 'deg', }),
            (0, 0, {'checklist2': 'pro', }),
            (0, 0, {'checklist2': 'letter', }),
            (0, 0, {'checklist2': 'relieving', }),
            (0, 0, {'checklist2': 'payslips', }),
            (0, 0, {'checklist2': 'details', }),
            (0, 0, {'checklist2': 'num', }),
            (0, 0, {'checklist2': 'form', }),
            (0, 0, {'checklist2': 'email', }),
            (0, 0, {'checklist2': 'database', }),
            (0, 0, {'checklist2': 'intro', }),
            (0, 0, {'checklist2': 'buddy', }),
            (0, 0, {'checklist2': 'desktop', }),
            (0, 0, {'checklist2': 'citrix', }),
            (0, 0, {'checklist2': 'appointment', }),
            (0, 0, {'checklist2': 'id', }),
            (0, 0, {'checklist2': 'insurance', }),
            (0, 0, {'checklist2': 'salary', }),
            (0, 0, {'checklist2': 'updateacc', }),
            (0, 0, {'checklist2': 'no', }),
            (0, 0, {'checklist2': 'location', }),
            (0, 0, {'checklist2': 'bank', }),
            (0, 0, {'checklist2': 'nominee', }),
            (0, 0, {'checklist2': 'pf', }),
            (0, 0, {'checklist2': 'passport_photo', }),
        ]
        defaults['checklist_ids'] = res
        return defaults

    @api.depends('job_id', 'department_id')
    def _compute_company(self):
        for applicant in self:
            company_id = False
            if applicant.department_id:
                company_id = applicant.department_id.company_id.id
            if not company_id and applicant.job_id:
                company_id = applicant.job_id.company_id.id
            applicant.company_id = company_id or self.env.company.id

    @api.onchange('name', 'fathers_name', 'mothers_name')
    def caps_name(self):
        self.name = (self.name).title() if self.name else ''
        #    self.web_enter_name = (self.web_enter_name).title() if self.web_enter_name else ''
        self.fathers_name = (self.fathers_name).title() if self.fathers_name else ''
        self.mothers_name = (self.mothers_name).title() if self.mothers_name else ''

    @api.model
    def create(self, vals):
        pat = "^[a-zA-Z0-9-_.]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
        if vals.get('email'):
            if not re.match(pat, vals['email']):
                raise ValidationError('Incorrect Email Id')
            if vals['email'].split('@')[0].count('.') > 1:
                raise ValidationError('Incorrect Email Id')
        return super(EmployeeRegistration, self).create(vals)

    def write(self, vals):
        pat = "^[a-zA-Z0-9-_.]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
        pat_alpha = "^[A-Za-z ]*$"
        if 'name' in vals and vals['name'] != False and not re.match(pat_alpha, vals['name']):
            raise ValidationError('Invalid Name')
        elif 'fathers_name' in vals and vals['fathers_name'] != False and not re.match(pat_alpha, vals['fathers_name']):
            raise ValidationError("Invalid Father's name")
        elif 'mothers_name' in vals and vals['mothers_name'] != False and not re.match(pat_alpha, vals['mothers_name']):
            raise ValidationError("Invalid Mother's name")
        if vals.get('email'):
            email = vals.get('email')
            if not re.match(pat, email):
                raise ValidationError('Incorrect Email Id')
            if email.split('@')[0].count('.') > 1:
                raise ValidationError('Incorrect Email Id')
        return super(EmployeeRegistration, self).write(vals)

    def amount_in_words(self):
        for rec in self:
            rec.ctc_amount_in_word = str(self.env.user.company_id.currency_id.amount_to_text(self.company_ctc))

    def action_draft_document(self):
        self.state = 'draft'

    def action_approve_document(self):

        if not self.name:
            raise UserError(_('You must define a Contact Name for this self.'))
        if not self.joining_date:
            raise UserError(_('Please fill the joining date'))
        employee_data = {
            'name': self.name,
            'job_id': self.job_id.id,
            'job_title': self.job_id.name,
            'department_id': self.department_id.id or False,
            'work_phone': self.department_id.company_id.phone,
            'private_email_id': self.email,
            'country_id': self.p_country_id.id or False,
            'marital': self.marital,
            'emergency_contact': self.contact_number,
            'phone': self.contact_number,
            'emergency_phone': self.emergency_contact_number,
            'experience_previous_company': self.no_of_year_experience,
            'date_join': self.joining_date,
            'employee_registration_id': self.id,
            'birthday': self.date_of_birth or False,
            'previous_organization_designation': self.previous_designation or '',
            'gender': self.gender or '',
            'certificate': self.certificate or '',
            'study_field': self.study_field or '',
            # 'visa_no': self.visa_no or '',
            'passport_id': self.passport_id or '',
            'pf_number': self.pf_number or '',
            'uan_number': self.uan_number or '',
            'aadhar_number': self.aadhar_number or '',
            'pan_number': self.pan_number or '',
            'esi_number': self.esi_number or '',
            'mode_of_pay': 'bank' or '',
            'lang': 'en_IN',
            'city': 'Chennai',
            'work_email': self.email,
            'mobile_phone': self.contact_number,
        }
        employee_id = self.env['hr.employee'].create(employee_data)
        employee_id.write({'employeeid': self.env['ir.sequence'].next_by_code('employee.id') or _('New')})
        self.employee_id = employee_id.id
        self.state = 'approved'
        # return {
        #     'name': _('Employee'),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'hr.employee',
        #     'context': {'create': False},
        #     'view_mode': 'tree,form',
        #     'domain': [('id', '=', employee_id.id)],
        # }
        # send mail to Manager
        if self.department_id:
            if self.department_id.manager_id:
                subject = "New Employee Onboarding Approved - %s" % self.name
                body = """</br>
                          <p>Dear %s,</br>
                          </br>
                          Kindly find the below Joining details of <b>%s</b> - Designation from <b>%s</b>:
                          <table style="width=600px; margin:5px; border: 1px solid black;">
                                <tr style="border: 1px solid black;">
                                    <td style="border: 1px solid black;"><b>Date of Joining:</b></td>
                                    <td style="border: 1px solid black;"></b>%s</td></br>
                                </tr>
                                <tr style="border: 1px solid black;">
                                    <td style="border: 1px solid black;"><b>Probation / Internship End Date:</b></td>
                                    <td style="border: 1px solid black;">%s</td></br>
                                </tr>
                                <tr style="border: 1px solid black;">
                                    <td style="border: 1px solid black;"><b>Onroll Employment Date:</b></td>
                                    <td style="border: 1px solid black;">%s</td></br>
                                </tr>
                            </table>
                          </p>
                          <p>Sincerely,<br/>
                             HR</p>""" % (
                    self.department_id.manager_id.name, self.name, self.department_id.name,
                    self.joining_date.strftime('%d-%m-%Y') if self.joining_date else '',
                    self.date_probation.strftime('%d-%m-%Y') if self.date_probation else '', self.onroll_employment_date.strftime('%d-%m-%Y') if self.onroll_employment_date else '')
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    # 'email_from': self.env.user.company_id.payslip_mail,
                    'email_to': ('%s') % (self.department_id.manager_id.work_email)
                }
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
            else:
                raise ValidationError('Please map manager field for respective department given.')
        else:
            raise ValidationError('Department field is mandatory.')
        # template = self.env.ref('employee_documents.manager_mail_template')
        # print(template)
        # for rec in self:
        #     template.send_mail(rec.id, force_send=True)

    def action_cancel_document(self):
        self.state = 'cancel'

    # def action_request(self):
    #     action = self.env.ref('employee_documents.action_request_registration')
    #     return action

    # def _find_mail_template(self):
    #     template_id = False
    #     if not template_id:
    #         template_id = self.env['ir.model.data']._xmlid_to_res_id('employee_documents.onboarding_mail_template',
    #                                                                  raise_if_not_found=False)
    #
    #     return template_id

    def action_asset_request(self):
        template = self.env.ref('employee_documents.asset_request_mail_template')

        for rec in self:
            template.send_mail(rec.id, force_send=True)
        rec.state = 'approved'
        rec.asset_email_boolean = True

    def action_asset_request_return(self):
        return

    def action_asset_retrieve(self):
        template = self.env.ref('employee_documents.asset_retrieve_mail_template')
        for rec in self:
            template.send_mail(rec.id, force_send=True)
            rec.asset_email_retrieve_boolean = True

    def offer_letter_extra_mail_template(self):
        template = self.env.ref('employee_documents.offer_letter_extra_mail_template')
        for rec in self:
            template.send_mail(rec.id, force_send=True)
            rec.asset_email_retrieve_boolean = True


        # self.ensure_one()action_asset_request
        # template_id = self._find_mail_template()
        # lang = self.env.context.get('lang')
        # template = self.env['mail.template'].browse(template_id)
        # if template.lang:
        #     lang = template._render_lang(self.ids)[self.id]
        #
        # ctx = {
        #     'default_model': 'employee.registration',
        #     'default_res_id': self.ids[0],
        #     'default_use_template': bool(template_id),
        #     'default_template_id': template_id,
        #     'force_email': True,
        #     'custom_layout': "mail.mail_notification_paynow",
        #     # 'model_description': self.with_context(lang=lang).type_name,
        # }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     'res_model': 'mail.compose.message',
        #     'views': [(False, 'form')],
        #     'view_id': False,
        #     'target': 'new',
        #     'context': ctx,
        # }

    def action_open_employee_recruitment(self):
        action = {
            'name': _('Recruitment'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'context': {'create': False},
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.hr_application_id.id)],
        }
        return action

    def action_open_employee(self):
        action = {
            'name': _('Employee'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'context': {'create': False},
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.employee_id.id)],
        }
        return action

    @api.onchange('joining_date')
    def _onchange_dates(self):
        for rec in self:
            if rec.joining_date:
                rec.date_probation = datetime.combine(rec.joining_date, datetime.min.time()) + relativedelta(months=6)
                rec.onroll_employment_date = rec.date_probation + timedelta(days=1)

    def action_create_new_employment(self):
        for applicant in self:
            if not applicant.name:
                raise UserError(_('You must define a Contact Name for this applicant.'))
            if not applicant.joining_date:
                raise UserError(_('Please fill the joining date'))
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.display_name
            else:
                if not applicant.name:
                    raise UserError(_('You must define a Contact Name for this applicant.'))
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'type': 'private',
                    'name': applicant.name,
                    'email': applicant.email,
                })
                applicant.partner_id = new_partner_id
                address_id = new_partner_id.address_get(['contact'])['contact']
            if applicant.name:
                employee_data = {
                    'default_name': applicant.name,
                    'default_last_name': applicant.last_name,
                    'default_job_id': applicant.job_id.id,
                    'default_job_title': applicant.job_id.name,
                    'default_employee_categ': applicant.employee_categ,
                    'default_date_probation': applicant.date_probation,
                    'default_department_id': applicant.department_id.id,
                    'default_parent_id': applicant.department_id.manager_id.id,
                    # 'default_address_home_id': address_id,
                    'default_department_id': applicant.department_id.id or False,
                    'default_work_phone': applicant.department_id.company_id.phone,
                    'form_view_initial_mode': 'edit',
                    'default_private_email_id': applicant.email,
                    'default_country_id': applicant.p_country_id.id or False,
                    'default_marital': applicant.marital,
                    'default_emergency_contact': applicant.contact_number,
                    'default_phone': applicant.contact_number,
                    'default_emergency_phone': applicant.emergency_contact_number,
                    'default_experience_previous_company': applicant.no_of_year_experience,
                    # 'default_date_join': applicant.joining_date,
                    'default_employee_registration_id': applicant.id,
                    'default_parent_name': applicant.fathers_name or applicant.mothers_name or '',
                    'default_birthday': applicant.date_of_birth or False,
                    'default_previous_organization_designation': applicant.previous_designation or '',
                    'default_gender': applicant.gender or '',
                    'default_certificate': applicant.certificate or '',
                    'default_study_field': applicant.study_field or '',
                    # 'default_visa_no': applicant.visa_no or '',
                    'default_passport_id': applicant.passport_id or '',
                    'default_pf_number': applicant.pf_number or '',
                    'default_uan_number': applicant.uan_number or '',
                    'default_aadhar_number': applicant.aadhar_number or '',
                    'default_pan_number': applicant.pan_number or '',
                    'default_esi_number': applicant.esi_number or '',
                    'default_mode_of_pay': 'bank' or '',
                    'default_lang': 'en_IN',
                    'default_city': 'Chennai',
                    'default_work_email': applicant.email,
                    'default_mobile_phone': applicant.contact_number,
                }

            dict_act_window = self.env['ir.actions.act_window']._for_xml_id('hr.open_view_employee_list')
            dict_act_window['context'] = employee_data
            # send mail to Manager
            if self.department_id.manager_id:
                subject = "New Employee Onboarding - %s" % self.name
                body = """</br>
                          <p>Dear %s,</br>
                          </br>
                          Please find below the details regarding %s's start date, probation / internship end date, and onroll employment date: </br>
                          </br>
                          <b>Date of Joining:</b> %s</br>
                          <b>Probation / Internship End Date:</b> %s</br>
                          <b>Onroll Employment Date:</b> %s</br>
                          </p>
                          <p>Sincerely,<br/>
                             HR</p>""" % (
                    self.department_id.manager_id.name, self.name, self.joining_date.strftime('%d-%m-%Y'),
                    self.date_probation.strftime('%d-%m-%Y'), self.onroll_employment_date.strftime('%d-%m-%Y'))
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.env.user.company_id.payslip_mail,
                    'email_to': ('%s') % (self.department_id.manager_id.work_email)
                }
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
            return dict_act_window

    def print_offer_letter(self):
        if not self.joining_date:
            raise UserError(_('Please select the Joining Date'))
        if not self.company_ctc:
            raise UserError(_('Please enter the CTC '))
        if not self.street:
            raise UserError(_('Please Fill th Address'))
        # if self.employment_type == 'regular':
        amount_text = num2words(self.company_ctc, lang='en_IN').title()
        self.ctc_amount_in_word = amount_text
        print(self.ctc_amount_in_word)

        report_template_id = self.env.ref(
            'employee_documents.action_report_regular_employment_letter').report_action(self.id)
        return report_template_id

    # def _find_mail_template(self):
    #     template_id = False
    #
    #     if self.state == 'approved':
    #         template_id = self.env.ref('employee_documents.offer_letter_mail_template').id
    #         print(template_id, 'fggfgffffdferfddrfg')
    #         if not template_id:
    #             template_id = self.env['ir.model.data']._xmlid_to_res_id('employee_documents.offer_letter_mail_template', raise_if_not_found=False)
    #         print(template_id, 'fggfgffffdf')
    #
    #     # if not template_id:
    #     #     template_id = self.env['ir.model.data']._xmlid_to_res_id('employee_documents.email_template_edi_sale', raise_if_not_found=False)
    #
    #     return template_id
    #
    # def action_quotation_send(self):
    #     ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
    #     self.ensure_one()
    #     template_id = self._find_mail_template()
    #     lang = self.env.context.get('lang')
    #     template = self.env['mail.template'].browse(template_id)
    #     if template.lang:
    #         lang = template._render_lang(self.ids)[self.id]
    #     ctx = {
    #         'default_model': 'hr.applicant',
    #         'default_res_id': self.ids[0],
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         'default_composition_mode': 'comment',
    #         'mark_so_as_sent': True,
    #         'custom_layout': "mail.mail_notification_paynow",
    #         'proforma': self.env.context.get('proforma', False),
    #         'force_email': True,
    #         'model_description': self.with_context(lang=lang),
    #     }
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(False, 'form')],
    #         'view_id': False,
    #         'target': 'new',
    #         'context': ctx,
    #     }


class EducationQualification(models.Model):
    _name = 'employee.education.qualification'

    register_id = fields.Many2one('employee.registration', string="Register")
    course_type = fields.Selection(
        [('ug', 'UG'), ('pg', 'PG'), ('technical', 'Technical Course'), ('other_course', 'Other Course')])
    type = fields.Selection([('educational', 'Educational'), ('technical', 'Technical'), ('other', 'Others')], string="Type", default='other')
    name_of_the_institute = fields.Char('Institution Name')
    dept_name = fields.Char('Department')
    marks = fields.Char('CGPA / Marks')
    passing_year = fields.Integer('Year of Passing')
    course_details = fields.Text("Course Details")
    global_certification = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Global Certification")
    certification_no = fields.Char("Certification Number")
    others = fields.Text("Description")


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    file_name = fields.Char('Document Name')


class documentschecklist(models.Model):
    _name = 'documents.checklist'

    onboard_id = fields.Many2one('employee.registration')

    checklist2 = fields.Selection([
        ('induction', 'HR Induction & New Joining Application Form'),
        ('name', 'Employee Name & ID'),
        ('contact', 'Contact No.'),
        ('doj', 'DOJ'),
        ('edoc', 'EDOC'),
        ('card', 'Aadhar Card'),
        ('pan', 'Pan Card'),
        ('sslc', 'SSLC/Diploma'),
        ('hslc', 'HSLC'),
        ('marksheet', 'UG & PG Marksheet'),
        ('deg', 'Deg. Certificate '),
        ('pro', 'Prov. Certificate'),
        ('letter', 'Offer Letter'),
        ('relieving', 'Relieving Letter'),
        ('payslips', 'Payslips (3M) & Bank Statements'),
        ('details', 'Bank Acc. Details'),
        ('num', 'ESI Number'),
        ('form', ' IF not PF then Form 11 & request letter'),
        ('email', 'Email id Creation'),
        ('database', 'Database Update'),
        ('intro', 'Introduction'),
        ('buddy', 'Buddy Connect'),
        ('desktop', 'Desktop/laptop'),
        ('citrix', 'Citrix/File folder access'),
        ('appointment', 'Appointment Letter'),
        ('id', 'ID card'),
        ('insurance', 'Employee Insurance - GPA & GMC'),
        ('salary', 'Salary Acc. Creation'),
        ('updateacc', 'Update Acc.Details to Accounts Team'),
        ('no', 'Employee Contact Number'),
        ('location', 'Location details'),
        ('bank', 'Bank Acc. Details'),
        ('nominee', 'Nominee details'),
        ('pf', 'PF Number'),
        ('passport_photo', 'Passport size photo')], default='card', size=36)

    verify = fields.Boolean(string="Verified")


class RequestRegistrationWizard(models.TransientModel):
    _name = "request.registration.wizard"
    _description = "Request Registration Wizard"

    @api.model
    def default_get(self, fields):
        res = super(RequestRegistrationWizard, self).default_get(fields)
        res['date_cancel'] = datetime.date.today()
        return res

    mail_id = fields.Many2one('employee.registration', string="Mail",
                              domain=[('state', '=' 'draft'), ('priority', 'in', ('0', '1', False))])
    reason = fields.Text(string="Reason")
    date_cancel = fields.Date(string="Cancellation Date")

    def action_cancel(self):
        self.state = 'cancel'


class OnboardDocLine(models.Model):
    _name = 'onboard.doc.line'

    line_id = fields.Many2one('employee.registration', string='Onboard Document', required=True, ondelete='cascade')
    document_name = fields.Char(string='Document Name')
    file = fields.Binary("Document", attachment=False)
    file_name = fields.Char("Image Name")