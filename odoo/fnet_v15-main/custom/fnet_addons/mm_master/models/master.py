# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleType(models.Model):
    _name = "sale.type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sale Type'
    
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    active = fields.Boolean(string="Active", default=True)
    payment_term_id = fields.Many2one('account.payment.term', string="Payment Terms")
    sales_sub_types = fields.One2many('sale.type.line', 'type_id', string="Sub Types")


class SaleTypeLines(models.Model):
    _name = 'sale.type.line'
    _rec_name = 'name'

    type_id = fields.Many2one('sale.type', string="Type ID", invisible=True)
    name = fields.Char(string="Name",required=True)