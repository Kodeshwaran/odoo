# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class Product(models.Model):
    _inherit = 'product.product'

    product_takeover_type = fields.Selection([('tos', 'TOS'), ('tor', 'TOR')], string="Takeover Type")