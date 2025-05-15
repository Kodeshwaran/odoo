# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class Shift(models.Model):
    _name = "hr.shift"
    _description = "HR Shift"

    name = fields.Selection([
        ('General', 'General'),
        ('First', 'First'),
        ('Second', 'Second'),
        ('Third Shift', 'Third Shift'),
        ('Night', 'Night'),
        ('WeekOff', 'WeekOff'),

    ], required=True,)
    start_time = fields.Float("Start", required=True)
    end_time = fields.Float("End", required=True)
    hours = fields.Float("Total Hours", compute='_get_hours')
    is_night_shift = fields.Boolean(string='Night Shift', default=False)
    sequence = fields.Integer(string='Sequence', default=10)
    code = fields.Char("Default Code", required=1)
    allowance_request=fields.Boolean()
    # color = fields.Char("Color")




    # @api.depends('name')
    # def _compute_allowance_request(self):
    #     for record in self:
    #         if record.name:
    #             record.allowance_request = True
    #         else:
    #             record.allowance_request = False


    @api.depends('start_time', 'end_time')
    def _get_hours(self):
        for rec in self:
            hours = 0
            if rec.end_time:
                from_time = timedelta(hours=rec.start_time)
                to_time = timedelta(hours=rec.end_time)
                if rec.end_time < rec.start_time:
                    max = 24.0 - rec.start_time
                    hours = max + rec.end_time
                else:
                    delta = to_time - from_time
                    sec = delta.total_seconds()
                    hours = sec / (60 * 60)
            rec.hours = hours








