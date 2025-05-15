from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    shift_cc_mail = fields.Char(string="CC Mail", related="company_id.shift_cc_mail", readonly=False)