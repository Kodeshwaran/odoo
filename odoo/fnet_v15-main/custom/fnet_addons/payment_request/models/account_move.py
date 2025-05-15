from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    cust_invoice_id = fields.Many2one('account.move', 'Customer Invoice')
    cust_invoice_partner_id = fields.Many2one('res.partner', string="Invoice Customer",related='cust_invoice_id.partner_id', store=True)
    cust_invoice_name = fields.Char(related='cust_invoice_id.name', store=True)
    cust_invoice_amount_residual = fields.Monetary(related='cust_invoice_id.amount_residual', string="Invoice Amount Due", store=True)
    bill_select = fields.Boolean('Select')
    payment_request_number = fields.Char()
    reference_1 = fields.Char("Reference")

    def payment_request(self):
        if any(bill.move_type != 'in_invoice' for bill in self):
            raise UserError(_('Please select the vendor bill only'))

        if any(bill.state != 'posted' for bill in self):
            raise UserError(_('Please choose the posted bills'))

        if any(bill.payment_state == 'paid' and 'in_payment' for bill in self):
            raise UserError(_('Please choose the unpaid bills bills'))

        # if self.filtered(lambda bill: bill.state != 'posted'):
        #     raise UserError(_('Please choose the posted bills to create payment request.'))

        matched_bills = []
        for bill in self:
            print('bill.....', bill)

            payment_request = self.env['payment.request'].search(
                [('account_move_ids', 'in', bill.id), ('state', 'in', ['finance_approval', 'md_approval'])])
            print('payment.....', payment_request)
            if payment_request:
                matched_bills.append(bill.name)
        if matched_bills:
            raise UserError(
                _('Payment request is ALREADY created for following bills. Please check.\n%s') % (matched_bills))
        self.env['payment.request'].create({'account_move_ids': self.ids})
        return True

    def un_tax_amount(self):

        bill = self.env['account.move'].browse(self._context.get('active_ids', []))
        values = json.loads(self.tax_totals_json)
        cgst_amount = 0.00
        sgst_amount = 0.00
        igst_amount = 0.00
        taxes_amount = 0.00
        debit_total = 0.00
        total_amount = 0.00
        tax_reduced = 0.00
        amount_paid = 0.00

        if values.get('groups_by_subtotal'):
            tax_amount = values.get('groups_by_subtotal')['Untaxed Amount']
            un_tax_amount = values.get('amount_untaxed')

            for l in tax_amount:
                if l.get('tax_group_name') == 'CGST':
                    cgst_amount = l.get('tax_group_amount')
                if l.get('tax_group_name') == 'SGST':
                    sgst_amount = l.get('tax_group_amount')
                if l.get('tax_group_name') == 'IGST':
                    igst_amount = l.get('tax_group_amount')
                if l.get('tax_group_name') == 'Taxes':
                    taxes_amount = l.get('tax_group_amount')
            total_amount = un_tax_amount + cgst_amount + sgst_amount + igst_amount
            tax_reduced = taxes_amount
            amount_paid = total_amount + taxes_amount + self.amount_tds
        if not values.get('groups_by_subtotal'):
            un_tax_amount = values.get('amount_untaxed')
            total_amount = un_tax_amount
            amount_paid = un_tax_amount + self.amount_tds
            tax_reduced = self.amount_tds
        if self.reversal_move_id:
            debit_total = sum(self.reversal_move_id.filtered(lambda x: x.payment_state == 'paid').mapped('amount_total_signed'))
        vals = {
            'total_amount': total_amount or 0.00,
            'tax_reduced': abs(tax_reduced) or 0.00,
            'amount_paid': amount_paid or 0.00,
            'debit_amount': debit_total or 0.00,
        }
        return vals


