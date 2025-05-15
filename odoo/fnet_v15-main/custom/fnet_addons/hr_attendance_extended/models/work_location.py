# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta


class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Hours')
    public_holiday_ids = fields.Many2many('resource.calendar.leaves', string='Public Holidays')
