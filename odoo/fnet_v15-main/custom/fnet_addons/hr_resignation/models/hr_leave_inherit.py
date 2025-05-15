from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('hr_resignation.group_restrict_leave_apply'):
            raise ValidationError('You cannot apply for leave as you are in notice period.')
        return super(HolidaysRequest, self).create(vals)