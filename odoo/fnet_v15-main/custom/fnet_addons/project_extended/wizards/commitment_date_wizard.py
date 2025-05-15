from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CommitmentDateWizard(models.TransientModel):
    _name = 'commitment.date.wizard'
    _description = 'Commitment Date Wizard'

    commitment_date = fields.Datetime("Enter Delivery Date", help="Delivery Date")
    sale_id = fields.Many2one('sale.order', string='Sale Order')

    def action_close(self):
        for rec in self:
            if rec.commitment_date and any(rec.sale_id.order_line.mapped('product_id').mapped('is_project_mail')):
                mail_template = self.env.ref('project_extended.email_template_update_delivery_date')
                mail_template.sudo().send_mail(self.id, force_send=True)
            rec.sale_id.commitment_date = rec.commitment_date

    def action_project_email(self):
        company_id = self.env.user.company_id
        return company_id.project_email if company_id else None


class ReasonWizard(models.TransientModel):
    _name = 'reason.wizard'
    _description = 'Reason Wizard'

    opportunity_id = fields.Many2one('crm.lead')
    reject_reason = fields.Text(string='Reason for Rejection')

    def action_close(self):
        if not self.reject_reason:
            raise ValidationError("Kindly enter the Reject Reason")
        else:
            self.opportunity_id.reason_for_reject = self.reject_reason
            pre_sale_requested = self.env['crm.stage'].sudo().search([('pre_sale_alert', '=', 'True')], limit=1)
            self._cr.execute("""update crm_lead set stage_id=%s where id=%s""" % (pre_sale_requested.id, self.opportunity_id.id))
            subject = "Presale Documents Rejected for %s" % self.opportunity_id.name
            body = """
                  <p></br>
                  The Project Approval for the Opportunity %s has been rejected for the following reason:</br></br>
                  %s</br></br>
                  </p>
                  <p>Thank You,<br/>
                     %s</p>""" % (self.opportunity_id.name, self.reject_reason, self.env.user.name)
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_from': self.env.user.login,
                'email_to': str(self.opportunity_id.sale_type_id.pre_sale_users.mapped('login')).replace('[', '').replace(']', '').replace("'", ''),
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
            self.opportunity_id.project_approved = True

class ScopeDocumentWizard(models.TransientModel):
    _name = 'scope.document.wizard'
    _description = 'Scope Document'

    opportunity_id = fields.Many2one('crm.lead')
    sco_file = fields.Many2many('ir.attachment', string='Scope Document')

    def update_document(self):
        if not self.sco_file:
            raise UserError('Kindly attach the Technical Document')
        else:
            values = {
                'name': 'Scope Document',
                'date': fields.Datetime.now(),
                'document_attachment': [(6, 0, self.sco_file.ids)],
            }
            self.opportunity_id.write({'scope_file_id': [(6, 0, self.sco_file.ids)], 'attachment_tracking_ids': [(0, 0, values)]})









