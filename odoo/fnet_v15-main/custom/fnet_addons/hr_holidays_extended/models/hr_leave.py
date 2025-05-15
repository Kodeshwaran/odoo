# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from datetime import timedelta, time, datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import float_to_time
from dateutil.relativedelta import relativedelta
import pytz
import calendar
from requests import Request
from odoo.tools.float_utils import float_round


class LeaveType(models.Model):
    _inherit = 'hr.leave.type'

    maximum_days_allowed = fields.Float(string="Maximum Days Allowed", help="Requesting Maximum Days Consecutively")
    past_allowed_days = fields.Float(string="Past Allowed Days", help="Able to request for leave before than current date")
    eligible_after = fields.Integer("Eligible after(Days/DOJ)", help="Based on Employee date of joining")
    eligible_before = fields.Integer("Apply prior to(Days)", help="How early(Days) leave need to create.")
    time_eligible_before = fields.Float("Apply prior to(Time)", digits=(16, 2),
                                        help="How early(Time) leave need to create.")
    reset = fields.Boolean("Reset", help="Reset leave automatically")
    pro_rata_basis = fields.Boolean(string="Pro Rata Basis")
    reset_based_on = fields.Selection([('join', 'Joining Date'), ('confirm', 'Confirmation Date')])
    reset_days = fields.Integer("Reset to Days", help="The days will automatically allocated on every year")
    reset_leave_month = fields.Selection([('Jan', 'January'), ('Feb', 'February'), ('Mar', 'March'),
                                          ('Apr', 'April'), ('May', 'May'), ('Jun', 'June'),
                                          ('Jul', 'July'), ('Aug', 'August'), ('Sep', 'September'),
                                          ('Oct', 'October'), ('Nov', 'November'), ('Dec', 'December')],
                                         string="Leave Reset Period")
    reset_leave_days = fields.Integer(string="days")
    maximum_days = fields.Integer("Maximum Days",
                                  help="Maximum number of days can be allocated. Set 0 to allow unlimited.Only restrict while request")
    minimum_days = fields.Integer("Minimum Days",
                                  help="Minimum number of days can be allocated. Set 0 to allow unlimited.Only restrict while request")
    allow_encashment = fields.Boolean(string="Allow Encashment")
    restrict_advance_allocation = fields.Boolean(string="Restrict Advance Allocation",
                                                 help="This will restrict employee to request in advance")
    probation_validation = fields.Boolean(string="Enable Probation Validation")
    is_casual = fields.Boolean("Is Casual Leave")
    is_maternity = fields.Boolean("Is Maternity Leave")
    is_privilege = fields.Boolean("Is Privilege Leave")
    is_lop = fields.Boolean("Is LOP")
    is_compensatory_off = fields.Boolean("Is Compensatory Off")
    expiry_days = fields.Integer(string="Expiry days")
    calcultaion_type = fields.Selection([('working', 'Working Days'), ('calendar', 'CalendarDays')],
                                        string="Calculation Method", default='working', required=1)
    leave_validation_type = fields.Selection(
        selection_add=[('higher', 'Manager'), ('both',), ('three', 'Team Leader,Time Off Officer and Manager')])
    carry_forward = fields.Boolean(string="Carry to next year")
    maximum_limit_days = fields.Integer("Maximum limit (in Days) can be carried forward")
    is_alternative_leave = fields.Boolean("Alternative leave eligibilty")
    restrict_days = fields.Boolean('Restrict Days', help="Restrict user to apply leave more than month count.")
    allow_swap_leave = fields.Boolean('Allow Swap Leave', help="Employee's Manager can swap time off type of the request if enabled.")
    eligible_within = fields.Integer("Apply Within(Days)", help="How early(Days) allocation need to create.")
    allocation_validation_type = fields.Selection(selection_add=[('manager', 'Approved by Manager'), ('manager_hod', 'Approved by Manager,Head of the Department')])
    advance_leave_notice_ids = fields.One2many('advance.leave.notice', 'leave_type_id', string="Leave Control")


