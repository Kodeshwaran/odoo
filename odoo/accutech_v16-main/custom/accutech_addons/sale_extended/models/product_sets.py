from odoo import models, fields, api, _

class ProductSets(models.Model):
    _name = 'product.sets'
    _rec_name = 'number'

    number = fields.Integer('Number')
    description = fields.Text(string='Description', default='TEST', readonly=True)
