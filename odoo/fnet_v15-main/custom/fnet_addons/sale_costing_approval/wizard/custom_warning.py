# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class CustomWarning(models.TransientModel):
    _name = 'cost.custom.warning'
    _description = 'Custom Warning'

    sale_costing_id = fields.Many2one('sale.costing', 'Sale Costing')

    def action_continue(self):
        active_id = self.sale_costing_id
        if active_id:
            if self.env.context.get('sale_costing'):
                sale_costing = self.env['sale.costing'].browse(active_id.id)
                if sale_costing.sale_cost_approval_rule_ids:
                    sale_costing.message_subscribe(
                        partner_ids=sale_costing.sale_cost_approval_rule_ids.mapped(
                            'users.partner_id.id'))
                    msg = _("Costing is waiting for approval.")
                    sale_costing.message_post(body=msg, subtype='mail.mt_comment')

                self.env['sale.cost.approval.history'].create({
                    'sale_costing': sale_costing.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'send_for_approval'
                })
                sale_costing.write({'send_for_approval': True, 'is_rejected': False})
        return True
