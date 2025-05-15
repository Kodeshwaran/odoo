from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from datetime import datetime
from dateutil import relativedelta
import openerp.addons.decimal_precision as dp
import json

class ExitInterview(models.Model):
    _name = 'exit.interview'

    name = fields.Many2one('hr.employee', string='Name of the Employee')
    settlement_id = fields.Many2one('final.settlement', string="Settlement")
    employeeid = fields.Char(string="Employee ID")
    department = fields.Many2one('hr.department', 'Department')
    date_of_resignation = fields.Date('Date of Resignation')
    date_of_ei = fields.Date('Date Of EI Conducted', default=fields.Date.context_today)
    reporting_manager = fields.Many2one('hr.employee', 'Reporting Manager')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('cancel', 'Rejected')], string="Status", default="draft")

    section1_1 = fields.Boolean('Unemployed and needed a Job ')
    section1_2 = fields.Boolean('Referred by a Friend')
    section1_3 = fields.Boolean('Fringe Benefits')
    section1_4 = fields.Boolean('FUTURENET reputation as a good place to work.')
    section1_5 = fields.Boolean('Career Advancement')
    section1_6 = fields.Boolean('Advertisement')
    section1_7 = fields.Boolean('Salary Advancement')
    section1_8 = fields.Boolean('Others')

    section2_1 = fields.Boolean('Higher Pay')
    section2_2 = fields.Boolean('Benefits')
    section2_3 = fields.Boolean('Better Job Opportunity')
    section2_4 = fields.Boolean('Commute')
    section2_5 = fields.Boolean('Conflict with Other Employees')
    section2_6 = fields.Boolean('Conflict with Managers')
    section2_7 = fields.Boolean('Family and Personal Reasons')
    section2_8 = fields.Boolean('Relocation/Move')
    section2_9 = fields.Boolean('Career Change')
    section2_10 = fields.Boolean('Company Instability')
    section2_11 = fields.Boolean('Work')
    section2_12 = fields.Boolean('Health Issues')
    section2_13 = fields.Boolean('Others')

    section3 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section4 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section5 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section6 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section7 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section8 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section9 = fields.Text()

    section10 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section11 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section12 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section13 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section14 = fields.Text()

    section15 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section16 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section17 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section18 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section19 = fields.Text()

    section20 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section21 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section22 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section23 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section24 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section25 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section26 = fields.Selection([('strongly_disagree', 'Stongly Disagree'),('disagree', 'Disagree'),('neutral', 'Neutral'),('agree','Agree'),('strongly_agree','Strongly Agree')])
    section27 = fields.Text()
    section28 = fields.Text()
    section29 = fields.Text()

    signature_hr_manager = fields.Many2one('res.users', string="Signature of HR Manager", readonly=True)
    employee_signature = fields.Many2one('res.users', string="Employee Signature", readonly=True)
    date1 = fields.Datetime(string="Date", readonly=True)
    date2 = fields.Datetime(string="Date", readonly=True)
    # hr_resign_id = fields.Many2one('hr.resignation')

    def action_submit(self):
        self.write({'state': 'submitted'})
        now = fields.Datetime.now()
        current_uid = self.env.context.get('uid')
        result = self.update(
            {'employee_signature': current_uid,
             'date2': now
             }
        )
        return result

    def action_approve(self):
        self.write({'state': 'approved'})
        now = fields.Datetime.now()
        current_uid = self.env.user
        result = self.update(
            {'date1': now,
             'signature_hr_manager': current_uid}
        )
        return result

    def action_reset(self):
        self.write({'state': 'draft'})

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.employeeid = self.name.employeeid
            self.department = self.name.department_id.id
            self.reporting_manager = self.name.parent_id.id


