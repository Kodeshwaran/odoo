# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleTypeLine(models.Model):
    _inherit = 'sale.type.line'

    margin_percent = fields.Float(string="Margin Percentage")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_create_invoice(self):
        res = super(PurchaseOrder, self).action_create_invoice()
        for rec in self.sale_id.mapped('invoice_ids').mapped('invoice_line_ids'):
            rec.compute_margin()
        return res