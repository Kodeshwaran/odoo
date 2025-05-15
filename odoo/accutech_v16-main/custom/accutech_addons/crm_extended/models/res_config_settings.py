from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    weighted_amount_perc = fields.Float(string='Set Weighted Amount Percentage')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            weighted_amount_perc=self.env['ir.config_parameter'].sudo().get_param(
                'crm_extended.weighted_amount_perc'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        weighted_perc = self.weighted_amount_perc or False

        param.set_param('crm_extended.weighted_amount_perc', weighted_perc)
