from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseAgreement(models.Model):
    _inherit = 'purchase.requisition'

    def get_salecost_count(self):
        for rec in self:
            rec.salecost_count = self.env['sale.costing'].search_count([('opportunity_id', '=', rec.id)])

    salecost_count = fields.Integer("Sale Costing", compute='get_salecost_count')

    def create_sale_costing(self):
        # selected_lines = self.bid_received_line.filtered(lambda x: x.valid_qoute)
        # if len(selected_lines.mapped('purchase_order_id').mapped('currency_id').ids) > 1:
        #        raise UserError(_("Please select bids with same currency."))
        #  exist = []
        #  for rec in selected_lines:
        #      if rec.requisition_line_id.id in exist:
        #          raise UserError(_("You have selected same products more than one time."))
        #      exist.append(rec.requisition_line_id.id)
        # if not selected_lines:
        #     return {
        #             'name': _('Warning'),
        #             'view_type': 'form',
        #             'view_mode': 'form',
        #             'res_model': 'sale.costing.warning',
        #             'type': 'ir.actions.act_window',
        #             'target': 'new',
        #             'context': {'default_requisition_id': self.id}
        #             }
        costing_id = self.env['sale.costing'].create({
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'pricelist_id': self.currency_id.id,
        })
        for line in self.line_ids:
            self.env['sale.cost.line'].create({
                'costing_id': costing_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.price_unit,
            })
        action = self.env.ref('sale_costing.action_sale_costing').read()[0]
        action['domain'] = [('id', '=', costing_id.id)]
        return action

    def action_view_costing(self):
        action = self.env.ref('sale_costing.action_sale_costing').read()[0]
        costing_ids = self.env['sale.costing'].search([('opportunity_id', '=', self.id)])
        if len(costing_ids) > 1:
            action['domain'] = [('opportunity_id', '=', self.id)]
        else:
            action['views'] = [(self.env.ref('sale_costing.sale_costing_form').id, 'form')]
            action['res_id'] = costing_ids.id
        return action

