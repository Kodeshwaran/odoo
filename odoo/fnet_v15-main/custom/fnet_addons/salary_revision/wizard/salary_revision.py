# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError


class SalaryRevision(models.Model):
    _name = "salary.revision"

    basic = fields.Char('Basic Percentage')
    wage = fields.Float('Wages', digits=(16, 5))
    effective_date = fields.Date('Effective Date')
    structure_id = fields.Many2one('hr.payroll.structure', 'Payroll Structure')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    travel_allowance = fields.Float('Travel Allowance', digits=(16, 5))
    ea_allowance = fields.Float('EA Allowance', digits=(16, 5))
    data_allowance = fields.Float('Data Card Allowance', digits=(16, 5))
    overtime_allowance = fields.Float('Overtime Allowance', digits=(16, 5))
    pt = fields.Float('PT', digits=(16, 5))
    hra = fields.Float('HRA', digits=(16, 5))
    bonus = fields.Float('Bonus', digits=(16, 5))
    medical = fields.Float('Medical', digits=(16, 5))
    conveyance = fields.Float('Conveyance ', digits=(16, 5))
    other = fields.Float('Other Allowance ', digits=(16, 5))
    tds_deduction = fields.Float('TDS', digits=(16, 5))
    mobile_deduction = fields.Float('Mobile Deduction', digits=(16, 5))
    other_deduction = fields.Float('Other Deduction', digits=(16, 5))

    @api.model
    def default_get(self, fields):
        rec = super(SalaryRevision, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _("Programmation error: wizard action executed without active_model or active_ids in context."))

        # Checks on received invoice records
        contract = self.env[active_model].browse(active_ids)
        rec.update({
            'basic': contract.basic_percentage,
            'wage': contract.wage,
            'effective_date': '',
            'structure_id': contract.struct_id.id,
            'contract_id': contract.id,
        })

        return rec

    def update_salary(self):
        lines = []
        lines.append((0, 0, {
            'old_basic': self.contract_id.basic_percentage,
            'old_wage': self.contract_id.wage,
            'contract_id': self.contract_id.id,
            'old_structure_id': self.contract_id.struct_id.id,
            'travel_allowance': self.contract_id.travel_allowance,
            'ea_allowance': self.contract_id.earning_alw,
            'data_allowance': self.contract_id.data_card_alw,
            'overtime_allowance': self.contract_id.ot_allowance,
            'hra': self.contract_id.hra,
            'bonus': self.contract_id.bonus,
            'medical': self.contract_id.medical_allowance,
            'conveyance': self.contract_id.conveyance,
            'other': self.contract_id.other_allowance,
            'tds_deduction': self.contract_id.tds,
            'mobile_deduction': self.contract_id.mobile_deduction,
            'other_deduction': self.contract_id.other_deduction,
            'effective_date': self.contract_id.effective_date,
        }))
        vals = {
            'history_line': lines,
        }
        self.contract_id.write(vals)
        self.contract_id.basic_percentage = self.basic
        self.contract_id.wage = self.wage
        self.contract_id.struct_id = self.structure_id.id
        self.contract_id.effective_date = self.effective_date
        self.contract_id.travel_allowance = self.travel_allowance
        self.contract_id.earning_alw = self.ea_allowance
        self.contract_id.data_card_alw = self.data_allowance
        self.contract_id.ot_allowance = self.overtime_allowance
        self.contract_id.bonus = self.bonus
        self.contract_id.medical_allowance = self.medical
        self.contract_id.conveyance = self.conveyance
        self.contract_id.other_allowance = self.other
        self.contract_id.tds = self.tds_deduction
        self.contract_id.mobile_deduction = self.mobile_deduction
        self.contract_id.other_deduction = self.other_deduction
        self.contract_id.effective_date = self.effective_date