# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleOrderApprovalHistory(models.Model):
    _name = 'sale.cost.approval.history'
    _description = 'Sale Costing Approval History'
    _order = 'write_date desc'

    sale_costing = fields.Many2one('sale.costing', string='Sale Costing', ondelete='cascade')
    user = fields.Many2one('res.users')
    date = fields.Datetime()
    state = fields.Selection([
            ('send_for_approval', 'Send For Approval'),
            ('approved', 'Approved'),
            ('reject', 'Reject'),
        ])
    rejection_reason = fields.Text(string='Rejection Reason')
