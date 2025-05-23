# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseOrderApprovalHistory(models.Model):
    _name = 'purchase.order.approval.history'
    _description = 'Purchase Order Approval History'
    _order = 'write_date desc'

    purchase_order = fields.Many2one('purchase.order', string='Purchase Order', ondelete='cascade')
    user = fields.Many2one('res.users')
    date = fields.Datetime()
    state = fields.Selection([
            ('send_for_approval', 'Send For Approval'),
            ('approved', 'Approved'),
            ('reject', 'Reject'),
        ])
    rejection_reason = fields.Text(string='Rejection Reason')
