from odoo import models, fields, api, _
from num2words import num2words
from odoo.exceptions import UserError, AccessError
import base64
import uuid
from time import gmtime, strftime
from datetime import datetime, time
from dateutil.relativedelta import relativedelta


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'
    _rec_name = 'partner_name'

    employee_registration_ids = fields.One2many('employee.registration', 'hr_application_id')
    name = fields.Char("Subject / Application Name", required=False,
                       help="Email subject for applications sent via email")
    joining_date = fields.Date('Joining Date')
    street = fields.Char("street")
    street2 = fields.Char("street2")
    zip = fields.Char("Zip")
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state', "State")
    country_id = fields.Many2one('res.country', "Country")
    ctc_amount = fields.Float('CTC Annual')
    ctc_stripend = fields.Float('CTC stripend Month')
    effective_date = fields.Date('Effective Date')
    ctc_amount_in_word = fields.Char(compute='_compute_ctc_in_word')
    website_url = fields.Char('Url')
    report_date = fields.Date(string='Date', default=fields.Date.today())
    employment_type = fields.Selection([('regular', 'Regular'), ('internship', 'Internship'), ('others', 'Others')])
    expected_joining_date = fields.Date('Expected Joining Date')
    docu_url_expire = fields.Date('Expire_date')


    def _find_mail_template(self):
        template_id = False

        if self.employment_type:
            template_id = self.env.ref('employee_documents.email_template_employee_request_document').id
            if not template_id:
                template_id = self.env['ir.model.data']._xmlid_to_res_id('employee_documents.email_template_employee_offer_letter', raise_if_not_found=False)

        # if not template_id:
        #     template_id = self.env['ir.model.data']._xmlid_to_res_id('employee_documents.email_template_edi_sale', raise_if_not_found=False)

        return template_id

    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        if not self.employment_type:
            raise UserError(_('PLease select the Employment Type'))

        employee_register = self.env['employee.registration'].search([('hr_application_id', '=', self.id)]).ids
        if employee_register:
            for rec in employee_register:
                self.env.cr.execute("DELETE FROM employee_registration WHERE id=%s", [rec])

        if self.employment_type == 'regular':
            if not self.salary_proposed:
                raise UserError(_('Please enter the CTC '))
            if not self.expected_joining_date:
                raise UserError('Please fill the expected joining date ')

            # employee_register fields creates

            employee_registration_id = self.env['employee.registration'].create(
                {'name': self.partner_name,
                 'hr_application_id': self.id,
                 'job_id': self.job_id.id,
                 'department_id': self.department_id.id,
                 # 'expected_joining_date': self.expected_joining_date,
                 'employment_type': self.employment_type,
                 'type_id': self.type_id.id,
                 'company_ctc': self.ctc_amount,
                 'joining_date': self.joining_date
                 })

            # access token
            employee_registration_id.sudo().write({'access_token': str(uuid.uuid4())})
            # url link expire
            current_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            date_1 = datetime.strptime(current_date, "%Y-%m-%d %H:%M:%S")
            date_after_15_days = date_1 + relativedelta(days=15)
            expire_date = date_after_15_days.strftime("%Y-%m-%d %H")
            self.write({'docu_url_expire': expire_date})
            employee_registration_id.sudo().write({'document_url_expire': date_after_15_days})
            # url link
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            base_url += '/register_form/%s/%s' % (employee_registration_id.id, employee_registration_id.access_token)
            self.write({'website_url': base_url})
        template_id = self._find_mail_template()
        template = self.env['mail.template'].browse(template_id)
        terms_and_conditions_report = self.env.ref('employee_documents.action_report_employment_terms_conditions')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(terms_and_conditions_report[0])
        ir_values = {
            'name': "Terms & Conditions.pdf",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        terms_and_conditions = self.env['ir.attachment'].create(ir_values)
        template.write({'attachment_ids': [(6, 0, [terms_and_conditions.id])]})
        report_template_id = self.env.ref('employee_documents.action_report_offer_letter')._render_qweb_pdf(self.id)
        data_record1 = base64.b64encode(report_template_id[0])
        ir_values1 = {
            'name': "Offer Letter.pdf",
            'type': 'binary',
            'datas': data_record1,
            'store_fname': data_record1,
            'mimetype': 'application/x-pdf',
        }
        attachment = self.env['ir.attachment'].create(ir_values1)
        template.write({'attachment_ids': [(4, attachment.id)]})
        ctx = {
            'default_register_id': self.id,
            'default_subject': template.subject,
            'default_body_html': template.body_html,
            'default_email_from': self.env.user.login,
            'default_email_to': self.email_from,
            'default_res_model': 'hr.applicant',
            'default_template_id': template.id,
            'default_attachment_ids': template.attachment_ids.ids
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'offer.letter.wizard',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.depends('ctc_amount')
    def _compute_ctc_in_word(self):
        for rec in self:
            amount_text = num2words(rec.ctc_amount, lang='en_IN').title()
            rec.ctc_amount_in_word = amount_text
            print(rec.ctc_amount_in_word)

    def action_employee_document_request(self):

        if not self.employment_type:
            raise UserError(_('PLease select the Employment Type'))

        employee_register = self.env['employee.registration'].search([('hr_application_id', '=', self.id)]).ids
        if employee_register:
            for rec in employee_register:
                self.env.cr.execute("DELETE FROM employee_registration WHERE id=%s", [rec])

        if self.employment_type == 'regular':
            if not self.ctc_amount:
                raise UserError(_('Please enter the CTC '))
            if not self.expected_joining_date:
                raise UserError('Please fill the expected joining date ')

            # employee_register fields creates

            employee_registration_id = self.env['employee.registration'].create(
                {'name': self.partner_name,
                 'hr_application_id': self.id,
                 'job_id': self.job_id.id,
                 'department_id': self.department_id.id,
                 # 'expected_joining_date': self.expected_joining_date,
                 'employment_type': self.employment_type,
                 'type_id': self.type_id.id,
                 'company_ctc': self.ctc_amount,
                 'joining_date': self.joining_date
                 })

            # access token
            employee_registration_id.sudo().write({'access_token': str(uuid.uuid4())})
            # url link expire
            current_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            date_1 = datetime.strptime(current_date, "%Y-%m-%d %H:%M:%S")
            date_after_15_days = date_1 + relativedelta(days=15)
            expire_date = date_after_15_days.strftime("%Y-%m-%d %H")
            self.write({'docu_url_expire': expire_date})
            employee_registration_id.sudo().write({'document_url_expire': date_after_15_days})
            # url link
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            base_url += '/register_form/%s/%s' % (employee_registration_id.id, employee_registration_id.access_token)
            self.write({'website_url': base_url})

            # email template

            report_template_id = self.env.ref(
                'employee_documents.action_report_employment_terms_conditions')._render_qweb_pdf(self.id)
            data_record = base64.b64encode(report_template_id[0])
            ir_values = {
                'name': "Terms & Conditions.pdf",
                'type': 'binary',
                'datas': data_record,
                'store_fname': data_record,
                'mimetype': 'application/x-pdf',
            }
            attachment = self.env['ir.attachment'].create(ir_values)
            if self.employment_type == 'regular':
                mail_template = self.env.ref('employee_documents.email_template_employee_request_document')
                template_values = {
                    'email_to': self.email_from,
                }
                mail_template.write(template_values)
                mail_template.write({'attachment_ids': [(6, 0, [attachment.id])]})
                mail_template.send_mail(self.id, force_send=True)

    def action_internship_letter(self):

        if not self.employment_type:
            raise UserError(_('PLease select the Employment Type'))

        if self.employment_type == 'internship':
            if not self.effective_date:
                raise UserError(_('Please enter the Effective Date '))
            if not self.ctc_stripend:
                raise UserError('Please fill the CTC Stripend ')
            mail_template = self.env.ref('employee_documents.email_template_employee_internship_request_document')
            template_values = {
                'email_to': self.email_from,
            }
            mail_template.write(template_values)
            mail_template.send_mail(self.id, force_send=True)

    def action_open_employee_registered_documents(self):
        action = {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'employee.registration',
            'context': {'create': False},
            'view_mode': 'tree,form',
            'domain': [('hr_application_id', 'in', self.ids)],
        }
        return action

    def action_open_employee_master(self):
        hr_application_id = self.env['employee.registration'].search([('hr_application_id', '=', self.id)])
        action = {
            'name': _('Employee Master'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'context': {'create': False},
            'view_mode': 'tree,form',
            'domain': [('employee_registration_id', '=', hr_application_id.id)],
        }
        return action

    def action_send_offer_letter(self):
        if not self.employment_type:
            raise UserError(_('PLease select the Employment Type'))
        if not self.joining_date:
            raise UserError(_('Please select the Joining Date'))
        if not self.ctc_amount:
            raise UserError(_('Please enter the CTC '))
        if not self.street:
            raise UserError(_('Please Fill th Address'))


            report_template_id = self.env.ref(
                'employee_documents.action_report_regular_employment_letter')._render_qweb_pdf(self.id)
            data_record = base64.b64encode(report_template_id[0])
            ir_values = {
                'name': "Offer Letter.pdf",
                'type': 'binary',
                'datas': data_record,
                'store_fname': data_record,
                'mimetype': 'application/x-pdf',
            }
            attachment = self.env['ir.attachment'].create(ir_values)

            mail_template = self.env.ref('employee_documents.email_template_employee_offer_letter')
            mail_template.write({'attachment_ids': [(6, 0, [attachment.id])]})
            mail_template.send_mail(self.id, force_send=True)

        if self.employment_type == 'internship':
            report_template_id = self.env.ref(
                'employee_documents.action_report_internship_employment_letter')._render_qweb_pdf(self.id)
            data_record = base64.b64encode(report_template_id[0])
            ir_values = {
                'name': "Internship Letter",
                'type': 'binary',
                'datas': data_record,
                'store_fname': data_record,
                'mimetype': 'application/x-pdf',
            }
            attachment = self.env['ir.attachment'].create(ir_values)

            mail_template = self.env.ref('employee_documents.email_template_employee_internship_letter')
            mail_template.write({'attachment_ids': [(6, 0, [attachment.id])]})
            mail_template.send_mail(self.id, force_send=True)
