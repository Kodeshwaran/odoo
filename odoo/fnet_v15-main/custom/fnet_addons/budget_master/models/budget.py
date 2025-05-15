# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DepartmentBudget(models.Model):
    _name = 'department.budget'
    _description = 'Department Budget'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char('Name', required=True, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting for Approval'),
                              ('first_approve', 'Finance Approved'), ('cancel', 'Rejected')], default='draft', tracking=True)
    date_from = fields.Date(string='Date From', required=True, copy=False)
    date_to = fields.Date(string='Date To', required=True, copy=False)
    budget_lines = fields.One2many('department.budget.line', 'budget_id', string="Budget Lines")

    def submit(self):
        if not self.budget_lines:
            raise UserError(_("Add the Budget Lines before submitting..!"))
        self.write({'state': 'waiting'})

    def first_approve(self):
        self.write({'state': 'first_approve'})

    # def second_approve(self):
    #     self.write({'state': 'second_approve'})

    def cancel(self):
        self.write({'state': 'cancel'})

    def reset(self):
        self.write({'state': 'draft'})


class DepartmentBudgetLines(models.Model):
    _name = 'department.budget.line'
    _description = "Budget Lines"

    budget_id = fields.Many2one('department.budget', string="Budget ID")
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    payslip_ids = fields.One2many('hr.payslip', 'budget_line_id', string="Payslips")
    expected_value = fields.Float('Expected Budget')
    remaining_value = fields.Float('Remaining Budget', compute="compute_remaining_value")
    actual_value = fields.Float('Actual Expense', compute="compute_actual_value")

    @api.depends('expected_value', 'actual_value')
    def compute_remaining_value(self):
        for line in self:
            line.remaining_value = line.expected_value - line.actual_value

    @api.depends('payslip_ids')
    def compute_actual_value(self):
        for line in self:
            line.actual_value = sum(line.payslip_ids.mapped('line_ids').filtered(lambda x: x.code == 'NET').mapped('total'))
