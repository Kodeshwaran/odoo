# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_check_out = fields.Boolean(string='Automatic Check Out for Attendance')
    auto_check_out_hours = fields.Float(string="Automatic Check Out After(Hours)")
    duration = fields.Float(string='Duration')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_check_out = fields.Boolean(string='Automatic Check Out for Attendance' , related="company_id.auto_check_out", readonly=False)
    auto_check_out_hours = fields.Float(string="Automatic Check Out After(Hours)", related="company_id.auto_check_out_hours", readonly=False)
    duration = fields.Float(string='Duration', related="company_id.duration", readonly=False)
