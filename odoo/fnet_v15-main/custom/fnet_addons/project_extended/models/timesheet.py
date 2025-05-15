from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.rrule import rrule, DAILY
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    enable_timesheet_alert = fields.Boolean('Sent Timesheet Remainder')


class ProjectTaskType(models.Model):
    _name = 'task.type'
    _description = 'Task Type'

    name = fields.Char(string="Name")


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')
    task_type = fields.Many2one('task.type', 'Task Type')

    @api.onchange('start_time', 'end_time')
    def onchange_start_end_time(self):
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise UserError("Start Time cannot be greater than End Time")
        elif self.start_time and self.end_time:
            self.unit_amount = self.end_time - self.start_time
        else:
            self.unit_amount = 0.0
    def _cron_timesheet_entry_alert(self):
        companies = self.env['res.company'].search([('enable_timesheet_alert', '=', True)])
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        menu_id = self.env.ref('hr_timesheet.timesheet_menu_root').id
        url += '/web#menu_id=%s&view_type=list&model=%s' % (menu_id, self._name)
        for company in companies:
            employee_ids = self.env['hr.employee'].search([('company_id', '=', company.id), ('enable_timesheet_alert', '=', True)])
            final_end_date = fields.Date.today()
            start_date = final_end_date - timedelta(days=company.timesheet_alert_day)
            extra_days = 0
            for date in rrule(DAILY, dtstart=start_date, until=final_end_date - timedelta(days=1)):
                if date.strftime('%A') == 'Sunday':
                    extra_days += 1
            final_start_date = start_date - timedelta(days=extra_days)
            for employee in employee_ids:
                timesheet_ids = self.env['account.analytic.line'].search([('employee_id', '=', employee.id), ('date', '>=', final_start_date)])
                if not timesheet_ids:
                    mail_content = """
                        <p>
                            Hello %s,
                        </p>
                        <p>
                            You have not updated your timesheet for %s days. Kindly update time sheets regularly.
                            <div style="padding: 16px 8px 16px 8px;">
                            <a href="%s"
                               style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                Enter Timesheet
                            </a>
                        </div>
                        </p>
                        <p>
                            Thanks & Regards,<br/>
                            Futurenet Admin.
                        </p>
                    """ % (employee.name, str(company.timesheet_alert_day), url)
                    main_content = {
                        'subject': "Timesheet Remainder",
                        'body_html': mail_content,
                        'email_to': employee.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()
