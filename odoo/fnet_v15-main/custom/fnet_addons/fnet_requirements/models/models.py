from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('amount_total', 'invoice_ids.amount_total', 'invoice_ids.amount_residual')
    def _compute_due(self):
        self.amount_paid = 0.0
        self.amount_residual = 0.0
        for rec in self:
            tot_paid_amount = 0
            due_amount = rec.amount_untaxed
            paid = rec.mapped('invoice_ids').filtered(lambda x: x.state == 'posted' and x.move_type == 'out_invoice')
            deducted = rec.mapped('invoice_ids').filtered(lambda x: x.state == 'posted' and x.move_type == 'out_refund')
            if paid or deducted:
                tot_paid_amount = sum(paid.mapped('amount_untaxed')) - sum(deducted.mapped('amount_untaxed'))
                due_amount = rec.amount_untaxed - tot_paid_amount
            rec.amount_residual = 0 if due_amount < 1 else due_amount
            rec.amount_paid = tot_paid_amount

    amount_residual = fields.Monetary(string='Amount to be Invoiced', store=True, compute='_compute_due')
    amount_paid = fields.Monetary(string='Amount Invoiced', store=True, compute='_compute_due')

    def run_compute_manually(self):
        self.search([])._compute_due()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        self.ensure_one()
        for line in self.move_ids_without_package:
            if line.quantity_done > line.product_uom_qty:
                raise UserError(_("The system could not allow done quantity more than demand."))
        return super(StockPicking, self).button_validate()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_service = fields.Boolean('Is Service')

class Partner1(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    customer_name = fields.Integer(string='Customer ID')
#
#     customer_name = fields.Integer(string='Customer ID')
#     customer_name1 = fields.Integer(related="customer_name" ,string='Customer ID1',store=True)
#     customer_name2 = fields.Integer(related="customer_name1",string='Customer ID2',store=True)


class Partner1(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    customer_name = fields.Integer(string='Customer ID')


# class SaleReport(models.Model):
#     _inherit = 'sale.report'
#
#     amount_residual = fields.Float('Amount to be Invoiced', readonly=True, store=True)
#
#     def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
#         fields['amount_residual'] = ", SUM(s.amount_residual) AS amount_residual"
#         return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