class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    comp_holiday_status_id = fields.Many2one("hr.leave.type", string="Remaining leaves to take from")
    comp_days = fields.Float("Compensatory Days")
    date_join = fields.Date("Joining Date", related='employee_id.date_join', store=True)
    is_casual = fields.Boolean("Is Casual", related="holiday_status_id.is_casual", readonly=True)

    is_lop = fields.Boolean("Is LOP", related="holiday_status_id.is_lop", readonly=True)
    is_privilege = fields.Boolean("Is Privilege Leave", related="holiday_status_id.is_privilege", readonly=True)
    available_privilege_leave = fields.Boolean('PL Available', compute='compute_get_privilege_leave')
    emp_manager = fields.Many2one(string="Employee Manager", related="employee_id.parent_id")
    is_manager = fields.Boolean(string="Is Manager", compute="check_user")
    is_employee = fields.Boolean(string="Is Employee", compute="check_user")
    comp_leave_id = fields.Many2one('hr.leave')
    alternative_employee_id = fields.Many2one('hr.employee', string="Alternative Employee")
    state = fields.Selection(selection_add=[('confirm_cancel', 'Cancelled')])
    cancel_date_from = fields.Date('Cancel From')
    cancel_till = fields.Selection([('full', 'Full'), ('until', 'Until'), ('after', 'After')], string="Cancel of",
                                   default='full')
    first_cancel_approver_id = fields.Many2one(
        'hr.employee', string='First Cancel Approval', readonly=True, copy=False,
        help='This area is automatically filled by the user who validate the cancel request')
    second_cancel_approver_id = fields.Many2one(
        'hr.employee', string='Second Cancel Approval', readonly=True, copy=False,
        help='This area is automatically filled by the user who validate the cancel request with second level (If time off type need second validation)')
    is_request = fields.Boolean(string='Apply', default=False, store=True)
    final_tot_leaves = fields.Integer('Compensation Leaves', readonly=True)
    compensation_count = fields.Integer("Compensation", compute="compute_count")
    compute_remaining_days = fields.Float(store=True, compute="get_remaining_days")
    new_requires_allocation = fields.Selection([('yes', 'Yes'),('no', 'No Limit')], related="comp_holiday_status_id.requires_allocation")
    is_swap_leave = fields.Selection([('yes', 'Yes'), ('no', 'No')], default="no")
    is_lop_leave = fields.Boolean(compute="check_is_lop")
    is_lop_submitted = fields.Boolean()
    emp_leave_availability = fields.Boolean()
    is_hod = fields.Boolean(compute="check_hod_user")

    @api.depends_context('uid')
    def _compute_description(self):
        self.check_access_rights('read')
        self.check_access_rule('read')

        is_officer = self.user_has_groups('hr_holidays.group_hr_holidays_user')

        for leave in self:
            if is_officer or leave.user_id == self.env.user or leave.employee_id.leave_manager_id == self.env.user or leave.employee_id.department_id.head_of_department.user_id == self.env.user:
                leave.name = leave.sudo().private_name
            else:
                leave.name = '*****'

    @api.onchange('is_swap_leave')
    def get_available_leave_types(self):
        employee_leave_types = []
        available_leave_types = self.env['hr.leave.allocation'].search(
            [('employee_id', '=', self.employee_id.id),
             ('remaining_leave', '>=', self.number_of_days),
             ('holiday_status_id.code', '!=', 'sl'),
             ('holiday_status_id.is_alternative_leave', '!=', False),
             ('state', '=', 'validate')]).mapped('holiday_status_id')
        return {'domain': {'alternate_type': [('id', 'in', available_leave_types.ids)]}}
    #
    # def get_available_leave_types(self):
    #     employee_leave_types = []
    #     available_leave_types = self.env['hr.leave.allocation'].search(
    #         [('employee_id', '=', self.employee_id.id),
    #          ('remaining_leave', '>=', self.number_of_days),
    #          ('holiday_status_id.code', '!=', 'SL'),
    #          ('state', '=', 'validate')]).mapped('holiday_status_id')
    #     if available_leave_types:
    #         for leave_type in available_leave_types:
    #             back_end = str(leave_type.id)
    #             employee_leave_types.append((back_end, leave_type.name))
    #     return employee_leave_types


    # alternate_type = fields.Selection(selection='get_available_leave_types', string="Select Alternate Leave")
    alternate_type = fields.Many2one('hr.leave.type', string="Select Alternate Leave")

    @api.depends('holiday_status_id')
    def check_is_lop(self):
        for rec in self:
            if rec.holiday_status_id.is_lop:
                rec.is_lop_leave = True
            else:
                rec.is_lop_leave = False
    def check_hod_user(self):
        for rec in self:
            if rec.employee_id.department_id.head_of_department.user_id.id == self.env.user.id:
                rec.is_hod = True
            else:
                rec.is_hod = False

    @api.onchange('is_swap_leave', 'alternate_type')
    def get_emp_leave_count(self):
        for rec in self:
            remaining_leave_balance = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('holiday_status_id', '=', rec.alternate_type.id),
                 ('state', '=', 'validate')])
            if remaining_leave_balance:
                remaining_leaves = sum(remaining_leave_balance.mapped('remaining_leave'))
                if rec.number_of_days <= remaining_leaves:
                    rec.emp_leave_availability = True
                else:
                    rec.emp_leave_availability = False
            else:
                rec.emp_leave_availability = False

    @api.depends('comp_holiday_status_id')
    def get_remaining_days(self):
        for rec in self:
            allocations = self.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
                                                                  ('holiday_status_id.is_privilege', '=', True),
                                                                  ('state', '=', 'validate')])
            remaining_leaves = sum(allocations.mapped('number_of_days_display')) - sum(
                allocations.mapped('leaves_taken'))

            if self.comp_holiday_status_id.is_privilege:
                self.compute_remaining_days = remaining_leaves
            else:
                self.compute_remaining_days = 0

    def check_user(self):
        for rec in self:
            if self.env.user.has_group('hr_holidays_extended.group_hr_holidays_administrator'):
                rec.is_employee = True
                rec.is_manager = True
            elif (self.env.user.id == rec.employee_id.parent_id.user_id.id) and (
                    self.env.user.id == rec.employee_id.user_id.id):
                rec.is_employee = True
                rec.is_manager = True
            elif self.env.user.id == rec.employee_id.parent_id.user_id.id:
                rec.is_manager = True
                rec.is_employee = False
            elif self.env.user.id == rec.employee_id.user_id.id:
                rec.is_employee = True
                rec.is_manager = False
            else:
                rec.is_employee = False
                rec.is_manager = False

    def get_compensation(self):
        comp_leave = self.env['hr.leave'].search([('comp_leave_id', '=', self.id)], limit=1)
        return {
            'name': _('Compensated Leaves'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_holidays.hr_leave_view_form').id,
            'res_model': 'hr.leave',
            'res_id': comp_leave.id,
        }

    def compute_count(self):
        for rec in self:
            rec.compensation_count = self.env['hr.leave'].search_count([('comp_leave_id', '=', self.id)])

    @api.depends('number_of_days')
    def compute_get_privilege_leave(self):
        for rec in self:
            allocations = self.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
                                                                  ('holiday_status_id.is_privilege', '=', True),
                                                                  ('state', '=', 'validate')])
            remaining_leaves = sum(allocations.mapped('number_of_days_display')) - sum(
                allocations.mapped('leaves_taken'))
            if remaining_leaves != 0 and remaining_leaves >= (
                    rec.number_of_days - rec.holiday_status_id.maximum_days_allowed):
                rec.available_privilege_leave = True
            else:
                rec.available_privilege_leave = False

    @api.onchange('employee_id')
    def onchange_alternative_employee_id(self):
        if self.employee_id:
            self.date_join = self.employee_id.date_join
        else:
            self.date_join = ''

    @api.onchange('cancel_date_from')
    def onchange_cancel_date(self):
        if self.cancel_date_from and self.request_date_from and self.cancel_date_from < self.request_date_from:
            raise UserError(_("Date should be in leave period"))
        if self.cancel_date_from and self.request_date_to and self.cancel_date_from > self.request_date_to:
            raise UserError(_("Date should be in leave period"))

    def cancel_request(self):
        start_date = fields.Date.from_string(self.request_date_from)
        end_date = fields.Date.from_string(self.request_date_to)
        mail_content = "  Hello  " + self.employee_id.name + ",<br>Your leave request of " + self.holiday_status_id.name + \
                       " on " + str(start_date) + " to " + str(end_date) + " has been Cancelled."
        main_content = {
            'subject': _('Leave Request Cancelled'),
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.employee_id.work_email,
        }
        self.env['mail.mail'].create(main_content).send()
        self.write({'state': 'confirm_cancel'})
        return {
            'type': 'ir.actions.act_window_close',
            'name': 'Cancelled'
        }

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url

    def get_mail_approval_url(self):
        action_id = self.env.ref('hr_holidays.hr_leave_action_action_approve_department', raise_if_not_found = False)
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s&action=%s' % (self.id, self._name, action_id.id)
        return url

    def mail_leave_request(self):
        if self.employee_id.user_id.id != self.env.uid and not self.env.user.has_group('hr_holidays_extended.group_hr_holidays_administrator'):
            raise UserError(_("You cannot submit other employee's leave."))
        self.write({'state': 'confirm'})
        subject = 'Leave Request'
        manager = self.employee_id.parent_id.work_email
        body = """<p>Dear Sir/Ma'am,</p>
                  <br/>
                  <p>Kindly approve my leave request</p>
                <center>
					<a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Leave</a>
					<br/><br/><br/>
                </center>""" % (self.get_mail_approval_url())
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.employee_id.work_email,
            'email_to':  manager,
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        if self.is_lop_leave:
            self.write({'is_lop_submitted': True})

    def action_lop_submit_to_hod(self):
        # code_dict = dict(self.fields_get(allfields=['alternate_type'])['alternate_type']['selection'])[self.alternate_type]
        if self.alternate_type and self.emp_leave_availability == False:
            raise ValidationError("Selected alternate leave - %s is not available for this employee, Please select any other available leave" % self.alternate_type.name)
        manager = self.employee_id.parent_id.work_email
        hod = self.employee_id.department_id.head_of_department.work_email
        if (self.is_manager and self.is_hod) or (self.employee_id.user_id.id == self.employee_id.department_id.head_of_department.user_id.id):
            self.action_hod_validate()
        elif self.is_manager and not self.is_hod and not self.employee_id.user_id.id == self.employee_id.department_id.head_of_department.user_id.id:
            self.write({'state': 'validate1'})
            subject = 'Alternate Leave Request'
            body = """<p>Dear Sir/Ma'am,</p>
                      <br/>
                      <p>Kindly Approve/Refuse the time off request.</p>
                    <center>
                        <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Leave</a>
                        <br/><br/><br/>
                    </center>""" % (self.get_mail_approval_url())
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': manager,
                'email_to': hod if hod else '',
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

    def action_hod_validate(self):
        if self.alternate_type:
            self.write({'holiday_status_id': self.alternate_type.id})
        self.write({'state': 'validate'})
        hod = self.employee_id.department_id.head_of_department.work_email
        subject = 'Leave Confirmed'
        body = """<p>Dear %s,</p>
                          <br/>
                          <p>Requested LOP time off is changed to <b>%s</b> upon Manager and HOD's decision.</p>
                        <center>
                            <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Leave</a>
                            <br/><br/><br/>
                        </center>""" % (
            self.employee_id.name, self.holiday_status_id.name, self.get_mail_url())
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': hod if hod == self.env.user.login else self.env.user.login,
            'email_to': self.employee_id.work_email,
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()


    def cancel_activity_update(self):
        to_clean, to_do = self.env['hr.leave'], self.env['hr.leave']
        for holiday in self:
            if self.cancel_till == 'full':
                note = _('New %s cancel Request created by %s') % (
                    holiday.holiday_status_id.name, holiday.create_uid.name)
            else:
                note = _('New %s cancel Request created by %s %s %s') % (
                    holiday.holiday_status_id.name, holiday.create_uid.name, holiday.cancel_till,
                    fields.Datetime.to_string(holiday.cancel_date_from))
            if holiday.state == 'cancel_request':
                to_clean |= holiday
            elif holiday.state == 'confirm_cancel':
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate1_cancel':
                holiday.activity_feedback(['hr_holidays.mail_act_leave_approval'])
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_second_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate':
                to_do |= holiday
            elif holiday.state == 'refuse':
                to_clean |= holiday
        if to_clean:
            to_clean.activity_unlink(
                ['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
        if to_do:
            to_do.activity_feedback(
                ['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])

    def check_eligible_date(self, employee_id, request_start_date, request_end_date, days, holiday_status_id):
        if self.env.user.has_group('hr_holidays_extended.group_hr_holidays_administrator'):
            return
        # todo Every validation must be written only after this line
        if self.is_swap_leave:
            return
        if not employee_id.date_join:
            raise UserError(_("Please update date of joining in employee form."))
        start_date = fields.Date.from_string(str(request_start_date))
        date_end = fields.Date.from_string(str(request_end_date))
        past_days = (fields.Date.today() - timedelta(days=holiday_status_id.past_allowed_days))
        if (start_date or date_end) < past_days and (holiday_status_id.past_allowed_days != 0):
            raise ValidationError(_('%s can only be requested within a %s-day period after it has been taken.') % (
                holiday_status_id.name, int(holiday_status_id.past_allowed_days)))
        no_of_days = days if days else 0
        end_date = fields.Date.from_string(employee_id.date_join) + timedelta(days=holiday_status_id.eligible_after)
        if holiday_status_id.probation_validation:
            if not employee_id.date_probation:
                raise UserError(_("Please update date of probation period in employee form."))
            probation_end = fields.Date.from_string(employee_id.date_probation)
            if start_date <= probation_end:
                raise UserError(_("Selected leave cannot applicable for employee in probation period."))
        if start_date <= end_date:
            raise UserError(_("You are not eligible for the current leave type."))
        if holiday_status_id.eligible_before:
            prior_date = fields.Date.today() + timedelta(days=holiday_status_id.eligible_before)
            # if str(request_start_date) >= str(fields.Date.today()) or str(request_end_date) >= str(fields.Date.today()):
            if start_date < prior_date:
                raise UserError(
                    _("Current leave cannot be applicable before %s days." % holiday_status_id.eligible_before))
        if holiday_status_id.restrict_advance_allocation and start_date > fields.Date.today():
            raise UserError(_("Current leave cannot taken in advance."))
        if holiday_status_id.time_eligible_before:
            tz = pytz.timezone(self.env.user.tz or 'UTC')
            before_time = float_to_time(holiday_status_id.time_eligible_before)
            current_time = datetime.now(tz).time()
            if start_date == fields.Date.today() and current_time > before_time:
                raise UserError(_("Current leave should be request before %s" % before_time))
        if (no_of_days > holiday_status_id.maximum_days_allowed) and (holiday_status_id.maximum_days_allowed != 0):
            raise ValidationError(_('%s can only be applied for a maximum of %s day(s).') % (
                    holiday_status_id.name, int(holiday_status_id.maximum_days_allowed)))
        if no_of_days < holiday_status_id.minimum_days:
            raise ValidationError(_('%s can only be applied for a minimum of %s days, consecutively.') % (
                    holiday_status_id.name, int(holiday_status_id.minimum_days)))
        if holiday_status_id.restrict_days:
            today = fields.Date.today()
            holiday_allocation = self.env['hr.leave.allocation'].search([('holiday_status_id', '=', holiday_status_id.id), ('employee_id', '=', employee_id.id),
                                 ('state', '=', 'validate'), ('date_from', '<=', today), ('date_to', '>=', today)], limit=1)
            total_allocation = holiday_allocation.number_of_days
            already_taken = sum(self.env['hr.leave'].search([('holiday_status_id', '=', holiday_status_id.id), ('employee_id', '=', employee_id.id),
                                 ('state', 'not in', ['refuse', 'confirm_cancel']), ('date_from', '>=', holiday_allocation.date_from), ('date_to', '<=', holiday_allocation.date_to)]).mapped('number_of_days'))
            if start_date.month == date_end.month:
                check_month = start_date.month
                leaves_allowed = check_month - holiday_allocation.date_from.month - already_taken + 1
                if leaves_allowed <= 0:
                    raise ValidationError(_('Your limit for %s for the month of %s has already been availed') % (holiday_status_id.name, start_date.strftime('%B')))
                if not leaves_allowed >= no_of_days:
                    raise ValidationError(_('You can avail only %s day(s) of %s for the month of %s') % (leaves_allowed, holiday_status_id.name, start_date.strftime('%B')))
            elif start_date.month != date_end.month:
                sm_from = start_date
                sm_to = sm_from.replace(day=calendar.monthrange(start_date.year, start_date.month)[1])
                days_in_start = (sm_to - sm_from).days + 1
                sm_allowed = sm_from.month - holiday_allocation.date_from.month - already_taken + 1
                if sm_allowed <= 0:
                    raise ValidationError(_('Your limit for %s for the month of %s has already been availed') % (holiday_status_id.name, start_date.strftime('%B')))
                if not sm_allowed >= days_in_start:
                    raise ValidationError(_('You can avail only %s day(s) of %s for the month of %s') % (sm_allowed, holiday_status_id.name, start_date.strftime('%B')))
                em_from = date_end.replace(day=1)
                em_to = date_end
                days_in_end = (em_to - em_from).days + 1
                em_allowed = em_from.month - holiday_allocation.date_from.month - already_taken - days_in_start + 1
                if em_allowed <= 0:
                    raise ValidationError(_('Your limit for %s for the month of %s has already been availed') % (holiday_status_id.name, date_end.strftime('%B')))
                if not em_allowed >= days_in_end:
                    raise ValidationError(_('You can avail only %s day(s) of %s for the month of %s') % (em_allowed, holiday_status_id.name, start_date.strftime('%B')))
        for holiday in  holiday_status_id.advance_leave_notice_ids:
            if (holiday.notice_leave_days and holiday.notice_days) > 0:
                request_start_date = fields.Date.from_string(request_start_date)
                days_difference = (request_start_date - fields.Date.today()).days
                if holiday.notice_leave_days <= days:
                    if days_difference < holiday.notice_days:
                        raise ValidationError(f'You must apply for a {days}-day leave at least {holiday.notice_days} days in advance.')
            # year_date_from = start_date.replace(day=1, month=1)
            # print("\n---",start_date.month, date_end.month,"--start_date.month, date_end.month--\n")
            # if start_date.month == date_end.month:
            #     date_from = start_date.replace(day=1, month=1)
            #     date_to = start_date.replace(day=calendar.monthrange(start_date.year, start_date.month)[1])
            #     already_taken = sum(self.env['hr.leave'].search([('holiday_status_id', '=', holiday_status_id.id), ('request_date_from', '>=', year_date_from), ('request_date_to', '<=', date_to), ('employee_id', '=', employee_id.id), ('state', '=', 'validate')]).mapped('number_of_days'))
            #     can_take = start_date.month - already_taken
            #     print("\n---",already_taken, can_take,"--already_taken, can_take--\n")
            #     print("\n---",no_of_days,"--no_of_days--\n")
            #     if can_take < no_of_days:
            #         if can_take <= 0:
            #             raise UserError(_("You have exceeded the maximum allowed leave for the current month."))
            #         else:
            #             raise UserError(_("You have only %s days remaining for the current month." % can_take))
            # else:
            #     # Prefix month availability check
            #     pref_date_from = year_date_from
            #     pref_date_to = start_date.replace(day=calendar.monthrange(start_date.year, start_date.month)[1])
            #     already_taken = sum(self.env['hr.leave'].search(
            #         [('holiday_status_id', '=', holiday_status_id.id), ('request_date_from', '>=', pref_date_from),
            #          ('request_date_to', '<=', pref_date_to), ('state', '=', 'validate')]).mapped('number_of_days'))
            #     current_month_days = self._get_number_of_days(datetime.combine(start_date, time.min), datetime.combine(pref_date_to, time.max), self.employee_id.id)
            #     print("\n---",current_month_days,"--current_month_days--\n")
            #     can_take = start_date.month - already_taken
            #     print("\n---",current_month_days.get('days'), can_take,"----\n")
            #     if can_take < current_month_days.get('days') :
            #         if can_take <= 0:
            #             raise UserError(_("You have exceeded the maximum allowed leave for the current month."))
            #         else:
            #             raise UserError(_("You have only %s days remaining for the current month." % can_take))
            #     # Suffix month availability check
            #     suf_date_from = date_end.replace(day=1)
            #     suf_date_to = date_end
            #     already_taken = sum(self.env['hr.leave'].search(
            #         [('holiday_status_id', '=', holiday_status_id.id), ('request_date_from', '>=', suf_date_from),
            #          ('request_date_to', '<=', suf_date_to), ('state', '=', 'validate')]).mapped('number_of_days'))
            #     current_month_days = self._get_number_of_days(datetime.combine(suf_date_from, time.min),
            #                                                   datetime.combine(suf_date_to, time.max),
            #                                                   self.employee_id.id)
            #     print("\n---", current_month_days, "--current_month_days-suffix--\n")
            #     can_take = start_date.month - already_taken
            #     if can_take < current_month_days.get('days'):
            #         if can_take <= 0:
            #             raise UserError(_("You have exceeded the maximum allowed leave for the current month."))
            #         else:
            #             raise UserError(_("You have only %s days remaining for the current month." % can_take))


    @api.depends('holiday_status_id')
    def _compute_state(self):
        res = super(HolidaysRequest, self)._compute_state()
        for leave in self:
            leave.state = 'draft'
        return res

    @api.model
    def default_get(self, fields_list):
        defaults = super(HolidaysRequest, self).default_get(fields_list)
        defaults['state'] = 'draft'
        return defaults

    @api.model
    def create(self, vals):
        employee_id = self.env['hr.employee'].browse(vals['employee_id'])
        holiday_status_id = self.env['hr.leave.type'].browse(vals['holiday_status_id'])
        request_date_from = vals['request_date_from'] or fields.Datetime.from_string(str(vals['date_from'])).date()
        request_date_to = vals['request_date_to'] or fields.Datetime.from_string(str(vals['date_to'])).date()
        days = vals['number_of_days'] if 'number_of_days' in vals else self.number_of_days or 0
        self.check_eligible_date(employee_id, request_date_from, request_date_to, days, holiday_status_id)
        res = super(HolidaysRequest, self).create(vals)
        vals['state'] = 'draft'
        return res

    def write(self, vals):
        if 'employee_id' in vals or 'request_date_from' in vals or 'request_date_to' in vals or 'holiday_status_id' in vals or 'number_of_days' in vals:
            employee_id = self.env['hr.employee'].browse(vals['employee_id']) if 'employee_id' in vals else self.employee_id
            self.check_eligible_date(employee_id, self.request_date_from, self.request_date_to, self.number_of_days, self.holiday_status_id)

            start_date = vals['request_date_from'] if 'request_date_from' in vals else self.request_date_from
            end_date = vals['request_date_to'] if 'request_date_to' in vals else self.request_date_to
            days = vals['number_of_days'] if 'number_of_days' in vals else self.number_of_days
            self.check_eligible_date(self.employee_id, start_date, end_date, days, self.holiday_status_id)

            holiday_status_id = self.env['hr.leave.type'].browse(vals['holiday_status_id']) if 'holiday_status_id' in vals else self.holiday_status_id
            self.check_eligible_date(self.employee_id, self.request_date_from, self.request_date_to, self.number_of_days, holiday_status_id)
        return super(HolidaysRequest, self).write(vals)

    def unlink(self):
        if self.state not in ['draft']:
            raise UserError(_("You cannot delete the leave request after submitting."))
        return super(HolidaysRequest, self).unlink()

    def action_confirm(self):
        for holiday in self:
            if holiday.holiday_status_id.maximum_days and holiday.number_of_days > holiday.holiday_status_id.maximum_days:
                raise UserError(
                    _("You could not request leave for more than %s days" % holiday.holiday_status_id.maximum_days))
            if holiday.holiday_status_id.minimum_days and holiday.number_of_days < holiday.holiday_status_id.minimum_days:
                raise UserError(
                    _("You could not request leave for less than %s days" % holiday.holiday_status_id.minimum_days))
        return super(HolidaysRequest, self).action_confirm()

    def action_cancel_request(self):
        if not self.state == 'validate':
            raise UserError(_("The leave should be in approved..!"))
        requests = self.env['hr.leave.cancel'].search([('leave_id', '=', self.id), ('state', '!=', 'cancel')])
        if requests:
            raise UserError(_("Cancel request already exist for this leave..!"))
        self.env['hr.leave.cancel'].create({
            'leave_id': self.id,
            'employee_id': self.employee_id.id,
            'date_from': self.request_date_from,
            'date_to': self.request_date_to,
        })
        action = self.env.ref('hr_holidays_extended.hr_leave_cancel_action').read()[0]
        action['domain'] = [('leave_id', '=', self.id)]
        action['context'] = {'default_leave_id': self.id, 'create': 0}
        return action

    def action_validate(self):
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))
        if self.employee_id.user_id.id == self.env.user.id:
            raise ValidationError("You cannot approve your own leave.")
        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            holiday.message_post(
                body=_('Your %s planned on %s has been accepted') % (
                holiday.holiday_status_id.display_name, holiday.date_from),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)

            if holiday.holiday_status_id.maximum_days and holiday.number_of_days > holiday.holiday_status_id.maximum_days:
                raise UserError(
                    _("Current leave type cannot approved for more than %s days" % holiday.holiday_status_id.maximum_days))
            if holiday.holiday_status_id.minimum_days and holiday.number_of_days < holiday.holiday_status_id.minimum_days:
                raise UserError(
                    _("Current leave type cannot approved for less than %s days" % holiday.holiday_status_id.minimum_days))
        if self.is_casual and self.comp_holiday_status_id:
            raise ValidationError(
                _('Enter the no.of days for %s') % self.comp_holiday_status_id.name)
        res = super(HolidaysRequest, self).action_validate()
        if self.is_manager and self.is_hod:
            if self.holiday_status_id.is_lop:
                self.action_lop_submit_to_hod()
        return res


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    expiry_date = fields.Date(string="Leave Expiry Date")
    approved_date = fields.Date("Approved Date")
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('confirm2', 'To Allocate'),
        ('refuse', 'Refused'),
        ('validate', 'Allocated')
    ], string='Status', readonly=True, tracking=True, copy=False, default='draft',
        help="The status is set to 'To Submit', when an allocation request is created." +
             "\nThe status is 'To Approve', when an allocation request is confirmed by user." +
             "\nThe status is 'Refused', when an allocation request is refused by manager." +
             "\nThe status is 'Approved', when an allocation request is approved by manager.")
    remaining_leave = fields.Float(compute='cal_remaining_leave')
    date_from = fields.Date('Start Date', index=True, copy=False, default=fields.Date.context_today, tracking=True, required=True, readonly=False)
    is_manager = fields.Boolean(compute="check_user")
    is_hod = fields.Boolean(compute="check_user")
    date_to = fields.Date('End Date', copy=False, tracking=True,states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]}, store=True, default=datetime.now().replace(day=31, month=12))

    @api.onchange('expiry_date')
    def onchange_expiry_date(self):
        if self.expiry_date:
            self.date_to = self.expiry_date

    @api.depends_context('uid')
    def _compute_description(self):
        self.check_access_rights('read')
        self.check_access_rule('read')

        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')

        for allocation in self:
            if is_officer or allocation.employee_id.user_id == self.env.user or allocation.employee_id.leave_manager_id == self.env.user or allocation.employee_id.department_id.head_of_department.user_id == self.env.user:
                allocation.name = allocation.sudo().private_name
            else:
                allocation.name = '*****'

    @api.onchange('holiday_status_id', 'date_from')
    def _onchange_date1(self):
            if self.holiday_status_id.expiry_days > 0:
                self.date_to = self.date_from + timedelta(days=self.holiday_status_id.expiry_days)
            else:
                self.date_to = datetime.now().replace(day=31, month=12)

    def check_user(self):
        for rec in self:
            rec.is_manager = False
            rec.is_hod = False
            if (rec.employee_id.parent_id.user_id.id == self.env.user.id) and (rec.employee_id.department_id.head_of_department.user_id.id == self.env.user.id):
                rec.is_manager = True
                rec.is_hod = True
            elif rec.employee_id.parent_id.user_id.id == self.env.user.id:
                rec.is_manager = True
                rec.is_hod = False
            elif rec.employee_id.department_id.head_of_department.user_id.id == self.env.user.id:
                rec.is_manager = False
                rec.is_hod = True
            else:
                rec.is_manager = False
                rec.is_hod = False

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return
        current_employee = self.env.user.employee_id
        if not current_employee:
            return
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        for holiday in self:
            val_type = holiday.holiday_status_id.sudo().allocation_validation_type
            if state == 'confirm':
                continue

            if state == 'draft':
                if holiday.employee_id != current_employee and not is_manager:
                    raise UserError(_('Only a time off Manager can reset other people allocation.'))
                continue

            # if not is_officer and self.env.user != holiday.employee_id.leave_manager_id and not val_type == 'no':
            #     raise UserError(
            #         _('Only a time off Officer/Responsible or Manager can approve or refuse time off requests.'))

            if is_officer or self.env.user == holiday.employee_id.leave_manager_id:
                # use ir.rule based first access check: department, members, ... (see security.xml)
                holiday.check_access_rule('write')

            if holiday.employee_id == current_employee and not is_manager and not val_type == 'no':
                raise UserError(_('Only a time off Manager can approve its own requests.'))

            if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager'):
                if self.env.user == holiday.employee_id.leave_manager_id and self.env.user != holiday.employee_id.user_id:
                    continue
                manager = holiday.employee_id.parent_id or holiday.employee_id.department_id.manager_id
                if (manager != current_employee) and not is_manager:
                    raise UserError(
                        _('You must be either %s\'s manager or time off manager to approve this time off') % (
                            holiday.employee_id.name))

            if state == 'validate' and val_type == 'both':
                if not is_officer:
                    raise UserError(_('Only a Time off Approver can apply the second approval on allocation requests.'))


    @api.model
    def _check_leave_expiry(self):
        current_date = datetime.now().date()
        allocation_obj = self.env['hr.leave.allocation'].search(
            [('state', '=', 'validate'), ('expiry_date', '<', current_date)])
        for rec in allocation_obj:
            rec.write({'state': 'cancel'})

    def get_mail_approval_url(self):
        action_id = self.env.ref('hr_holidays.hr_leave_allocation_action_approve_department', raise_if_not_found = False)
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s&action=%s' % (self.id, self._name, action_id.id)
        return url

    def get_mail_url(self):
        action_id = self.env.ref('hr_holidays.hr_leave_allocation_action_my', raise_if_not_found=False)
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s&action=%s' % (self.id, self._name, action_id.id)
        return url

    # def action_confirm(self):
    #     res = super(HolidaysAllocation, self).action_confirm()
    #     if self.validation_type in ['manager', 'manager_hod']:
    #         manager = self.employee_id.parent_id.work_email
    #         subject = "Allocation Request"
    #         body = """<p>Dear Sir/Ma'am,</p>
    #                           <br/>
    #                           <p>Kindly approve the allocation request of %s</p>
    #                         <center>
    #                             <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Leave</a>
    #                             <br/><br/><br/>
    #                         </center>""" % (self.employee_id.name, self.get_mail_approval_url())
    #         template_data = {
    #             'subject': subject,
    #             'body_html': body,
    #             'email_to': manager,
    #             'email_cc': self.env.user.company_id.probation_hr_mail,
    #         }
    #         template_id = self.env['mail.mail'].sudo().create(template_data)
    #         template_id.sudo().send()
    #     return res


    def action_validate(self):
        for holiday in self:
            # holiday.write({'state': 'validate'})
            holiday._action_validate_create_childs()
            holiday.approved_date = datetime.now().date()
            if holiday.holiday_status_id.expiry_days:
                holiday.expiry_date = holiday.approved_date + timedelta(days=holiday.holiday_status_id.expiry_days)
        self.activity_update()
        if self.validation_type == 'officer':
            self.write({'state': 'validate'})
            self.action_validate_email_to_emp()
        elif self.is_manager and self.validation_type == 'manager':
            self.write({'state': 'validate'})
            self.action_validate_email_to_emp()
        elif (self.is_manager and self.is_hod) or (self.employee_id.user_id.id == self.employee_id.department_id.head_of_department.user_id.id):
            self.write({'state': 'validate'})
            self.action_validate_email_to_emp()
        elif self.is_manager and not self.is_hod and self.validation_type == 'manager_hod':
            self.write({'state': 'confirm2'})
            manager = self.employee_id.parent_id.work_email
            hod = self.employee_id.department_id.head_of_department.work_email
            subject = "Allocation Request"
            body = """<p>Dear Sir/Ma'am,</p>
                          <br/>
                          <p>Kindly Approve/Refuse the allocation request.</p>
                        <center>
                            <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Leave</a>
                            <br/><br/><br/>
                        </center>""" % (self.get_mail_approval_url())
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': manager if manager else self.env.user.login,
                'email_to': hod if hod else '',
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
        return True

    def action_hod_validate(self):
        if self.is_hod and not self.is_manager and self.validation_type == 'manager_hod':
            self.write({'state': 'validate'})
            self.action_validate_email_to_emp()

    def action_validate_email_to_emp(self):
        # manager = self.employee_id.parent_id.work_email
        # hod = self.employee_id.department_id.head_of_department.work_email
        subject = 'Allocation Confirmed'
        body = ''
        if self.holiday_status_id.employee_requests == 'yes':
            body += """<p>Dear %s,</p>
                          <br/>
                          <p>Requested allocation is approved. Allocation expiry date is on: <b>%s</b>.</p>
                        <center>
                            <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Leave</a>
                            <br/><br/><br/>
                        </center>""" % (
                self.employee_id.name, self.expiry_date.strftime('%d-%m-%Y'), self.get_mail_url())
        else:
            body += """<p>Dear %s,</p>
                      <br/>
                      <p>Your allocation for %s is approved.</p>
                    <center>
                        <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Leave</a>
                        <br/><br/><br/>
                    </center>""" % (
                        self.employee_id.name, self.holiday_status_id.name, self.get_mail_url())
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.login,
            'email_to': self.employee_id.work_email,
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['confirm', 'validate', 'validate1'] for holiday in self):
            raise UserError(_('Allocation request must be confirmed or validated in order to refuse it.'))

        self.write({'state': 'refuse', 'approver_id': current_employee.id})
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()
        self.activity_update()
        res = super(HolidaysAllocation, self).action_refuse()
        subject = 'Allocation Refused'
        body = """<p>Dear %s,</p>
                              <br/>
                              <p>Requested allocation is refused. Please contact HR.</p>
                            <center>
                                <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Leave</a>
                                <br/><br/><br/>
                            </center>""" % (
            self.employee_id.name, self.get_mail_url())
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.login,
            'email_to': self.employee_id.work_email,
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        return res

    @api.depends('holiday_status_id')
    def cal_remaining_leave(self):
        for rec in self:
            rec.remaining_leave = rec.number_of_days_display - rec.leaves_taken

    @api.model
    def _reset_leave(self):
        current_date = fields.Date.today()
        before_year = current_date - relativedelta(years=1)
        month = current_date.strftime('%b')
        day = current_date.strftime('%d')
        # for leave_type in self.env['hr.leave.type'].search([('reset', '=', True), ('reset_leave_month', '=', month), ('reset_leave_days', '=', day)]):
        #     existing_allocations = self.env['hr.leave.allocation'].search([('employee_id', '!=', False), ('holiday_status_id', '=', leave_type.id), ('state', '=', 'validate')])
        #     for alloc in existing_allocations:
        #         alloc.write({'state': 'cancel'})
        #     employees = []
        #     if leave_type.reset_based_on == 'join':
        #         employees += self.env['hr.employee'].search([('date_join', '<=', before_year), ('confirm_date', '<=', fields.Date.today())])
        #     elif leave_type.reset_based_on == 'confirm' or not leave_type.reset_based_on:
        #         employees += self.env['hr.employee'].search([('confirm_date', '<=', fields.Date.today())])
        #     if leave_type.carry_forward:
        #         for emp in employees:
        #             number_of_days = 0
        #             remaining_days = 0
        #             old_allocation = existing_allocations.filtered(lambda x: x.employee_id.id == emp.id)
        #             if old_allocation:
        #                 remaining_days += sum(old_allocation.mapped('number_of_days')) - sum(old_allocation.mapped('leaves_taken'))
        #             if remaining_days and (remaining_days + leave_type.reset_days >= leave_type.maximum_limit_days):
        #                 number_of_days = leave_type.maximum_limit_days
        #             elif remaining_days:
        #                 number_of_days = remaining_days + leave_type.reset_days
        #             else:
        #                 number_of_days = leave_type.reset_days
        #             allocation_obj = self.env['hr.leave.allocation'].create({
        #                 'name': "Auto Allocation of %s" % leave_type.name,
        #                 'holiday_type': 'employee',
        #                 'holiday_status_id': leave_type.id,
        #                 'date_from': current_date,
        #                 'date_to': current_date + relativedelta(months=12),
        #                 'number_of_days': number_of_days,
        #                 'employee_id': emp.id,
        #                 'allocation_type': 'regular',
        #             })
        #             if allocation_obj:
        #                 allocation_obj.action_confirm()
        #                 allocation_obj.action_validate()
        #     else:
        #         for emp in employees:
        #             allocation_obj = self.env['hr.leave.allocation'].create({
        #                 'name': "Auto Allocation of %s" % leave_type.name,
        #                 'holiday_type': 'employee',
        #                 'holiday_status_id': leave_type.id,
        #                 'date_from': current_date,
        #                 'date_to': current_date + relativedelta(months=12),
        #                 'number_of_days': leave_type.reset_days,
        #                 'employee_id': emp.id,
        #                 'allocation_type': 'regular',
        #             })
        #             if allocation_obj:
        #                 allocation_obj.action_confirm()
        #                 allocation_obj.action_validate()
        for leave_type in self.env['hr.leave.type'].search([('reset', '=', 'True')]):
            leave_months = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6, Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)
            not_allocated_employees = []
            if leave_type.reset_based_on == 'join':
                for employee in self.env['hr.employee'].search([('date_join', '<=', before_year), ('confirm_date', '<=', fields.Date.today())]):
                    current_year_allocations = self.env['hr.leave.allocation'].search([('employee_id', '=', employee.id), ('holiday_status_id', '=', leave_type.id), ('state', '=', 'validate'),
                                                                              ('date_from', '>=', current_date.replace(day=leave_type.reset_leave_days, month=leave_months[leave_type.reset_leave_month]))])
                    if not current_year_allocations:
                        not_allocated_employees.append(employee)
            elif leave_type.reset_based_on == 'confirm':
                for employee in self.env['hr.employee'].search([('confirm_date', '<=', fields.Date.today())]):
                    current_year_allocations = self.env['hr.leave.allocation'].search([('employee_id', '=', employee.id), ('holiday_status_id', '=', leave_type.id), ('state', '=', 'validate'),
                                                                              ('date_from', '>=', current_date.replace(day=leave_type.reset_leave_days, month=leave_months[leave_type.reset_leave_month]))  ])
                    if not current_year_allocations:
                        not_allocated_employees.append(employee)
            if leave_type.carry_forward:
                for empl in not_allocated_employees:
                    number_of_days = 0
                    remaining_days = 0
                    old_allocation = self.env['hr.leave.allocation'].search([('employee_id', '=', empl.id), ('holiday_status_id', '=', leave_type.id), ('state', '=', 'validate')])
                    if old_allocation:
                        remaining_days += sum(old_allocation.mapped('number_of_days')) - sum(old_allocation.mapped('leaves_taken'))
                    if remaining_days and (remaining_days + leave_type.reset_days >= leave_type.maximum_limit_days):
                        number_of_days = leave_type.maximum_limit_days
                    elif remaining_days:
                        number_of_days = remaining_days + leave_type.reset_days
                    else:
                        number_of_days = leave_type.reset_days
                    for allocation in old_allocation:
                        allocation.write({'state': 'cancel'})
                    allocation_obj = self.env['hr.leave.allocation'].create({
                        'name': "Auto Allocation of %s" % leave_type.name,
                        'holiday_type': 'employee',
                        'holiday_status_id': leave_type.id,
                        'date_from': current_date,
                        'date_to': current_date + relativedelta(months=12),
                        'number_of_days': number_of_days,
                        'employee_id': empl.id,
                        'allocation_type': 'regular',
                    })
                    if allocation_obj:
                        allocation_obj.action_confirm()
                        allocation_obj.action_validate()
            else:
                for empl in not_allocated_employees:
                    old_allocation = self.env['hr.leave.allocation'].search([('employee_id', '=', empl.id), ('holiday_status_id', '=', leave_type.id), ('state', '=', 'validate')])
                    for allocation in old_allocation:
                        allocation.write({'state': 'cancel'})
                    allocation_obj = self.env['hr.leave.allocation'].create({
                        'name': "Auto Allocation of %s" % leave_type.name,
                        'holiday_type': 'employee',
                        'holiday_status_id': leave_type.id,
                        'date_from': current_date,
                        'date_to': current_date + relativedelta(months=12),
                        'number_of_days': round((12 - empl.confirm_date.month) * (leave_type.reset_days/12)) if empl.confirm_date.year == current_date.year else leave_type.reset_days,
                        'employee_id': empl.id,
                        'allocation_type': 'regular',
                    })
                    if allocation_obj:
                        allocation_obj.action_confirm()
                        allocation_obj.action_validate()

    @api.model
    def _auto_allocation_leave(self):
        current_date = fields.Date.today()
        before_year = current_date - relativedelta(years=1)
        year_end = current_date.replace(day=31, month=12)
        for leave_type in self.env['hr.leave.type'].search([('reset', '=', True), ('pro_rata_basis', '=', True)]):
            employees = []
            if leave_type.reset_based_on == 'join':
                employees_allocated = self.env['hr.leave.allocation'].search([('holiday_status_id', '=', leave_type.id)]).mapped('employee_id')
                employees += self.env['hr.employee'].search([('id', 'not in', employees_allocated.ids), ('date_join', '<=', before_year), ('confirm_date', '<=', current_date)])
                for emp in employees:
                    number_of_days = 0
                    eligible_date = emp.date_join + relativedelta(years=1)
                    if leave_type.carry_forward:
                        date_diff = relativedelta(year_end, eligible_date)
                        number_of_days += (date_diff.years * 12 + date_diff.months) * (leave_type.reset_days/12)
                    else:
                        number_of_days += round((12 - (emp.date_join + relativedelta(year=1)).month) * (leave_type.reset_days/12))
                    if number_of_days > 0:
                        allocation_obj = self.env['hr.leave.allocation'].create({
                            'name': "Auto Allocation of %s" % leave_type.name,
                            'holiday_type': 'employee',
                            'holiday_status_id': leave_type.id,
                            'date_from': current_date,
                            'date_to': current_date.replace(day=31, month=12),
                            'number_of_days': number_of_days if number_of_days <= leave_type.maximum_limit_days else leave_type.maximum_limit_days,
                            'employee_id': emp.id,
                            'allocation_type': 'regular',
                        })
                        if allocation_obj:
                            allocation_obj.action_confirm()
                            allocation_obj.action_validate()
            elif leave_type.reset_based_on == 'confirm':
                employees_allocated = self.env['hr.leave.allocation'].search([('holiday_status_id', '=', leave_type.id)]).mapped('employee_id')
                employees += self.env['hr.employee'].search([('id', 'not in', employees_allocated.ids), ('confirm_date', '<=', current_date)])
                for emp in employees:
                    number_of_days = 0
                    if leave_type.carry_forward:
                        number_of_days += (relativedelta(current_date.replace(day=31, month=12), emp.confirm_date)).months * (leave_type.reset_days/12)
                    else:
                        number_of_days = round((12 - emp.confirm_date.month) * (leave_type.reset_days/12))
                    if number_of_days > 0:
                        allocation_obj = self.env['hr.leave.allocation'].create({
                            'name': "Auto Allocation of %s" % leave_type.name,
                            'holiday_type': 'employee',
                            'holiday_status_id': leave_type.id,
                            'date_from': current_date,
                            'date_to': current_date.replace(day=31, month=12),
                            'number_of_days': number_of_days if number_of_days <= leave_type.maximum_limit_days else leave_type.maximum_limit_days,
                            'employee_id': emp.id,
                            'allocation_type': 'regular',
                        })
                        if allocation_obj:
                            allocation_obj.action_confirm()
                            allocation_obj.action_validate()


    @api.onchange('employee_id', 'holiday_status_id')
    def leave_gender_validation(self):
        if self.employee_id.gender != 'female' and self.holiday_status_id.is_maternity:
            raise ValidationError(_('You cannot apply for Maternity Leave'))

    def check_eligible_date(self, request_start_date, request_end_date, holiday_status_id):
        if self.env.user.has_group('hr_holidays_extended.group_hr_holidays_administrator'):
            return
        # todo Every validation must be written only after this line
        start_date = fields.Date.from_string(str(request_start_date))
        date_end = fields.Date.from_string(str(request_end_date))
        if holiday_status_id.eligible_within > 0:
            within_date = fields.Date.today() - timedelta(days=holiday_status_id.eligible_within)
            if start_date < within_date:
                raise UserError(_("Current allocation should be done within %s days of working." % holiday_status_id.eligible_within))

    @api.model
    def create(self, vals):
        holiday_status_id = self.env['hr.leave.type'].browse(vals['holiday_status_id'])
        request_date_from = vals['date_from']
        request_date_to = vals['date_to']
        self.check_eligible_date(request_date_from, request_date_to, holiday_status_id)
        res = super(HolidaysAllocation, self).create(vals)
        return res

    def write(self, vals):
        if 'date_from' in vals or 'date_to' in vals or 'holiday_status_id' in vals:
            start_date = vals['date_from'] if 'date_from' in vals else self.date_from
            end_date = vals['date_to'] if 'date_to' in vals else self.date_to
            self.check_eligible_date(start_date, end_date, self.holiday_status_id)
        return super(HolidaysAllocation, self).write(vals)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    reset_leave_month = fields.Selection([('Jan', 'January'), ('Feb', 'February'), ('Mar', 'March'),
                                          ('Apr', 'April'), ('May', 'May'), ('Jun', 'June'),
                                          ('Jul', 'July'), ('Aug', 'August'), ('Sep', 'September'),
                                          ('Oct', 'October'), ('Nov', 'November'), ('Dec', 'December')],
                                         string="Leave Reset Period")
    reset_leave_days = fields.Integer(string="days")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups="base.group_user", tracking=True)


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    reset_leave_month = fields.Selection([('Jan', 'January'), ('Feb', 'February'), ('Mar', 'March'),
                                          ('Apr', 'April'), ('May', 'May'), ('Jun', 'June'),
                                          ('Jul', 'July'), ('Aug', 'August'), ('Sep', 'September'),
                                          ('Oct', 'October'), ('Nov', 'November'), ('Dec', 'December')],
                                         string="Leave Reset Period")
    reset_leave_days = fields.Integer(string="days")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups="base.group_user", tracking=True)
#
#
class AdvanceLeaveNotice(models.Model):
    _name = 'advance.leave.notice'

    notice_leave_days = fields.Integer(string="Minimum No Of Days")
    notice_days = fields.Integer(string="Apply prior to(Days)")
    leave_type_id = fields.Many2one('hr.leave.type', string='Time Off Type')

    # @api.constrains('notice_leave_days')
    # def _check_ip_address(self):
    #     for record in self:
    #         if record.notice_leave_days < 3:
    #             raise ValidationError("Privilege Leave (PL) must be applied for a minimum of 3 days, so it cannot be configured for less than 3 days")



#
#
