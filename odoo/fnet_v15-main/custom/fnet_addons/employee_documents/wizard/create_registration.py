from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64


class RequestRegistrationWizard(models.TransientModel):
    _name = "create.registration.wizard"
    _description = "Create Registration Wizard"


    body = fields.Html('Contents', render_engine='qweb', compute=False, default='', sanitize_style=True)
    register_id = fields.Many2one('employee.registration', "Register", copy=False)
    name = fields.Char(string="Name")
    email = fields.Char(string="email")
    subject = fields.Char(string="Subject", default='Offer Letter')


    def set_boolean_field(self):
        if self.register_id:
            self.register_id.write({'send01' : True})


    def action_request_registration(self):
        self.set_boolean_field()
        record_ids = self.env.context.get('active_ids', [])
        rec = self.env['employee.registration'].search([('id', 'in', record_ids)], limit=1)
        report_template_id = self.env.ref('employee_documents.action_report_regular_employment_letter')._render_qweb_pdf(
            rec.id)
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Appointment form.pdf",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        attachment = self.env['ir.attachment'].create(ir_values)
        mail_template = self.env.ref('employee_documents.onboarding_mail_template')
        if not self.email:
            raise ValidationError(_('Please enter the "Email To" Address'))
        email = {
            'email_to': self.email or '',
        }
        mail_template.write(email)
        mail_template.write({'attachment_ids': [(6, 0, [attachment.id])]})
        mail_template.send_mail(rec.id, force_send=True)
        self.set_boolean_field()

    # attachment.unlink()
    # @api.onchange('name')
    # def _name_onboarding_mail_template(self):
    #     selected_template = self.env.ref('employee_documents.onboarding_mail_template')
    #     if selected_template:
    #         email_body = selected_template.body_html
    #         self.body = email_body


