# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SaleOrderApprovalRule(models.Model):
    _name = 'sale.order.approval.rule'
    _description = 'Sale Order Approval Rule'

    name = fields.Char(required=True)
    minimum_approval = fields.Integer('Minimum Approval Amount')
    maximum_approval = fields.Integer('Maximum Approval Amount')
    approval_rule_ids = fields.One2many('sale.order.approval.rule.lines', 'approval_rule_id', string='Approval Rule Lines')


class SaleConfigApprovalRules(models.Model):
    _name = 'sale.order.approval.rule.lines'
    _description = 'Sale Config Approval Rules'

    approval_rule_id = fields.Many2one('sale.order.approval.rule')
    sequence = fields.Integer(string='Sequence', required=True)
    approval_role = fields.Many2one('approval.role', string='Approval Role', required=True)
    approval_category = fields.Many2one('approval.category.knk', string='Approval Category')
    email_template = fields.Many2one('mail.template', string='Mail Template')
    quotation_lower_limit = fields.Float(string="Lower Limit", required=True)
    quotation_upper_limit = fields.Float(string="Upper Limit", required=True)


    # @api.constrains('quotation_upper_limit')
    # def _constrains_reconcile(self):
    #     for record in self:
    #         if record.quotation_upper_limit <= record.quotation_lower_limit and record.quotation_upper_limit != -1:
    #             raise UserError(_('An Upper limit must be grater then lower limit'))
