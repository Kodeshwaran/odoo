# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_cost_approval_rule_id = fields.Many2one('sale.cost.approval.rule', string='Sale Costing Approval Rules')
    sale_cost_approval = fields.Boolean(string='Sale Cost Approval By Rule')