class NoDue(models.Model):
    _name = 'no.due'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'No Due'

    def _default_employee(self):
        return self.env.user.employee_id

    name = fields.Many2one('hr.employee', string='Employee Name', default=_default_employee)
    settlement_id = fields.Many2one('final.settlement', string="Settlement")
    employeeid = fields.Char(string="Employee ID")
    select_department = fields.Many2one('hr.department', string="Department")
    manager = fields.Many2one('hr.employee', 'Manager')
    date_join = fields.Date("Date of Joining")
    is_finance = fields.Boolean(compute='check_user')
    is_it = fields.Boolean(compute='check_user')
    is_admin = fields.Boolean(compute='check_user')
    is_manager = fields.Boolean(compute='check_user')
    is_hr = fields.Boolean(compute='check_user')
    date_of_resignation = fields.Date('Date of Resignation')
    salary_adv_taken = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Salary or another Advance taken")
    travel_settlement = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="All Travel expense settlements done")
    loan_amount = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Loan Amount clearance (if applicable)")
    income_tax_details = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Income Tax Details or Declaration Documents (If Applicable)")
    pt_deduct = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="PT Amount to be Deducted")
    ad_login_details = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="AD Login Credentials Disabled")
    erp_login_details = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="ERP Login Credentials Disabled")
    email_disable = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Email ID Disabled or Forwarded to the appropriate Mailbox")
    materials_handed = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Laptop and other Materials Handed over")
    kt_done = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="KT has been done")
    related_data = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Company related Data hand over")
    completed_tenure = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Completed his/her tenure as per the locking period if applicable")
    badge_and_card = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Employee ID Badge & Access Card Handed over")
    keys_handed_over = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Cupboard keys handed over")
    mobile_and_sim = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Mobile & SIM Card Handed over")
    insurance_card = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Insurance Card Handed over")
    update_records = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Updation of Employee Personnel records")
    remove_insurance = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Removing from Insurance Register")
    biometric_removal = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Biometric Access Removal")
    sim_deactivation = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="SIM Card Deactivation")
    remove_number_whatsapp = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Remove Number from WhatsApp Group")
    google_sheet = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Updated in google sheet")
    closed_contract = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Closed contract in ERP")

    salary_adv_taken_remarks = fields.Text()
    travel_settlement_remarks = fields.Text()
    loan_amount_remarks = fields.Text()
    income_tax_details_remarks = fields.Text()
    pt_deduct_remarks = fields.Text()
    ad_login_details_remarks = fields.Text()
    erp_login_details_remarks = fields.Text()
    email_disable_remarks = fields.Text()
    materials_handed_remarks = fields.Text()
    kt_done_remarks = fields.Text()
    related_data_remarks = fields.Text()
    completed_tenure_remarks = fields.Text()
    badge_and_card_remarks = fields.Text()
    keys_handed_over_remarks = fields.Text()
    mobile_and_sim_remarks = fields.Text()
    insurance_card_remarks = fields.Text()
    update_records_remarks = fields.Text()
    remove_insurance_remarks = fields.Text()
    biometric_removal_remarks = fields.Text()
    sim_deactivation_remarks = fields.Text()
    remove_number_whatsapp_remarks = fields.Text()
    google_sheet_remarks = fields.Text()
    closed_contract_remarks = fields.Text()

    salary_adv_taken_signature = fields.Many2one('res.users')
    travel_settlement_signature = fields.Many2one('res.users')
    loan_amount_signature = fields.Many2one('res.users')
    income_tax_details_signature = fields.Many2one('res.users')
    pt_deduct_signature = fields.Many2one('res.users')
    ad_login_details_signature = fields.Many2one('res.users')
    erp_login_details_signature = fields.Many2one('res.users')
    email_disable_signature = fields.Many2one('res.users')
    materials_handed_signature = fields.Many2one('res.users')
    kt_done_signature = fields.Many2one('res.users')
    related_data_signature = fields.Many2one('res.users')
    completed_tenure_signature = fields.Many2one('res.users')
    badge_and_card_signature = fields.Many2one('res.users')
    keys_handed_over_signature = fields.Many2one('res.users')
    mobile_and_sim_signature = fields.Many2one('res.users')
    insurance_card_signature = fields.Many2one('res.users')
    update_records_signature = fields.Many2one('res.users')
    remove_insurance_signature = fields.Many2one('res.users')
    biometric_removal_signature = fields.Many2one('res.users')
    sim_deactivation_signature = fields.Many2one('res.users')
    remove_number_whatsapp_signature = fields.Many2one('res.users')
    google_sheet_signature = fields.Many2one('res.users')
    closed_contract_signature = fields.Many2one('res.users')
    is_finance_approved = fields.Boolean('Finance Approval', default=False)
    is_manager_approved = fields.Boolean('Manager Approval', default=False)
    is_it_approved = fields.Boolean('IT Approval', default=False)
    is_admin_approved = fields.Boolean('Admin Approval', default=False)
    is_hr_approved = fields.Boolean('HR Approval', default=False)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('submitted', 'Waiting for Approval'),
        ('validated', 'Validated'),
        ('refused', 'Refused')], string="Status", default="draft")
    is_employee = fields.Boolean()
    # hr_resign_id= fields.Many2one('hr.resignation')

    @api.model
    def _cron_send_mail_on_particular_date(self):

        particular_date = self.date_of_resignation
        current_date = fields.Date.today()

        support_team = self.env.ref('AG_final_settlement.support_team_mail_template')
        admin = self.env.ref('AG_final_settlement.admin_mail_template')

        if particular_date == current_date:
            support_team.send_mail(self.env.user.id, force_send=True)
            admin.send_mail(self.env.user.id, force_send=True)

    def check_user(self):
        for rec in self:
            if rec.employee_id.user_id.id == self.env.uid:
                rec.is_employee = True
            else:
                rec.is_employee = False

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url

    def action_submit(self):
        approvers = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('AG_final_settlement.group_finance'):
                approvers.append(user.login)
            if user.has_group('AG_final_settlement.group_hr'):
                approvers.append(user.login)
            if user.has_group('AG_final_settlement.group_admin'):
                approvers.append(user.login)
            if user.has_group('AG_final_settlement.group_it_department'):
                approvers.append(user.login)
        if self.manager:
            approvers.append(self.manager.work_email)
        mail_content = "Click on the button below to Approve the No Due Form of the Employee %s." \
                        "Do it as soon as possible.<br/><br/>" \
                        "<a href=%s><button>View No Due</button></a>" % (self.name.name, self.get_mail_url())
        main_content = {
            'subject': 'No Due Form Approval',
            'email_from': self.env.user.company_id.email,
            'body_html': mail_content,
            'email_to': str(approvers).strip('[]').replace("'", "")
        }
        template_id = self.env['mail.mail'].sudo().create(main_content)
        template_id.sudo().send()
        self.write({'state': 'submitted'})


    def action_hr_approve(self):
        self.write(
            {
                'update_records_signature': self.env.user.id,
                'remove_insurance_signature': self.env.user.id,
                'biometric_removal_signature': self.env.user.id,
                'sim_deactivation_signature': self.env.user.id,
                'remove_number_whatsapp_signature': self.env.user.id,
                'google_sheet_signature': self.env.user.id,
                'closed_contract_signature': self.env.user.id,
            }
        )

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.employeeid = self.name.employeeid
            self.select_department = self.name.department_id.id
            self.manager = self.name.parent_id.id
            self.date_join = self.name.date_join

    def check_user(self):
        if self.env.user.has_group('AG_final_settlement.group_finance'):
            self.is_finance = True
        else:
            self.is_finance = False
        if self.env.user.has_group('AG_final_settlement.group_it_department'):
            self.is_it = True
        else:
            self.is_it = False
        if self.env.user.has_group('AG_final_settlement.group_hr'):
            self.is_hr = True
        else:
            self.is_hr = False
        if self.env.user.id == self.name.parent_id.user_id.id:
            self.is_manager = True
        else:
            self.is_manager = False
        if self.env.user.has_group('AG_final_settlement.group_admin'):
            self.is_admin = True
        else:
            self.is_admin = False

    def action_validate(self):
        counter = 0
        values = [self.is_finance, self.is_admin, self.is_hr, self.is_it, self.is_manager]
        for val in values:
            if val:
                counter += 1
        if counter == 1:
            if self.is_finance:
                if self.is_finance_approved:
                    raise ValidationError('Finance Approval Already Completed')
                if not self.salary_adv_taken or not self.travel_settlement or not self.loan_amount or not self.income_tax_details or not self.pt_deduct:
                    raise ValidationError(_('Please fill the details...'))
                self.write({
                    'is_finance_approved': True,
                    'salary_adv_taken_signature': self.env.user.id,
                    'travel_settlement_signature': self.env.user.id,
                    'loan_amount_signature': self.env.user.id,
                    'income_tax_details_signature': self.env.user.id,
                    'pt_deduct_signature': self.env.user.id,
                    })
                self.message_post(body='Finance Approval has been done by %s' % (self.env.user.name), subject='Approval')
            elif self.is_hr:
                if self.is_hr_approved:
                    raise ValidationError('HR Approval Already Completed')
                if not self.update_records or not self.remove_insurance or not self.biometric_removal or not self.sim_deactivation or not self.remove_number_whatsapp or not self.google_sheet or not self.closed_contract:
                    raise ValidationError(_('Please fill the details...'))
                self.write({
                    'is_hr_approved': True,
                    'update_records_signature': self.env.user.id,
                    'remove_insurance_signature': self.env.user.id,
                    'biometric_removal_signature': self.env.user.id,
                    'sim_deactivation_signature': self.env.user.id,
                    'remove_number_whatsapp_signature': self.env.user.id,
                    'google_sheet_signature': self.env.user.id,
                    'closed_contract_signature': self.env.user.id,
                })
                self.message_post(body='HR Approval has been done by %s' % (self.env.user.name), subject='Approval')
            elif self.is_admin:
                if self.is_admin_approved:
                    raise ValidationError('Admin Approval Completed')
                if not self.badge_and_card or not self.keys_handed_over or not self.mobile_and_sim or not self.insurance_card:
                    raise ValidationError(_('Please fill the details...'))
                self.write({
                    'is_admin_approved': True,
                    'badge_and_card_signature': self.env.user.id,
                    'keys_handed_over_signature': self.env.user.id,
                    'mobile_and_sim_signature': self.env.user.id,
                    'insurance_card_signature': self.env.user.id,
                })
                self.message_post(body='Admin Approval has been done by %s' % (self.env.user.name), subject='Approval')
            elif self.is_it:
                if self.is_it_approved:
                    raise ValidationError('IT Department Head Approval Completed')
                if not self.ad_login_details or not self.erp_login_details or not self.email_disable or not self.materials_handed:
                    raise ValidationError(_('Please fill the details...'))
                self.write({
                    'is_it_approved': True,
                    'ad_login_details_signature': self.env.user.id,
                    'erp_login_details_signature': self.env.user.id,
                    'email_disable_signature': self.env.user.id,
                    'materials_handed_signature': self.env.user.id,
                    })
                self.message_post(body='IT Department Approval has been done by %s' % (self.env.user.name), subject='Approval')
            elif self.is_manager:
                if self.is_manager_approved:
                    raise ValidationError('Manager Approval Completed')
                if not self.kt_done or not self.related_data or not self.completed_tenure:
                    raise ValidationError(_('Please fill the details...'))
                self.write({
                    'is_manager_approved': True,
                    'kt_done_signature': self.env.user.id,
                    'related_data_signature': self.env.user.id,
                    'completed_tenure_signature': self.env.user.id,
                })
                self.message_post(body='Manager Approval has been done by %s' % (self.env.user.name), subject='Approval')
            if self.is_finance_approved and self.is_hr_approved and self.is_it_approved and self.is_admin_approved and self.is_manager_approved:
                self.write({'state': 'validated'})
                self.name.departure_date = self.date_of_resignation
                self.name.contract_id.date_end = self.date_of_resignation
                self.name.departure_reason_id = self.env.ref('hr.departure_resigned', False)
                # self.name.active = False
        elif counter > 1:
            return {
            'name': 'Validation',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'no.due.validate',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_no_due_id': self.id,
                        },
        }

    def action_refuse(self):
        self.write({'state': 'refused'})

