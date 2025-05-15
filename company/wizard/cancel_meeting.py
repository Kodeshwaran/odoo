import datetime
from odoo.exceptions import ValidationError
from odoo import api, fields, models,tools



class CompanyMeetingwizard(models.TransientModel):
    _name = "cancel.meeting.wizard"
    _description = "company meeting wizard"

    meeting_id=fields.Many2one("company.meeting",string='meeting ')
    reason=fields.Text(string='Reason')
    date_cancel=fields.Date(string='Cancel_date')

    def action_cancel(self):
        if self.meeting_id.attented_date == fields.Date.today():
            raise ValidationError('You are not allowed to cancel the meeting today.')
        return


    @api.model
    def default_get(self, fields):
        res = super(CompanyMeetingwizard, self).default_get(fields)
        res['date_cancel'] = datetime.date.today()
        return res