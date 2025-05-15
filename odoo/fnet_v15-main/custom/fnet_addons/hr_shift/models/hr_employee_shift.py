from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import pytz


def to_naive_utc(datetime, record):
    tz_name = record._context.get('tz') or record.env.user.tz
    tz = tz_name and pytz.timezone(tz_name) or pytz.UTC
    return tz.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(pytz.UTC).replace(tzinfo=None)


class EmployeeShift(models.Model):
    _name = "hr.employee.shift"
    _description = "HR Employee Shift"
    _inherit = ['mail.thread']



    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,)
    shift_id = fields.Many2one('hr.shift', string="Shift", required=True, tracking=True)
    date = fields.Date("Date", required=True)
    start_time = fields.Float("Start Time")
    end_time = fields.Float("End Time")
    date_start = fields.Datetime("Expected Start Date")
    date_end = fields.Datetime("Expected End Date")
    actual_date_start = fields.Datetime("Actual Check In", compute='_get_actual_hours')
    actual_date_end = fields.Datetime("Actual Check Out", compute='_get_actual_hours')
    attendance_ids = fields.One2many('hr.attendance', 'shift_id', string="Attendances")
    employee_level = fields.Selection([('l1', 'L1'),('l2', 'L2'),('l3', 'L3'),('l4', 'L4'),('db', 'DB')], related='employee_id.employee_level')
    state = fields.Selection([('confirm', 'Confirmed'), ('cancel', 'Cancelled')], default="confirm", tracking=True)
    total_hours = fields.Float('Total Hours', compute='_get_hours')
    actual_hours = fields.Float('Actual Worked Hours', compute='_get_actual_hours')
    overtime = fields.Float("Extra Worked Hours", compute='_get_actual_hours')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    # plan_id = fields.Many2one('hr.shift.plan', string="Plan")
    month_plan_id = fields.Many2one('hr.shift.month.plan', string="Plan")
    # color = fields.Char("Color", related='shift_id.color')
    replaced_shift_count = fields.Integer(compute="_compute_replaced_shift_count")
    shift_swapped = fields.Boolean()
    request_emp=fields.Boolean(compute='check_user')

    status=fields.Selection([('sent', 'Sent'),('approve', 'Approve'),('approval_cancel', 'Cancel')],readonly=True)
    request_allowance=fields.Boolean(related='shift_id.allowance_request')



    def check_user(self):
        for rec in self:
            if rec.employee_id.user_id.id == self.env.uid:
                rec.request_emp = True
            else:
                rec.request_emp = False

    # shift_count = fields.Integer(string="Shifts", compute="compute_shift_count", store=True)
    # def compute_shift_count(self):
    #     for rec in self:
    #         shift = self.env['shift.change.request'].search(
    #             [('assigned_date', '=', rec.date.strftime('%d-%m-%Y')), '|',
    #              ('employee_assigned_name', '=', self.employee_id.id),
    #              ('employee_requested_name', '=', self.employee_id.id),
    #              ('state', 'not in', ['reject'])])
    #         print("---", shift, "--shift-\n")
    #         if shift:
    #             rec.shift_count = 1
    #         else:
    #             rec.shift_count = 0



    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%s&model=hr.employee.shift&view_type=form' % (self.id)
        return url

    def action_shift_approve(self):
        subject = "%s's Shift Request" % (str(self.employee_id.name))
        body = """<p>Dear <strong>%s</strong>,</p>
                        <p></br>
                        I'm requesting to approve my shift request</br></br>
                        Thank You.</br>
                        </p>
                        <div style="padding: 16px 8px 16px 8px;">
                        <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" 
                        href="%s">
                              View Shift Request
                        </a>
                        </div>
                        <p>Sincerely,<br/>
                           %s</p>""" % (
        str(self.employee_id.parent_id.name),self.get_mail_url(),self.employee_id.name)
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': str(self.employee_id.work_email),
            'email_to': str(self.employee_id.parent_id.work_email),
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        self.write({
            'status': 'sent',
        })

    def action_shift_approved(self):
        subject = "%s's Shift Request Approved" % (self.employee_id.name)
        body = """<p>Dear <strong>%s</strong>,</p>
                             <p></br>
                             Approved your request for Night Shift</br></br>
                             Thank You.</br>
                             </p>
                             <div style="padding: 16px 8px 16px 8px;">
                             <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" 
                             href="%s">
                                   View Shift Request Approved
                             </a>
                             </div>
                             <p>Sincerely,<br/>
                                %s</p>""" % (
            (self.employee_id.name), self.get_mail_url(),self.employee_id.parent_id.name)
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': str(self.employee_id.parent_id.work_email),
            'email_to':str(self.employee_id.work_email),
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        self.write({
            'status': 'approve',
        })


    def action_cancel(self):
        subject = "%s's Shift Request Cancel" % (self.employee_id.name)
        body = """<p>Dear <strong>%s</strong>,</p>
                                     <p></br>
                                     Shift Request Cancel</br></br>
                                     Thank You.</br>
                                     </p>
                                     <div style="padding: 16px 8px 16px 8px;">
                                     <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" 
                                     href="%s">
                                           View Shift Request Cancel
                                     </a>
                                     </div>
                                     <p>Sincerely,<br/>
                                        %s</p>""" % (
            (self.employee_id.name), self.get_mail_url(), self.employee_id.parent_id.name)
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': str(self.employee_id.parent_id.work_email),
            'email_to': str(self.employee_id.work_email),
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        self.write({
            'status': 'approval_cancel',
        })



    def action_view_shift(self):
        assigned_shifts = self.env['shift.change.request'].search(
            [('assigned_date', '=', self.date.strftime('%d-%m-%Y')),
             ('employee_assigned_name', '=', self.employee_id.id),
             ('state', 'not in', ['reject'])]).requested_emp_shift
        requested_shifts = self.env['shift.change.request'].search(
            [('assigned_date', '=', self.date.strftime('%d-%m-%Y')),
             ('employee_requested_name', '=', self.employee_id.id),
             ('state', 'not in', ['reject'])]).assigned_emp_shift
        return {
            'name': "Shifts",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.employee.shift',
            'res_id': assigned_shifts.id if assigned_shifts else requested_shifts.id,
        }

    def _compute_replaced_shift_count(self):
        for rec in self:
            count = self.env['shift.change.request'].search_count([('assigned_date', '=', rec.date.strftime('%d-%m-%Y')), '|', ('employee_assigned_name', '=', self.employee_id.id), ('employee_requested_name', '=', self.employee_id.id), ('state', 'not in', ['reject'])])
            rec.replaced_shift_count = count


    def action_open_replaced_shift_smt_btn(self):
        shift_replace_id = self.env['shift.change.request'].search([('assigned_date', '=', self.date.strftime('%d-%m-%Y')), '|', ('employee_assigned_name', '=', self.employee_id.id), ('employee_requested_name', '=', self.employee_id.id), ('state', 'not in', ['reject'])], limit=1)
        return {
            'name': "Replace Request",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'shift.change.request',
            'res_id': shift_replace_id.id,
        }

    def action_cancel(self):
        for rec in self:
            rec.write({
                'state': 'cancel',
            })

    def unlink(self):
        for rec in self:
            if rec.state not in ['confirm']:
                raise UserError(_("You cannot delete Shift after confirming."))
        return super(EmployeeShift, self).unlink()

    def action_shift_change_req(self):
        for rec in self:
            shift_change = {
                'name': ('Shift change request for %s') % (rec.date.strftime('%d-%m-%Y')),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'shift.change.request.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_assigned_emp_shift_date': rec.date,
                    'default_assigned_emp_level': rec.employee_level,
                    'default_assigned_emp_id': rec.employee_id.id,
                    'default_assigned_emp_shift': rec.shift_id.id,
                    'default_assigned_emp': self.id,
                    }
            }
            return shift_change

    @api.onchange('start_time', 'end_time', 'date')
    def compute_dates(self):
        for rec in self:
            if rec.end_time and rec.date:
                from_time = (datetime.min + timedelta(hours=rec.start_time)).time()
                to_time = (datetime.min + timedelta(hours=rec.end_time)).time()
                from_date = datetime.combine(rec.date, from_time)
                to_date = datetime.combine(rec.date,to_time)
                if rec.end_time < rec.start_time:
                    to_date = to_date + timedelta(days=1)
                tz_from_date = to_naive_utc((from_date), rec)
                tz_to_date = to_naive_utc((to_date), rec)
                rec.date_start = tz_from_date
                rec.date_end = tz_to_date

    # @api.constrains('employee_id', 'shift_id', 'date')
    # def constrain_check(self):
    #     for rec in self:
    #         shift_id = self.env['hr.employee.shift'].search([('id', '!=', rec.id), ('employee_id', '=', rec.employee_id.id), ('date', '=', rec.date)])
    #         if shift_id:
    #             raise UserError(_("You cannot allocate more than one shift on same day."))

    def name_get(self):
        result = []
        for rec in self:
            name = rec.employee_id.name + ' - ' + rec.shift_id.name + ' on ' + datetime.strftime(rec.date, '%d-%b-%Y')
            result.append((rec.id, name))
        return result

    @api.onchange('shift_id')
    def onchange_time(self):
        for rec in self:
            if rec.shift_id:
                rec.start_time = rec.shift_id.start_time
                rec.end_time = rec.shift_id.end_time
                if rec.shift_id.name == 'WeekOff':
                    rec.start_time = 0
                    rec.end_time = 23.0

    @api.depends('start_time', 'end_time')
    def _get_hours(self):
        for rec in self:
            hours = 0
            if rec.end_time and rec.shift_id.code != 'WO':
                from_time = timedelta(hours=rec.start_time)
                to_time = timedelta(hours=rec.end_time)
                if rec.end_time < rec.start_time:
                    max = 24.0 - rec.start_time
                    hours = max + rec.end_time
                else:
                    delta = to_time - from_time
                    sec = delta.total_seconds()
                    hours = sec / (60 * 60)
            rec.total_hours = hours

    @api.depends('attendance_ids', 'attendance_ids.worked_hours', 'total_hours')
    def _get_actual_hours(self):
        for rec in self:
            attendance_ids = self.env['hr.attendance'].search([('id', 'in', rec.attendance_ids.ids)], order='check_in ASC')
            in_date = False
            out_date = False
            if attendance_ids:
                in_date = attendance_ids[0].check_in
                out_date = attendance_ids[len(attendance_ids)-1].check_out
            rec.actual_date_start = in_date
            rec.actual_date_end = out_date
            rec.actual_hours = sum(rec.attendance_ids.mapped('worked_hours'))
            extra_hours = sum(rec.attendance_ids.mapped('worked_hours')) - rec.total_hours
            rec.overtime = extra_hours if extra_hours > 0 else 0



