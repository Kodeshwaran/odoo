from odoo import api, fields, models, _


class LateDeliveryAlert(models.TransientModel):
    _name = 'late.delivery.alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    alert_id = fields.Many2one('sale.order')
    commitment_date = fields.Datetime(related="alert_id.commitment_date")
    new_commitment_date = fields.Datetime(string="Revised Delivery Date")

    def action_late_delivery_alert(self):
        if self.alert_id:
            subject = 'Late Delivery Notification'
            customer = self.alert_id.partner_id.email
            body = """<p>Dear %s,</p>
                      <br/>
                      <p>Unfortunately, We regret to inform you that delivery date against this order %s has been modified to <strong>%s</strong>.</p>
                      Thank You.</p>
                      <br/>
                      <p>Warm Regards,<br/>
                         %s</p>""" % (self.alert_id.partner_id.name, self.alert_id.name, self.new_commitment_date.strftime('%d/%m/%Y'), self.env.user.name)
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.env.user.email,
                'email_to': customer,
            }
            self.message_post(body=message_body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()