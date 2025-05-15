from odoo import api, fields, models, _


class DeliveryMail(models.TransientModel):
    _name = 'delivery.mail'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    delivery_id = fields.Many2one('stock.picking')
    project_head = fields.Many2one('res.users', string="Project Head", required=True)
    doc_name = fields.Char(related="delivery_id.origin")
    sales_person = fields.Many2one('res.users', string="Sales Person", related="sale_id.user_id")
    sale_id = fields.Many2one('sale.order')

    @api.onchange('doc_name')
    def onchange_sale_id(self):
        find_so = self.env['sale.order'].search([('name', '=', self.doc_name)])
        for rec in self:
            rec.sale_id = find_so


    def generate_email(self):
        if self.sale_id:
            subject = 'Material Delivery'
            project_head = self.project_head.work_email
            sales_person = self.sales_person.work_email
            body = """<p>Dear %s,</p>
                      <br/>
                      <p>The Material has been successfully delivered to the Project Site.</p>
                      <p><strong><u>Details:-</u></strong><br/>
                      <strong>SO No:</strong> %s,<br/>
                      <strong>Customer Name:</strong> %s<br/>
                      <br/>
                      Thank You.</p>
                      <br/>
                      <p>Sincerely,<br/>
                         %s</p>""" % (self.project_head.name, self.sale_id.name, self.sale_id.partner_id.name, self.env.user.name)
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.env.user.email,
                'email_to': project_head,
                'email_cc': sales_person,
            }
            self.message_post(body=message_body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

        else:
            subject = 'Material Delivery'
            project_head = self.project_head.work_email
            body = """<p>Dear %s,</p>
                      <br/>
                      <p>The Material has been successfully delivered to the Project Site.</p>
                      <p><strong><u>Details:-</u></strong><br/>
                      <strong>SO No:</strong> %s,<br/>
                      <strong>Customer Name:</strong> %s<br/>
                      <br/>
                      Thank You.</p>
                      <br/>
                      <p>Sincerely,<br/>
                         %s</p>""" % (self.project_head.name, self.sale_id.name, self.partner_id.name, self.env.uid)
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.env.user.email,
                'email_to': project_head,
            }
            self.message_post(body=message_body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()




