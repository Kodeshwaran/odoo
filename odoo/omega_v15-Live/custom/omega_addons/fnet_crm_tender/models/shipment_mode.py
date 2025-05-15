from odoo import api, fields, models, _
# ~ import uuid
from odoo.exceptions import UserError, except_orm


class ShipmentMode(models.Model):
    _name = 'shipment.mode'
    _rec_name = 'name'

    name = fields.Char("Name")
    code = fields.Char("Code")
    active = fields.Boolean("Active", default=True)
