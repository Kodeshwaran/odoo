from odoo import models, fields, api, _


class PurchaseAgreement(models.Model):
    _inherit = 'purchase.requisition'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order',
                                    domain="[('tender_id', '=', id)]")

    sale_no = fields.Char(
        'File No',
        copy=False,
        default=lambda self: _('New'),
        compute='_compute_sale_no',
    )

    def _compute_sale_no(self):
        for record in self:
            search =  self.env['sale.order'].search([('tender_id', '=', self.id)], limit=1)
            if search:
                record.sale_no = search.sale_no
            else:
                record.sale_no = False

    def get_salecost_count(self):
        for rec in self:
            rec.salecost_count = self.env['sale.costing'].search_count([('agreement_id', '=', rec.id)])

    salecost_count = fields.Integer("Sale Costing", compute='get_salecost_count')

    def create_sale_costing(self):
        costing_id = self.env['sale.costing'].create({
            'agreement_id': self.id,
            'partner_id': self.customer_id.id,
            'currency_id': self.currency_id.id,
        })
        for line in self.line_ids:
            self.env['sale.cost.line'].create({
                'costing_id': costing_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.price_unit,
            })
        action = self.env.ref('sale_costing.action_sale_costing').sudo().read()[0]
        action['domain'] = [('id', '=', costing_id.id)]
        return action

    def action_view_costing(self):
        action = self.env.ref('sale_costing.action_sale_costing').sudo().read()[0]
        costing_ids = self.env['sale.costing'].search([('agreement_id', '=', self.id)])
        if len(costing_ids) > 1:
            action['domain'] = [('agreement_id', '=', self.id)]
        else:
            action['views'] = [(self.env.ref('sale_costing.sale_costing_form').id, 'form')]
            action['res_id'] = costing_ids.id
        return action


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_no = fields.Char(
        'File No',related='requisition_id.sale_no'

    )