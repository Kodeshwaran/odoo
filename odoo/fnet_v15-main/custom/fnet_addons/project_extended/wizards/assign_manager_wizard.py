from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AssignManagerWizard(models.TransientModel):
    _name = 'assign.manager.wizard'
    _description = 'Assign Manager'

    project_id = fields.Many2one('project.project', string='Project')
    user_id = fields.Many2one('res.users', 'Project Manager')

    def action_assign(self):
        if not self.user_id:
            raise UserError('Kindly select a user to assign as Project Manager')
        else:
            self.project_id.write({'user_id': self.user_id.id})
            sale_order = self.env['sale.order'].sudo().search([('name', '=', self.project_id.source_document)], limit=1)
            if sale_order:
                mail_template = self.env.ref('project_extended.email_template_project_create_alert_for_project')
                if sale_order.technical_file:
                    mail_template.attachment_ids = [(6, 0, sale_order.technical_file.ids)]
                if sale_order.vendor_attachment:
                    mail_template.attachment_ids = [(4, attachment.id) for attachment in sale_order.vendor_attachment]
                ctx = {'sale_order': sale_order}
                mail_template.with_context(ctx).send_mail(self.project_id.id, force_send=True)
