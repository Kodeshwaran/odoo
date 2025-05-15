# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import json


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    margin_amount = fields.Monetary("Margin", compute='compute_margin', store=True)
    margin_currency_id = fields.Many2one('res.currency', string='Margin Currency', related="company_id.currency_id")

    @api.depends('price_subtotal')
    def compute_margin(self):
        for rec in self.filtered(lambda x: not (x.display_type or x.is_rounding_line) and x.parent_state == 'posted'):
            invoice_date = rec.move_id.invoice_date or rec.move_id.create_date.date()
            bill = rec.env['account.move'].search([('cust_invoice_id', '=', rec.move_id.id), ('state', '=', 'posted')])
            credit_note = rec.move_id.reversal_move_id.filtered(lambda x: x.state == 'posted').mapped('invoice_line_ids')
            debit_note = bill.mapped('reversal_move_id').filtered(lambda x: x.state == 'posted').mapped('invoice_line_ids')
            invoice_total = 0.0
            invoice_amount = sum(rec.env['account.move.line'].search([('exclude_from_invoice_tab', '=', False), ('move_id', '=', rec.move_id.id), ('product_id', '=', rec.product_id.id)]).mapped('price_subtotal'))
            
            if rec.currency_id.id != rec.env.company.currency_id.id:
                invoice_total += rec.currency_id._convert(invoice_amount,rec.company_id.currency_id, rec.company_id, invoice_date)
            else:
                invoice_total += invoice_amount
            bill_lines = bill.mapped('invoice_line_ids').filtered(lambda x: x.product_id.id == rec.product_id.id)
            if bill_lines:
                bill_total = 0.0
                for b in bill_lines:
                    bill_date = b.move_id.invoice_date or b.move_id.create_date.date()
                    if b.currency_id.id != b.env.company.currency_id.id:
                        bill_total += b.currency_id._convert(b.price_subtotal, rec.company_id.currency_id, rec.company_id, bill_date)
                    else:
                        bill_total += b.price_subtotal
                # bill_total = sum(bill.mapped('invoice_line_ids').filtered(lambda x: x.product_id.id == rec.product_id.id).mapped('price_subtotal'))
                if rec.product_id in credit_note.mapped('product_id') and debit_note.mapped('product_id'):
                    credit_total = 0.0
                    debit_total = 0.0
                    for c in credit_note.filtered(lambda x: x.product_id.id == rec.product_id.id):
                        credit_invoice_date = c.move_id.invoice_date or c.move_id.create_date.date()
                        if c.currency_id.id != rec.env.company.id:
                            credit_total += c.currency_id._convert(c.price_subtotal, rec.company_id.currency_id, rec.company_id, credit_invoice_date)
                        else:
                            credit_total += c.price_subtotal
                    for d in debit_note.filtered(lambda x: x.product_id.id == rec.product_id.id):
                        debit_bill_date = d.move_id.invoice_date or d.move_id.create_date.date()
                        if d.currency_id.id != rec.env.company.currency_id.id:
                            debit_total += d.currency_id._convert(d.price_subtotal, rec.company_id.currency_id, rec.company_id, debit_bill_date)
                        else:
                            debit_total += d.price_subtotal
                    # credit_total = sum(credit_note.filtered(lambda x: x.product_id.id == rec.product_id.id).mapped('price_subtotal'))
                    # debit_total = sum(debit_note.filtered(lambda x: x.product_id.id == rec.product_id.id).mapped('price_subtotal'))
                    rec.margin_amount = invoice_total - bill_total - credit_total + debit_total
                elif rec.product_id in credit_note.mapped('product_id'):
                    credit_total = 0.0
                    for c in credit_note.filtered(lambda x: x.product_id.id == rec.product_id.id):
                        credit_invoice_date = c.move_id.invoice_date or c.move_id.create_date.date()
                        if c.currency_id.id != rec.env.company.currency_id.id:
                            credit_total += c.currency_id._convert(c.price_subtotal, rec.company_id.currency_id, rec.company_id, credit_invoice_date)
                        else:
                            credit_total += c.price_subtotal
                    # credit_total = sum(credit_note.filtered(lambda x: x.product_id.id == rec.product_id.id).mapped('price_subtotal'))
                    rec.margin_amount = invoice_total - bill_total - credit_total
                elif rec.product_id in debit_note.mapped('product_id'):
                    debit_total = 0.0
                    for d in debit_note.filtered(lambda x: x.product_id.id == rec.product_id.id):
                        debit_bill_date = d.move_id.invoice_date or d.move_id.create_date.date()
                        if d.currency_id.id != rec.env.company.currency_id.id:
                            debit_total += d.currency_id._convert(d.price_subtotal, rec.company_id.currency_id, rec.company_id, debit_bill_date)
                        else:
                            debit_total += d.price_subtotal
                    # debit_total = sum(debit_note.filtered(lambda x: x.product_id.id == rec.product_id.id).mapped('price_subtotal'))
                    rec.margin_amount = invoice_total - bill_total + debit_total
                else:
                    rec.margin_amount = invoice_total - bill_total


