from odoo import api, fields, models, _
#~ import uuid
from odoo.exceptions import UserError,except_orm

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_id = fields.Many2one('sale.order', 'Sale')
