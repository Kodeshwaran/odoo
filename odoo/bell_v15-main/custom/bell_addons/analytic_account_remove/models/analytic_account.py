from odoo import api, fields, models, _


class AnalyticAccountInherit(models.Model):
    _inherit = 'account.invoice'
    _inherit = 'account.move'
    _inherit = 'account.payment'






