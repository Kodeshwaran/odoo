from odoo import models, fields, api, _


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    timesheet_cost = fields.Float("Timesheet Cost", digits=(16, 2), readonly=True, group_operator="sum")

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    resignation_count = fields.Integer(compute="_compute_resignation_count")
    no_due_count = fields.Integer(compute='_compute_no_due_count')
    exit_int_count = fields.Integer(compute='_compute_exit_int_count')
    probation_review_count = fields.Integer(compute='_compute_probation_review_count')

    def _compute_resignation_count(self):
        for rec in self:
            count = self.env['hr.resignation'].search_count([('user_id', '=', rec.user_id.id)])
            rec.resignation_count = count

    def action_open_resignation(self):
        create = {
            'name': 'Resignation Form',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hr.resignation',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        return create

    def action_open_resignation_smt_btn_in_public(self):
        return {
            'name': _("%s's Resignation") % (self.employee_id.name),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'hr.resignation',
            'domain': [('user_id', '=', self.env.uid)]
        }

    def action_view_no_due(self):
        no_due_form = self.env['no.due'].search([('name.user_id', '=', self.env.uid), ('state', '=', 'draft')], limit=1)
        return {
            'name': _('No Due'),
            'type': 'ir.actions.act_window',
            'res_model': 'no.due',
            'view_mode': 'form',
            'res_id': no_due_form.id
        }

    def _compute_no_due_count(self):
        count_no_due = self.env['no.due'].search_count([('name.user_id', '=', self.env.uid)])
        for rec in self:
            rec.no_due_count = count_no_due

    def action_view_exit_int(self):
        exit_int_form = self.env['exit.interview'].search([('name.user_id', '=', self.env.uid), ('state', '=', 'draft')], limit=1)
        return {
            'name': _('Exit Interview'),
            'type': 'ir.actions.act_window',
            'res_model': 'exit.interview',
            'view_mode': 'form',
            'res_id': exit_int_form.id
        }

    def _compute_exit_int_count(self):
        count_exit_int = self.env['exit.interview'].search_count([('name.user_id', '=', self.env.uid)])
        for rec in self:
            rec.exit_int_count = count_exit_int

    def action_view_probation_review(self):
        probation_review_form = self.env['probation.review'].search([('employee_id.user_id', '=', self.env.uid), ('state', 'not in', ['draft'])], limit=1)
        return {
            'name': _('Probation Review'),
            'type': 'ir.actions.act_window',
            'res_model': 'probation.review',
            'view_mode': 'form',
            'res_id': probation_review_form.id,
        }

    def _compute_probation_review_count(self):
        count_probation_review = self.env['probation.review'].search_count([('employee_id.user_id', '=', self.env.uid)])
        for rec in self:
            rec.probation_review_count = count_probation_review
