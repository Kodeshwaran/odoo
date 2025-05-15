from odoo import models, fields, api, _



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_rims = fields.Boolean('Is RIMS?')
