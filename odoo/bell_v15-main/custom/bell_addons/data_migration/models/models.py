# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    old_name = fields.Char(string="Old Name")
    old_state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled')], string='Old Status')
    old_payment_state = fields.Selection([('not_paid', 'Not Paid'), ('paid', 'Paid')], string="Old Payment State")