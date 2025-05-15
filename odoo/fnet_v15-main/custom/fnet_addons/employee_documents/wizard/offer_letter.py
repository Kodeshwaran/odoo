from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64


class RequestRegistrationWizard(models.TransientModel):
    _name = "offer.letter.wizard"
    _description = "Offer Letter Wizard"


    body_html = fields.Text('Rich-text Contents', help="Rich-text/HTML message")
    register_id = fields.Many2one('hr.applicant', "Register", copy=False)
    email_from = fields.Char(string="Email From")
    email_to = fields.Text(string="Email To")
    email_cc = fields.Char(string="Email CC")
    subject = fields.Char(string="Subject")
    res_model = fields.Char(string='Model')
    template_id = fields.Many2one('mail.template', string='Template')
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")

    @api.onchange('template_id')
    def onchange_template(self):
        if self.template_id:
            if self.template_id:
                template_id = self.template_id.sudo().generate_email(self.register_id.id, ['subject', 'body_html', 'email_from', 'email_to', 'email_cc', 'attachment_ids'])
                self.subject = template_id['subject']
                self.email_from = self.env.user.login
                self.email_to = template_id['email_to']
                self.email_cc = template_id['email_cc']
                self.body_html = template_id['body_html']
                self.attachment_ids = False
                for att in template_id['attachment_ids']:
                    self.attachment_ids = [(4, att)]
        else:
            self.subject = False
            self.email_from = False
            self.email_to = False
            self.email_cc = False
            self.attachment_ids = False

    def action_offer_letter(self):
        if not self.email_to:
            raise ValidationError(_('Please enter the "Email To" Address'))
        email = {
            'subject': self.subject,
            'body_html': self.body_html,
            'email_from': self.env.user.login,
            'email_to': self.email_to,
            'email_cc': self.email_cc,
            'attachment_ids': self.attachment_ids.ids,
        }
        self.env['mail.mail'].sudo().create(email).send()
