# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta, time, datetime, timedelta, date


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    budget_lines = fields.One2many('employee.budget.line', 'employee_id', string='Budget Lines', copy=False, domain=[('date_from', '<=', datetime.now().date()), ('date_to', '>=', datetime.now().date())])

    # @api.constrains('budget_lines')
    # def budget_line_constrain(self):
    #     for rec in self:
    #         budget_sum = self.env['employee.budget.line'].search([('employee_id', '=', rec.id)]).mapped('percentage')
    #         if budget_sum and sum(budget_sum) != 1:
    #             raise UserError('Budget Percentage must sum upto 100')

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        if 'budget_lines' in vals and not vals['budget_lines'] and vals['department_id']:
            budget = self.env['employee.budget'].search([('date_from', '<=', fields.Date.today()), ('date_to', '>=', fields.Date.today())], limit=1)
            values = {
                'employee_id': res['id'],
                'budget_id': budget.id if budget else False,
                'department_id': res['department_id'].id,
                'percentage': 1,
            }
            self.env['employee.budget.line'].create(values)
        return res

    def write(self, vals):
        if 'department_id' in vals and not vals.get('department_id'):
            self.budget_lines.unlink()
        if 'department_id' in vals and vals.get('department_id'):
            self.budget_lines.unlink()
            budget = self.env['employee.budget'].search([('date_from', '<=', fields.Date.today()), ('date_to', '>=', fields.Date.today())], limit=1)
            values = {
                'employee_id': self.id,
                'budget_id': budget.id if budget else False,
                'department_id': vals.get('department_id'),
                'percentage': 1,
            }
            self.env['employee.budget.line'].create(values)
        return super(HrEmployee, self).write(vals)
