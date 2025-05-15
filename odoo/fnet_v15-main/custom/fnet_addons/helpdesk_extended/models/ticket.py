import re
from datetime import datetime
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class HelpdeskCode(models.Model):
    _inherit = 'helpdesk.stage'

    code = fields.Char(string='Code', readonly=True)

class HelpdeskExtended(models.Model):
    _inherit = 'helpdesk.ticket'

    name = fields.Char(string='Subject', required=True, index=True)
    name_seq = fields.Char(string='Ticket Id', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    expected_end_date = fields.Datetime(string='Expected end date')
    state_char = fields.Char(related='stage_id.code', string="state")

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.stage_id.code == 'TS':
            if self.display_timer_stop:
                raise ValidationError("Please Stop Timer.")


    def name_get(self):
        result = []
        for ticket in self:
            result.append((ticket.id, "%s" % ticket.name))
        return result

    @api.model
    def create(self, vals):
        vals['name_seq'] = self.env['ir.sequence'].next_by_code('helpdesk.ticket.id') or _('New')
        record = super(HelpdeskExtended, self).create(vals)
        template_id = self.env.ref('helpdesk_extended.customer_mail_template')
        template_id.send_mail(record.id, force_send=True)
        return record

    @api.onchange('stage_id')
    def _check_type_value(self):
        if self.stage_id.code == 'IC' and not self.ticket_type_id:
            raise ValidationError("Please enter a Ticket Type.")
        if self.stage_id.code == 'DEV' and not self.expected_end_date:
            raise ValidationError("Please enter a expected end date .")

    def assigned_mail(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
        user_email = employee.work_email
        return user_email

    def manager_mail(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
        email = employee.parent_id.work_email
        return email

    @api.onchange('stage_id')
    def send_email(self):
        if self.stage_id.code == 'TS':
            template_id = self.env.ref('helpdesk_extended.functional_testing_mail_template')
            if template_id:
                template_id.send_mail(self.ids[0], force_send=True)
        if self.stage_id.code == 'DEV':
            template_id = self.env.ref('helpdesk_extended.development_mail_template')
            if template_id:
                template_id.send_mail(self.ids[0], force_send=True)
        if self.stage_id.code == 'COM':
            template_id = self.env.ref('helpdesk_extended.completed_mail_template')
            if template_id:
                template_id.send_mail(self.ids[0], force_send=True)

    def action_approved(self):
        push_live_stage = self.env['helpdesk.stage'].search([('code', '=', 'PL')], limit=1)
        if push_live_stage:
            self.stage_id = push_live_stage.id
        template_id = self.env.ref('helpdesk_extended.approval_mail_template')
        template_id.send_mail(self.id, force_send=True)

    def action_rejected(self):
        development_stage = self.env['helpdesk.stage'].search([('code', '=', 'DEV')], limit=1)
        if development_stage:
            self.stage_id = development_stage.id
        template_id = self.env.ref('helpdesk_extended.rejected_mail_template')
        template_id.send_mail(self.id, force_send=True)

