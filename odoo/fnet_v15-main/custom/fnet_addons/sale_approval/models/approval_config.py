# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ApprovalRole(models.Model):
    _name = 'approval.role'
    _description = 'Approval Role'

    name = fields.Char(required=True)


class ApprovalCategory(models.Model):
    _name = 'approval.category.knk'
    _description = 'Approval Category'

    name = fields.Char(required=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'HR Employee'

    approval_role = fields.Many2many('approval.role', 'approval_role_hr_employee_rel', 'approval_role_id', 'hr_employee_id', string='Approval Role')
    sale_order_approval_rule_id = fields.Many2one('sale.order.approval.rule', related='company_id.sale_order_approval_rule_id', string='Sale Order Approval Rules')
    sale_order_approval = fields.Boolean(related='company_id.sale_order_approval', string='Sale Order Approval By Rule')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    approval_category = fields.Many2one('approval.category.knk', string='Approval Category')
    sale_order_approval_rule_id = fields.Many2one('sale.order.approval.rule', related='company_id.sale_order_approval_rule_id', string='Sale Order Approval Rules')
    sale_order_approval = fields.Boolean(related='company_id.sale_order_approval', string='Sale Order Approval By Rule')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'
    _description = 'HR Employee Public'

    approval_role = fields.Many2many('approval.role', 'approval_role_hr_employee_rel', 'approval_role_id', 'hr_employee_id', string='Approval Role')
    sale_order_approval_rule_id = fields.Many2one('sale.order.approval.rule', related='company_id.sale_order_approval_rule_id', string='Sale Order Approval Rules')
    sale_order_approval = fields.Boolean(related='company_id.sale_order_approval', string='Sale Order Approval By Rule')

