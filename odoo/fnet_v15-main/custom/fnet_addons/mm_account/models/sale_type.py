from odoo import api, fields, models, _

class SaleType(models.Model):
    _inherit = 'sale.type'

    declaration = fields.Html()