# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    history_line = fields.One2many('salary.history.line', 'contract_id', string="History Lines")
    effective_date = fields.Date('Effective Date')


class SalaryHistoryLine(models.Model):
    _name = 'salary.history.line'

    old_basic = fields.Char('Basic Percentage')
    old_wage = fields.Float('Wages', digits=(16, 5))
    old_structure_id = fields.Many2one('hr.payroll.structure', 'Salary Structure')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    hra = fields.Float('HRA')
    travel_allowance = fields.Float('Travel Allowance')
    meal_allowance = fields.Float("Meal Allowance")
    medical = fields.Float("Medical Allowance")
    overtime_allowance = fields.Float('Overtime Allowance')
    bonus = fields.Float('Bonus')
    conveyance = fields.Float("Conveyance")
    data_allowance = fields.Float('Data Card Allowance')
    ea_allowance = fields.Float('EA Allowance')
    learning_development = fields.Float('Learning and Development')
    other = fields.Float('Other Allowance')
    tds_deduction = fields.Float('TDS')
    mobile_deduction = fields.Float('Mobile Deduction')
    other_deduction = fields.Float('Other Deduction')
    effective_date = fields.Date('Effective Date')
