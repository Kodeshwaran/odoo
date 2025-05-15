from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class ShiftChangeRequest(models.Model):
    _name = 'shift.change.request'
    _description = "HR Shift Change Request"
    _inherit = ['mail.thread']

    employee_assigned_id = fields.Text(string='Employee Name', readonly=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda s: s.env.company)
    shift_assigned_id = fields.Text(string='Shift', readonly=True)
    assigned_date = fields.Text(string="Date", readonly=True)
    assigned_start_time = fields.Float(string="Start Time", readonly=True)
    assigned_end_time = fields.Float(string="End Time", readonly=True)
    employee_requested_id = fields.Text(string='Employee Name', readonly=True)
    shift_requested_id = fields.Text(string='Shift', readonly=True)
    requested_date = fields.Text(string='Date', readonly=True)
    requested_start_time = fields.Float(string="Start Time", readonly=True)
    requested_end_time = fields.Float(string="End Time", readonly=True)
    state = fields.Selection([('send', 'Sent'), ('accept', 'Accepted'), ('reject', 'Rejected'), ('manager_approve', 'Manager Approved'), ('manager_reject', 'Manager Rejected')], default='send', required=True, copy=False, tracking=True)
    assigned_emp_shift = fields.Many2one('hr.employee.shift')
    requested_emp_shift = fields.Many2one('hr.employee.shift')
    assigned_shift_id = fields.Many2one('hr.shift')
    replaced_shift_id = fields.Many2one('hr.shift')
    employee_assigned_name = fields.Many2one('hr.employee')
    employee_requested_name = fields.Many2one('hr.employee')
    is_assigned_emp = fields.Boolean(compute='check_user')
    is_requested_emp = fields.Boolean(compute='check_user')
    is_manager = fields.Boolean(compute='check_user')
    shift_week = fields.Selection([('previous', 'Previous Week'), ('upcoming', 'Upcoming Week')], default="previous", string="Select Week")
    shift_count = fields.Integer(string="Shifts", compute="compute_shift_count", store=True)
    # date_week_ids = fields.One2many('hr.employee.shift', compute='_compute_date_week_ids')
    #
    # @api.depends('shift_week')
    # def _compute_date_week_ids(self):
    #     for rec in self:
    #         previous_date = rec.assigned_emp_shift.date - relativedelta(weeks=1)
    #         coming_date = rec.assigned_emp_shift.date + relativedelta(weeks=1)
    #         if rec.shift_week == 'previous':
    #             previous_week = self.env['hr.employee.shift'].search([('date', '>=', previous_date), ('date', '<', rec.assigned_emp_shift.date)])
    #             rec.date_week_ids = previous_week.ids
    #         elif rec.shift_week == 'upcoming':
    #             coming_week = self.env['hr.employee.shift'].search([('date', '>', rec.assigned_emp_shift.date), ('date', '<=', coming_date)])
    #             rec.date_week_ids = coming_week.ids
    #         else:
    #             rec.date_week_ids = False

    @api.depends('assigned_emp_shift', 'requested_emp_shift')
    def compute_shift_count(self):
        for rec in self:
            if rec.assigned_emp_shift and rec.requested_emp_shift:
                shift_count = self.env['hr.employee.shift'].search_count([('id', 'in', [rec.assigned_emp_shift.id, rec.requested_emp_shift.id])])
                rec.shift_count = shift_count
            else:
                rec.shift_count = 0

    def action_view_shift(self):
        return {
            'name': _('Shifts'),
            'type': 'ir.actions.act_window',
            'res_model': "hr.employee.shift",
            'view_mode': 'list,form',
            'domain': [('id', 'in', [self.assigned_emp_shift.id, self.requested_emp_shift.id])],
        }


    def check_user(self):
        for rec in self:
            if rec.employee_assigned_name.parent_id.user_id.id == self.env.uid:
                rec.is_manager = True
            else:
                rec.is_manager = False
            if rec.employee_assigned_name.user_id.id == self.env.uid:
                rec.is_assigned_emp = True
            else:
                rec.is_assigned_emp = False
            if rec.employee_requested_name.user_id.id == self.env.uid:
                rec.is_requested_emp = True
            else:
                rec.is_requested_emp = False


    def name_get(self):
        result = []
        for rec in self:
            name = "Shift change for " + rec.requested_date
            result.append((rec.id, name))
        return result

    def unlink(self):
        if self.state in ['send', 'accept', 'reject', 'manager_approve', 'manager_reject']:
            raise UserError(_("You cannot delete Shift change request after requesting."))
        return super(ShiftChangeRequest, self).unlink()

    def action_employee_accept(self):
        for rec in self:
            rec.write({
                'state': 'accept',
            })
            subject = "%s's Shift Change Request - Accepted" % (str(self.employee_assigned_id))
            body = """<p>Dear <strong>%s</strong>,</p>
                      <p>As %s is requesting a re-schedule in shift on %s, </br>
                      I have accepted the request for change in shift from %s to <strong>%s</strong> on my behalf.</br></br>
                      Thank You.</br>
                      </p>
                      <div style="padding: 16px 8px 16px 8px;">
                      <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" 
                      href="%s">
                            View Shift Change Request
                      </a>
                      </div>
                      <p>Sincerely,<br/>
                         %s</p>""" % (
            str(self.employee_assigned_name.parent_id.name), str(self.employee_assigned_name.name), self.requested_date, str(self.shift_assigned_id), str(self.shift_requested_id), self.get_mail_url(),
            str(self.employee_requested_name.name))
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_from': str(self.employee_requested_name.work_email),
                'email_to': str(self.employee_assigned_name.parent_id.work_email),
                'email_cc': str(self.company_id.shift_cc_mail)
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

    def action_employee_reject(self):
        for rec in self:
            rec.write({
                'state': 'reject',
            })
            subject = "%s's Shift Change Request - Rejected" % (str(self.employee_assigned_id))
            body = """<p>Dear <strong>%s</strong>,</p>
                      <p>I regret to inform you that I cannot accept your shift change at this time.</br>
                      Thank you so much for your patience concerning my reply.</br>
                      </p>
                      <div style="padding: 16px 8px 16px 8px;">
                      <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" 
                      href="%s">
                            View Shift Change Request
                      </a>
                      </div>
                      <p>Sincerely,<br/>
                         %s</p>""" % (
                str(self.employee_assigned_name.name), self.get_mail_url(),
                str(self.employee_requested_name.name))
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_from': str(self.employee_requested_name.work_email),
                'email_to': str(self.employee_assigned_name.work_email),
                'email_cc': str(self.company_id.shift_cc_mail),
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

    def action_manager_approve(self):
        subject = "%s's Shift Change Request - Approved(By Manager)" % (str(self.employee_assigned_id))
        body = """<p>Dear <strong>%s</strong> and <strong>%s</strong>,</p>
                          <p> </br>
                          I have <strong>approved</strong> the shift change, swapped from <strong>%s</strong> shift to <strong>%s</strong> shift.</br></br>
                          Thank You.</br>
                          </p>
                          <div style="padding: 16px 8px 16px 8px;">
                          <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" 
                          href="%s">
                                View Shift Change Request
                          </a>
                          </div>
                          <p>Sincerely,<br/>
                             %s</p>""" % (
            str(self.employee_assigned_name.name), str(self.employee_requested_name.name), str(self.shift_assigned_id), str(self.shift_requested_id), self.get_mail_url(),
            str(self.employee_assigned_name.parent_id.name))
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': str(self.employee_assigned_name.parent_id.work_email),
            'email_cc': str(self.company_id.shift_cc_mail),
            # 'email_cc': 'rims@futurenet.in',
            'email_to': '%s, %s' % (
            str(self.employee_assigned_name.work_email), str(self.employee_requested_name.work_email)),
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        self.write({'state': 'manager_approve'})
        hr_employee_shift = self.env['hr.employee.shift']
        assigned_change_shift = hr_employee_shift.search([('id', '=', self.assigned_emp_shift.id)], limit=1)
        for assigned in assigned_change_shift:
            assigned.write({
                'shift_id': self.replaced_shift_id.id,
                'start_time': self.requested_start_time,
                'end_time': self.requested_end_time,
                'shift_swapped': True,
            })
        requested_change_shift = hr_employee_shift.search([('id', '=', self.requested_emp_shift.id)], limit=1)
        for requested in requested_change_shift:
            requested.write({
                'shift_id': self.assigned_shift_id.id,
                'start_time': self.assigned_start_time,
                'end_time': self.assigned_end_time,
                'shift_swapped': True,
            })

    def action_manager_reject(self):
        for rec in self:
            rec.write({
                'state': 'manager_reject',
            })
            subject = "%s's Shift Change Request - Rejected(By Manager)" % (str(self.employee_assigned_id))
            body = """<p>Dear <strong>%s</strong> and <strong>%s</strong>,</p>
                      <p></br>
                      I have <strong>rejected</strong> the shift change request.</br></br>
                      Thank You.</br>
                      </p>
                      <div style="padding: 16px 8px 16px 8px;">
                      <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" 
                      href="%s">
                            View Shift Change Request
                      </a>
                      </div>
                      <p>Sincerely,<br/>
                         %s</p>""" % (
                str(self.employee_assigned_name.name), str(self.employee_requested_name.name), self.get_mail_url(),
                str(self.employee_assigned_name.parent_id.name))
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_from': str(self.employee_assigned_name.parent_id.work_email),
                'email_to': '%s, %s' % (
                    str(self.employee_assigned_name.work_email), str(self.employee_requested_name.work_email)),
                'email_cc': str(self.company_id.shift_cc_mail),
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

    def task_send_mail(self):
        subject = "%s's Shift Change Request" % (str(self.employee_assigned_id))
        body = """<p>Dear <strong>%s</strong>,</p>
                  <p></br>
                  I'm requesting to change my shift so that I'd work %s instead on %s.</br></br>
                  Thank You.</br>
                  </p>
                  <div style="padding: 16px 8px 16px 8px;">
                  <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" 
                  href="%s">
                        View Shift Change Request
                  </a>
                  </div>
                  <p>Sincerely,<br/>
                     %s</p>""" % (str(self.employee_requested_id), str(self.shift_requested_id), self.requested_date, self.get_mail_url(), str(self.employee_assigned_id))
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': str(self.employee_assigned_name.work_email),
            'email_to': str(self.employee_requested_name.work_email),
            'email_cc': str(self.company_id.shift_cc_mail),
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    @api.model
    def create(self, vals):
        record = super(ShiftChangeRequest, self).create(vals)
        record.task_send_mail()
        return record

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%s&model=shift.change.request&view_type=form' % (self.id)
        return url