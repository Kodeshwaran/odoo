from odoo import api, fields, models
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    update_value = fields.Integer(string="Value", readonly=False, related='company_id.update_value', store=True)
    update_type = fields.Selection([('day', 'Days'), ('mon', 'Months')], readonly=False, related='company_id.update_type', store=True)
    execution_date = fields.Date(string="Next Execution Date", readonly=False, related='company_id.execution_date', store=True)

    @api.onchange('update_value', 'update_type')
    def _onchange_period(self):
        if self.update_type and self.update_type == 'day':
            self.execution_date = fields.Date.today() + timedelta(days=self.update_value)
        elif self.update_type and self.update_type == 'mon':
            self.execution_date = fields.Date.today() + relativedelta(months=self.update_value)


class ResCompany(models.Model):
    _inherit = 'res.company'

    update_value = fields.Integer(string="Value")
    update_type = fields.Selection([('day', 'Days'), ('mon', 'Months')])
    execution_date = fields.Date(string="Next Execution Date")


