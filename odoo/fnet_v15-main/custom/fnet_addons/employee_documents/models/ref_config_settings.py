from odoo import models, fields, api, _
from num2words import num2words


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    odoo_email = fields.Char('Request to email (odoo)', config_parameter='base.odoo_email')
    citrix_email = fields.Char('Request to  email (citrix)', config_parameter='base.citrix_email')
    account_email = fields.Char('Request to email (accounts)', config_parameter='base.account_email')
