# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ApprovalRole(models.Model):
    _name = 'cost.approval.role'
    _description = 'Approval Role'

    name = fields.Char(required=True)


class ApprovalCategory(models.Model):
    _name = 'cost.approval.category'
    _description = 'Approval Category'

    name = fields.Char(required=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'HR Employee'

    cost_approval_role = fields.Many2many('cost.approval.role', 'cost_approval_role_hr_employee_rel', 'cost_approval_role_id', 'cost_hr_employee_id', string='Approval Role')
    sale_cost_single_approval_rule_id = fields.Many2one('sale.cost.approval.rule',
                                                        related='company_id.sale_cost_single_approval_rule_id',
                                                        string='Sale Costing Approval Rules', readonly=False)
    sale_cost_double_approval_rule_id = fields.Many2one('sale.cost.approval.rule',
                                                        related='company_id.sale_cost_double_approval_rule_id',
                                                        string='Sale Costing Approval Rules', readonly=False)
    sale_cost_approval = fields.Boolean(related='company_id.sale_cost_approval', string='Sale Cost Approval By Rule')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cost_approval_category = fields.Many2one('cost.approval.category', string='Approval Category')
    sale_cost_single_approval_rule_id = fields.Many2one('sale.cost.approval.rule',
                                                        related='company_id.sale_cost_single_approval_rule_id',
                                                        string='Sale Costing Approval Rules', readonly=False)
    sale_cost_double_approval_rule_id = fields.Many2one('sale.cost.approval.rule',
                                                        related='company_id.sale_cost_double_approval_rule_id',
                                                        string='Sale Costing Approval Rules', readonly=False)
    sale_cost_approval = fields.Boolean(related='company_id.sale_cost_approval', string='Sale Cost Approval By Rule')
