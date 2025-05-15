# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EmployeeBudgetLine(models.Model):
    _name = 'employee.budget'
    _description = 'Employee Budget'
    _rec_name = 'name'

    name = fields.Char(string='Description', required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    state = fields.Selection([('draft', 'Draft'), ('budget_computed', 'Budget Computed')], string='Status', default='draft')

    def compute_employee_line(self):
        if not self.employee_ids:
            raise ValidationError('Select atleast one Employee to generate budget lines')
        else:
            budget_lines = self.env['employee.budget.line'].search([('budget_id', '=', self.id)])
            for line in budget_lines:
                line.unlink()
            for emp in self.employee_ids:
                vals = {
                    'employee_id': emp.id,
                    'budget_id': self.id,
                    'department_id': emp.department_id.id,
                    'percentage': 1,
                }
                self.env['employee.budget.line'].create(vals)
            self.write({'state': 'budget_computed'})

    def reset_to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def view_employee_budget(self):
        return {
            'name': _('Employee Budget'),
            'type': 'ir.actions.act_window',
            'res_model': 'employee.budget.line',
            'view_mode': 'tree,form',
            'domain': [('budget_id', '=', self.id)],
            'context': {
                'default_budget_id': self.id,
                'search_default_department': 1,
                'search_default_employee': 1,
                        }
        }


class DepartmentBudgetLine(models.Model):
    _name = 'employee.budget.line'
    _description = 'Budget Lines'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    budget_id = fields.Many2one('employee.budget', string='Budget')
    date_from = fields.Date(string='Date From', related='budget_id.date_from')
    date_to = fields.Date(string='Date To', related='budget_id.date_to')
    department_id = fields.Many2one('hr.department', string="Department")
    percentage = fields.Float(string="Percentage")

    @api.constrains('percentage')
    def percentage_constrain(self):
        for rec in self:
            if rec.percentage == 0:
                raise UserError("Percentage must not be 0")
            budget_sum = self.env['employee.budget.line'].search([('employee_id', '=', rec.employee_id.id), ('budget_id', '=', rec.budget_id.id)]).mapped('percentage')
            if budget_sum and sum(budget_sum) > 1:
                raise UserError('Budget Percentage must sum upto 100')
