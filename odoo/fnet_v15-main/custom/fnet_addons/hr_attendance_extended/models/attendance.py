# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    automatic_checkout = fields.Boolean(string="Automatic Check-Out", default=False)

    def _attendance_check_out(self):
        if self.env.user.company_id.auto_check_out:
            filter_time = fields.Datetime.now() - timedelta(hours=self.env.user.company_id.auto_check_out_hours)
            attendances = self.env['hr.attendance'].search([('check_out', '=', False), ('check_in', '<=', filter_time)])
            for att in attendances:
                att.check_out = att.check_in + timedelta(hours=self.env.user.company_id.duration)
                att.check_out_location = att.check_in_location
                att.check_out_latitude = att.check_in_latitude
                att.check_out_longitude = att.check_in_longitude
                att.automatic_checkout = True
