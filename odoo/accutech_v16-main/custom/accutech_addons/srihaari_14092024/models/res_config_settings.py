from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    duplicate_email_user = fields.Char(String="Merge Notification")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            duplicate_email_user=self.env['ir.config_parameter'].sudo().get_param(
                'srihaari_14092024.duplicate_email_user'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        email = self.duplicate_email_user or False

        param.set_param('srihaari_14092024.duplicate_email_user', email)