class AccountMove(models.Model):
    _inherit = 'account.move'

    margin_currency_id = fields.Many2one('res.currency', string='Margin Currency', related="company_id.currency_id")
    margin_amount = fields.Monetary("Margin", compute='compute_margin', currency_field='margin_currency_id', store=True)
    margin_amt_percent = fields.Float("Margin (%)", compute='compute_margin', store=True, precision_digits=2)
    bills_count = fields.Integer(compute='compute_bills_count')

    def compute_bills_count(self):
        for rec in self:
            bills = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('cust_invoice_id', '=', rec.id)])
            rec.bills_count = len(bills)

    @api.depends('invoice_line_ids.margin_amount', 'sales_sub_types.margin_percent', 'state')
    def compute_margin(self):
        for rec in self.filtered(lambda x: x.state == 'posted'):
            products = rec.invoice_line_ids.mapped('product_id')
            margin_amount = 0
            for p in products:
                margin_amount += sum(rec.env['account.move.line'].search([('exclude_from_invoice_tab', '=', False), ('move_id', '=', rec.id), ('product_id', '=', p.id)], limit=1).mapped('margin_amount'))
            if rec.bills_count > 0 and margin_amount > 0:
                self.env.cr.execute("""SELECT amount_untaxed FROM account_move WHERE id='%s' """ %rec._origin.id)
                amount_untaxed = self.env.cr.dictfetchall()[0]['amount_untaxed']
                print("---", amount_untaxed, "--amount_unsdstaxed--")
                # tax_totals_json = json.loads(rec.tax_totals_json)
                # amount_untaxed = tax_totals_json['amount_untaxed']
                margin_amt_percent = (rec.margin_amount / (amount_untaxed or 1)) * 100
                rec.update({
                    'margin_amount': margin_amount,
                    'margin_amt_percent': margin_amt_percent,
                })
            elif rec.bills_count <= 0:
                self.env.cr.execute("""SELECT amount_untaxed FROM account_move WHERE id='%s' """ %rec._origin.id)
                amount_untaxed = self.env.cr.dictfetchall()[0]['amount_untaxed']
                print("---", amount_untaxed, "--amount_untaxed--")
                # tax_totals_json = json.loads(rec.tax_totals_json)
                # amount_untaxed = tax_totals_json['amount_untaxed']
                margin_amount = (amount_untaxed * (rec.sales_sub_types.margin_percent / 100))
                rec.update({
                    'margin_amount': margin_amount,
                    'margin_amt_percent': rec.sales_sub_types.margin_percent,
                })
            else:
                rec.margin_amount = 0
                rec.margin_amt_percent = 0

    def open_vendor_bill_view(self):
        return {
            'name': 'Vendor Bills',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'domain': [('cust_invoice_id', '=', self.id)],
            'context': {'create': False, 'edit': False, 'delete': False},
        }