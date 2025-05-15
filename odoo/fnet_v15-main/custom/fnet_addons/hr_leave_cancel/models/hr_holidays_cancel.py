# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Holidays(models.Model):

    _name = "hr.holidays.cancel"
    _description = "Leave Cancellation"
    _inherit = 'mail.thread'

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char('Description')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
        help="The status is set to 'To Submit', when a holiday cancel request is created." +
             "\nThe status is 'To Approve', when holiday cancel request is confirmed by user." +
             "\nThe status is 'Refused', when holiday request cancel is refused by manager." +
             "\nThe status is 'Approved', when holiday request cancel is approved by manager.")
    report_note = fields.Text('HR Comments')
    holiday = fields.Many2one("hr.leave", string="Leaves", required=True, domain="[('state', '=', 'validate')]")
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True, readonly=True,
                                  states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                                  default=_default_employee)
    emp_manager = fields.Many2one(string="Employee Manager", related="employee_id.parent_id")
    is_manager = fields.Boolean(string="Is Manager", compute="check_user")
    is_employee = fields.Boolean(string="Is Employee", compute="check_user")

    def check_user(self):
        for rec in self:
            if (self.env.user.id == rec.employee_id.parent_id.user_id.id) and (
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

    def action_approve(self):
        for record in self:
            record.holiday.action_refuse()
            record.write({'state': 'validate'})

    def action_refuse(self):
        for record in self:
            record.write({'state': 'refuse'})

    def action_confirm(self):
        """
        Confirm leave cancel requests and send a mail to the concerning department head.
        :return:
        """
        for record in self:
            if record.employee_id and record.employee_id.parent_id and record.employee_id.parent_id.work_email:
                vals = {
                        'email_to': record.employee_id.parent_id.work_email,
                        'subject': 'Leave Cancel Request: From {employee} , {description}'
                                    .format(employee=record.employee_id.name, description=record.name),
                        'body_html': """
                                    <p>
                                        Hello Mr/Mrs %s,
                                    </p>
                                    <p>
                                        There is a leave cancellation request on an approved leave %s
                                    </p>
                                    <div style="padding: 16px 8px 16px 8px;">
                                        <a t-att-href= "%s"
                                           style="background-color: #875a7b; text-decoration: none; color: #fff; padding: 8px 16px 8px 16px; border-radius: 5px;">
                                            View Leave Cancel Request
                                        </a>
                                    </div>
                                    <p>
                                        Thank You.
                                    </p>
                                """ % (record.employee_id.parent_id.name, record.holiday.display_name, record.get_url())}
                mail = self.env['mail.mail'].sudo().create(vals)
                mail.send()
            record.write({'state': 'confirm'})

    def get_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url