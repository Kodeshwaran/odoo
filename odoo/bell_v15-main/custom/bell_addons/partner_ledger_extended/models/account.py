# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        analytic_line_id = self.mapped('invoice_line_ids').mapped('analytic_account_id')
        if len(analytic_line_id) > 1:
            raise UserError(_("All invoice lines must have same analytic account"))
        return super(AccountMove, self).action_post()


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPaymentRegister, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        if active_ids:
            invoices = self.env['account.move'].browse(active_ids)
            analytic_account_id = invoices.mapped('invoice_line_ids').mapped('analytic_account_id')
            if len(analytic_account_id) > 1:
                raise UserError (_("All invoice lines must have same analytic account"))
            if analytic_account_id:
                rec.update({'analytic_account_id': analytic_account_id.id})
        return rec

    def _create_payment_vals_from_wizard(self):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        analytic_id = self.analytic_account_id
        active_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        if not analytic_id:
            analytic_id = invoices.mapped('invoice_line_ids').mapped('analytic_account_id')
        if analytic_id:
            res.update({'analytic_account_id': analytic_id.id})
        return res

    # @api.multi
    # def _prepare_payment_vals(self, invoices):
    #     res = super(account_register_payments, self)._prepare_payment_vals(invoices)
    #     analylic_id = self.analytic_account_id
    #     if not analylic_id:
    #         analylic_id = invoices.mapped('invoice_line_ids').mapped('account_analytic_id')
    #     if analylic_id:
    #         res.update({'analytic_account_id': analylic_id.id})
    #     return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        invoice_defaults = rec.get('invoice_ids')
        if invoice_defaults and invoice_defaults[0].get('id', False):
            invoices = self.env['account.invoice'].browse(invoice_defaults[0].get('id'))
            analytic_id = invoices.mapped('invoice_line_ids').mapped('analytic_account_id')
            if len(analytic_id) > 1:
                raise UserError (_("All invoice lines must have same analytic account"))
            if analytic_id:
                rec.update({'analytic_account_id': analytic_id.id})
        return rec

    def action_post(self):
        ''' draft -> posted '''
        self.move_id.line_ids.write({'analytic_account_id': self.analytic_account_id.id})
        self.move_id._post(soft=False)

        self.filtered(
            lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()

    # def action_post(self):
    #     """ Create the journal items for the payment and update the payment's state to 'posted'.
    #         A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
    #         and another in the destination reconciliable account (see _compute_destination_account_id).
    #         If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
    #         If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
    #     """
    #     for rec in self:
    #
    #         if rec.state != 'draft':
    #             raise UserError(_("Only a draft payment can be posted."))
    #
    #         if any(inv.state != 'open' for inv in rec.invoice_ids):
    #             raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
    #
    #         # keep the name in case of a payment reset to draft
    #         if not rec.name:
    #             # Use the right sequence to set the name
    #             if rec.payment_type == 'transfer':
    #                 sequence_code = 'account.payment.transfer'
    #             else:
    #                 if rec.partner_type == 'customer':
    #                     if rec.payment_type == 'inbound':
    #                         sequence_code = 'account.payment.customer.invoice'
    #                     if rec.payment_type == 'outbound':
    #                         sequence_code = 'account.payment.customer.refund'
    #                 if rec.partner_type == 'supplier':
    #                     if rec.payment_type == 'inbound':
    #                         sequence_code = 'account.payment.supplier.refund'
    #                     if rec.payment_type == 'outbound':
    #                         sequence_code = 'account.payment.supplier.invoice'
    #             rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
    #             if not rec.name and rec.payment_type != 'transfer':
    #                 raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
    #
    #         # Create the journal entry
    #         amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
    #         move = rec._create_payment_entry(amount)
    #         if rec.analytic_account_id and move.line_ids:
    #             move.line_ids.write({'analytic_account_id': rec.analytic_account_id.id})
    #         # In case of a transfer, the first journal entry created debited the source liquidity account and credited
    #         # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
    #         if rec.payment_type == 'transfer':
    #             transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
    #             transfer_debit_aml = rec._create_transfer_entry(amount)
    #             (transfer_credit_aml + transfer_debit_aml).reconcile()
    #
    #         rec.write({'state': 'posted', 'move_name': move.name})
    #     return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    analytic_name = fields.Char(compute='_compute_analytic_name', store=True)

    @api.depends('analytic_account_id')
    def _compute_analytic_name(self):
        for line in self:
            if line.analytic_account_id:
                line.analytic_name = line.analytic_account_id.name
                

class AccountingCommonPartnerReport(models.TransientModel):
    _inherit = "account.common.partner.report"
    
    result_selection = fields.Selection(selection_add=[('other', 'Other Accounts')], ondelete={'other': 'cascade'})
    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts')
    partner_ids = fields.Many2many('res.partner', string='Partners')

    def pre_print_report(self, data):
        data['form'].update(self.read(['result_selection', 'analytic_account_ids', 'partner_ids'])[0])
        return data


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.base_accounting_kit.report_partnerledger'

    # def _lines(self, data, partner):
    #     full_account = []
    #     currency = self.env['res.currency']
    #     query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
    #     reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
    #     params = [partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
    #     analytic_account_ids = []
    #     if data and data['form'] and data['form'].get('analytic_account_ids', []):
    #         analytic_account_ids = data['form'].get('analytic_account_ids')
    #     query = """
    #     SELECT "account_move_line".id, "account_move_line".date, j.code, acc.code as a_code, acc.name as a_name, "account_move_line".ref, m.name as move_name,"account_move_line".name, "account_move_line".analytic_name,  "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency,"account_move_line".currency_id, c.symbol AS currency_code
    #     FROM """ + query_get_data[0] + """
    #     LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
    #     LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
    #     LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
    #     LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
    #     WHERE "account_move_line".partner_id = %s
    #         AND m.state IN %s
    #         AND "account_move_line".account_id IN %s AND """ + query_get_data[1] + reconcile_clause + """
    #         ORDER BY "account_move_line".date"""
    #     params.append(tuple(analytic_account_ids))
    #     if query:
    #         self.env.cr.execute(query, tuple(params))
    #         res = self.env.cr.dictfetchall()
    #         sum = 0.0
    #         lang_code = self.env.context.get('lang') or 'en_US'
    #         lang = self.env['res.lang']
    #         lang_id = lang._lang_get(lang_code)
    #         date_format = lang_id.date_format
    #         for r in res:
    #             r['date'] = datetime.strptime(r['date'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
    #             r['displayed_name'] = '-'.join(
    #                 r[field_name] for field_name in ('move_name', 'ref', 'name')
    #                 if r[field_name] not in (None, '', '/')
    #             )
    #             sum += r['debit'] - r['credit']
    #             r['progress'] = sum
    #             r['currency_id'] = currency.browse(r.get('currency_id'))
    #             full_account.append(r)
    #     return full_account

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        data['computed'] = {}
        context_rep = data['form'].get('used_context', {})
        analytic_account_ids = self.env['account.analytic.account']
        if data and data['form'] and data['form'].get('analytic_account_ids', []):
            analytic_account_ids = self.env['account.analytic.account'].browse(data['form'].get('analytic_account_ids'))
        context_rep.update({'analytic_account_ids': analytic_account_ids})
        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(context_rep)._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
        elif result_selection == 'customer_supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable', 'other', 'liquidity']
        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.internal_type IN %s
            AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        if data['form']['partner_ids']:
            partner_ids = data['form']['partner_ids']
        else:
            partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        # partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        if not partner_ids:
            raise UserError(_('Nothing to print. may be condition not satisfied'))
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))
        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
        }
