# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_order_approval_rule_id = fields.Many2one('sale.order.approval.rule', string='Sale Order Approval Rules')
    sale_order_approval = fields.Boolean(string='Sale Order Approval By Rule')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_approval_rule_id = fields.Many2one('sale.order.approval.rule', related='company_id.sale_order_approval_rule_id', string='Sale Order Approval Rules', readonly=False)
    sale_order_approval = fields.Boolean(related='company_id.sale_order_approval', string='Sale Order Approval By Rule', readonly=False)