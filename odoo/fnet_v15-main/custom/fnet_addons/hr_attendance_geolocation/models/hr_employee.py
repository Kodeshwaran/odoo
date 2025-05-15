# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from geopy.distance import great_circle as GC


class WorkLocation(models.Model):
    _inherit = 'hr.work.location'

    location_latitude = fields.Float("Location Latitude", digits=(16, 13))
    location_longitude = fields.Float("Location Longitude", digits=(16, 13))


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def attendance_manual(self, next_action, entered_pin=False, location=False):
        res = super(
            HrEmployee, self.with_context(attendance_location=location)
        ).attendance_manual(next_action, entered_pin)
        return res

    def _attendance_action_change(self):
        res = super()._attendance_action_change()
        location = self.env.context.get("attendance_location", False)
        if location[0] == 0 and location[1] == 0:
            raise UserError(_("Please enable location or allow access to location service"))
        if location:
            if self.env.user.company_id.enable_geofencing and self.env.user.company_id.geo_fencing_distance > 0:
                company_location = self.env['hr.work.location'].search([('address_id', '=', self.env.user.company_id.partner_id.id)], limit=1)
                if company_location:
                    company_coordinates = [company_location.location_latitude, company_location.location_longitude]
                    attendance_coordinates = [location[0], location[1]]
                    distance = GC(company_coordinates, attendance_coordinates)
                    if distance > self.env.user.company_id.geo_fencing_distance:
                        raise UserError(_('You cannot register attendance %skm away from the company location') % self.env.user.company_id.geo_fencing_distance)
            if self.attendance_state == "checked_in":
                res.write(
                    {
                        "check_in_latitude": location[0],
                        "check_in_longitude": location[1],
                    }
                )
            else:
                res.write(
                    {
                        "check_out_latitude": location[0],
                        "check_out_longitude": location[1],
                    }
                )
        return res
