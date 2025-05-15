# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    is_unique_calendar = fields.Boolean(string='Employee Based Calendar?')
    emp_resource_calendar_id = fields.Many2one('resource.calendar', ' Employee Working Hours')