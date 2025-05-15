# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_latitude = fields.Float(
        "Check-in Latitude", digits="Location", readonly=True
    )
    check_in_longitude = fields.Float(
        "Check-in Longitude", digits="Location", readonly=True
    )
    check_out_latitude = fields.Float(
        "Check-out Latitude", digits="Location", readonly=True
    )
    check_out_longitude = fields.Float(
        "Check-out Longitude", digits="Location", readonly=True
    )
    check_in_location = fields.Char("Location", compute='_compute_check_in')
    check_out_location = fields.Char("Location", compute='_compute_check_out')
    work_location_id = fields.Many2one('hr.work.location', related='employee_id.work_location_id')

    @api.depends('check_in_latitude', 'check_in_longitude')
    def _compute_check_in(self):
        for rec in self:
            if rec.check_in_latitude and rec.check_in_longitude:
                rec.check_in_location = 'https://maps.google.com/?q=%s,%s' %(rec.check_in_latitude, rec.check_in_longitude)
            else:
                rec.check_in_location = ''

    @api.depends('check_out_latitude', 'check_out_longitude')
    def _compute_check_out(self):
        for rec in self:
            if rec.check_out_latitude and rec.check_out_longitude:
                rec.check_out_location = 'https://maps.google.com/?q=%s,%s' % (rec.check_out_latitude, rec.check_out_longitude)
            else:
                rec.check_out_location = ''