from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_count = fields.Integer(string='# of Quote', compute='_get_purchase', readonly=True)

    def _get_purchase(self):
        for rec in self:
            purchase_order_search = self.env['purchase.order'].search(
                [('sale_id', '=', rec.id)])
            rec.update({
                'purchase_count': len(set(purchase_order_search)),
            })

    @api.multi
    def action_view_purchase(self):
        sale_order_search = self.env['purchase.order'].search(
            [('sale_id', '=', self.id)]).ids
        if len(sale_order_search) < 1:
            pass
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'View Purchase',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order',
                'nodestroy': True,
                'res_id': sale_order_search[0],
                'domain': [('id', 'in', sale_order_search)],
                'target': 'current',
            }

    def action_set_to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
