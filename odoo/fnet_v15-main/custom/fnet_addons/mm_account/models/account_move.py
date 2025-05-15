# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

import tempfile
import binascii
import base64
import io
import os

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import format_date


from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class AccountMove(models.Model):
    _inherit = "account.move"

    apply_tds = fields.Boolean(string='Apply TCS', default=False, readonly=True,
                               states={'draft': [('readonly', False)]})
    tds_ids = fields.Many2one('account.tax', string='TCS',
                              states={'draft': [('readonly', False)]})
    tds_added = fields.Monetary(string='TCS Amount added',
                                store=True, readonly=True, compute='_compute_amount')
    total_tds = fields.Monetary(string='Total Amount',
                                store=True, readonly=True, compute='_compute_amount')
    total_tds_amount = fields.Monetary(string='Total Amount After TCS',
                                       store=True, readonly=True, compute='_compute_amount')
    sale_type_id = fields.Many2one('sale.type', 'Sale Type')

    cust_invoice_id = fields.Many2one('account.move', 'Customer Invoice')

    # sale_id = fields.Many2one('sale.order', string="Sale", related="purchase_id.sale_id")

    sales_sub_types = fields.Many2one('sale.type.line', string="Sale Sub Types")

    amount_untaxed_signed = fields.Monetary(string='Gross Amount', store=True, readonly=True,
                                            compute='_compute_amount', currency_field='company_currency_id')

    ref = fields.Char(string='Customer Reference', copy=False, tracking=True)
    account_reference = fields.Char(string="Accounts", compute='_get_account_ids', store=True)

    display_declaration = fields.Boolean('Display Declaration Content')
    sale_type_name = fields.Char(related="sale_type_id.name", store=True, string='Sale type')

    @api.onchange('cust_invoice_id')
    def onchange_customer_invoice(self):
        if self.cust_invoice_id:
            self.sale_type_id = self.cust_invoice_id.sale_type_id.id if self.cust_invoice_id.sale_type_id else False
            self.sales_sub_types = self.cust_invoice_id.sales_sub_types.id if self.cust_invoice_id.sales_sub_types else False

    @api.depends('invoice_line_ids.account_id')
    def _get_account_ids(self):
        for rec in self:
            accounts = ''
            for account in rec.invoice_line_ids.mapped('account_id'):
                accounts += str(account.code) + ', ' + account.name + ', '
            rec.account_reference = accounts

    def _get_default_journal(self):
        if self._context.get('default_expense_bill'):
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1, order="id desc")
            return journal
        moves = super(AccountMove, self)._get_default_journal()
        return moves

    customer_invoice_id = fields.Many2one('account.move', 'Customer Invoice')

    vendor_bill = fields.Boolean(string="Vendor")
    expense_bill = fields.Boolean(string="Expense")
    to_self = fields.Char(string="To")
    date_commitment = fields.Date(string="Commitment Date", tracking=True)

    def update_commitment_date(self):
        action = self.env.ref('mm_account.action_account_move_update_commitment_date').sudo().read()[0]
        action['context'] = {'default_move_id': self.id, 'default_old_date_commitment': self.date_commitment}
        return action

    def turnover_compute(self, partner_id, limit, total_tds):
        account_move = self.env['account.move.line'].search(
            [
                ('partner_id', '=', partner_id),
                ('account_id.internal_type', '=', 'payable'),
                ('account_id.reconcile', '=', True),
                ('move_id.state', '=', 'posted')
            ])
        account_credit = sum([account.credit for account in account_move])
        account_credit = account_credit + total_tds
        if account_credit < limit:
            return False
        else:
            return True

    @api.depends('line_ids.debit', 'line_ids.credit', 'line_ids.currency_id', 'line_ids.amount_currency',
                 'line_ids.amount_residual', 'line_ids.amount_residual_currency', 'line_ids.payment_id.state',
                 'tds_ids')
    def _compute_amount(self):
        res = super(AccountMove, self)._compute_amount()
        for account_move in self:
            account_move.tds_added = (account_move.tds_ids.amount * (account_move.total_tds / 100))
            account_move.total_tds = account_move.amount_untaxed + account_move.amount_tax
            account_move.total_tds_amount = account_move.amount_untaxed + account_move.amount_tax + account_move.tds_added
            account_move.amount_total = account_move.amount_untaxed + account_move.amount_tax + account_move.tds_added
            tds_applicable = True
            if account_move.partner_id and account_move.tds_ids:
                tds_applicable = account_move.turnover_compute(account_move.partner_id.id,
                                                               account_move.tds_ids.excess_of,
                                                               account_move.total_tds)
            if not tds_applicable:
                account_move.tds_added = 0
        return res


    @api.onchange('tds_ids', 'apply_tds')
    def tds_ids_onchange(self):
        tds_applicable = True
        for tds in self:

            if tds.partner_id:
                tds_applicable = tds.turnover_compute(tds.partner_id.id, tds.tds_ids.excess_of,
                                                      tds.total_tds)

            if tds.currency_id != tds.company_id.currency_id:
                tds_currency_id = tds.currency_id.id
            else:
                tds_currency_id = False

            if tds.tds_ids:
                tds_tax_lines = tds.tds_ids.invoice_repartition_line_ids.filtered(
                    lambda t: t.repartition_type == 'tax')
            else:
                tds_tax_lines = None

            if tds_tax_lines:
                tax_lines = tds.line_ids.filtered(
                    lambda t: t.account_id.id == tds_tax_lines.account_id.id)
            else:
                tax_lines = None

            if tds.apply_tds and tds_applicable:
                tds_amount = abs(tds.tds_added)
            else:
                tds_amount = 0
            if tds.tds_ids:
                tds_tax = tds.tds_ids
            else:
                tds_tax = None
            account_credit = 0
            account_debit = 0
            if tds.move_type in ['in_invoice']:
                account_debit = tds_amount
            elif tds.move_type in ['out_invoice']:
                account_credit = tds_amount
            if tds_amount and tds_tax and tds_applicable and tds_tax and tds_tax_lines:
                if tax_lines:
                    tax_lines.credit = account_credit
                    tax_lines.debit = account_debit
                else:
                    create_method = tds.env['account.move.line'].new
                    create_method({
                        'name': tds_tax.name,
                        'debit': account_debit,
                        'credit': account_credit,
                        'quantity': 1.0,
                        'amount_currency': tds_amount,
                        'date_maturity': tds.invoice_date,
                        'move_id': tds.id,
                        'currency_id': tds_currency_id,
                        'account_id': tds_tax_lines.id and tds_tax_lines.account_id.id,
                        'partner_id': tds.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                    })
                tds._onchange_recompute_dynamic_lines()
            elif tax_lines:
                tax_lines.credit = 0
                tds._onchange_recompute_dynamic_lines()
                tds.line_ids = tax_lines


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _description = "Journal Item"

    from_sale = fields.Boolean("From Sale", copy=False)
    product_name = fields.Char(related="product_id.name",store=True)

    def _get_computed_taxes(self):
        self.ensure_one()

        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            if self.product_id.taxes_id:
                if self.env.user.company_id.state_id.id == self.move_id.partner_shipping_id.state_id.id:
                    tax_ids = self.product_id.product_tmpl_id.taxes_id
                else:
                    tax_ids = self.product_id.product_tmpl_id.state_taxes_ids
            elif self.account_id.tax_ids:
                tax_ids = self.account_id.tax_ids
            else:
                tax_ids = self.env['account.tax']
            if not tax_ids and not self.exclude_from_invoice_tab:
                tax_ids = self.move_id.company_id.account_sale_tax_id
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            if self.product_id.supplier_taxes_id:
                tax_ids = self.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
            elif self.account_id.tax_ids:
                tax_ids = self.account_id.tax_ids
            else:
                tax_ids = self.env['account.tax']
            if not tax_ids and not self.exclude_from_invoice_tab:
                tax_ids = self.move_id.company_id.account_purchase_tax_id
        else:
            # Miscellaneous operation.
            tax_ids = self.account_id.tax_ids

        if self.company_id and tax_ids:
            tax_ids = tax_ids.filtered(lambda tax: tax.company_id == self.company_id)

        fiscal_position = self.move_id.fiscal_position_id
        if tax_ids and fiscal_position:
            return fiscal_position.map_tax(tax_ids, partner=self.partner_id)
        else:
            return tax_ids

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        res['invoice_line_ids'][0][2]['from_sale'] = True
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res['from_sale'] = True
        return res

class AccountTDS(models.Model):
    _inherit = 'account.tax'

    apply_tds = fields.Boolean('Apply TCS', default=False)
    apply_tds_real = fields.Boolean('Apply TDS', default=False)
    excess_of = fields.Float('In excess of')
    apply_tds_to = fields.Selection([('individual', 'Individual'),
                                     ('company', 'Company'),
                                     ('both', 'Both')], string='Apply TCS to')
                                     

class InvoiceImport(models.Model):
    _name = 'invoice.import'
    _description = 'Invoice Import'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    move_document = fields.Binary(string="Invoice Document")
    move_document_name = fields.Char(string="File Name")
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled')
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    import_line = fields.One2many('invoice.import.line', 'import_id', 'Account Import')

    def generate_move(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.move_document))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except:
            raise UserError(_("Invalid file!"))
        for row_no in range(sheet.nrows):
            val = {}
            if row_no <= 0:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))

                val_line = {
                'name': 'AWS Rental',
                'product_id': self.env['product.product'].search([('default_code','=','AWS')], limit = 1).id,
                'product_uom': 1,
                'product_uom_qty': 1,
                'discount': 0.0,
                'price_unit': int(float(line[2])),

                }

                if self.env.user.company_id.state_id.id == self.env['res.partner'].search([('id','=',int(float(line[1])))], limit = 1).state_id.id:
                    val_line['tax_id'] = [(6, 0, self.env['product.product'].search([('default_code','=','AWS')], limit = 1).product_tmpl_id.taxes_id.ids)]
                else:
                    val_line['tax_id'] = [(6, 0, self.env['product.product'].search([('default_code','=','AWS')], limit = 1).product_tmpl_id.state_taxes_ids.ids)]

                vals = {
                'currency_id': self.company_id.currency_id.id,
                'date_order': self.date,
                'user_id': self.env.user.id,
                'partner_id': self.env['res.partner'].search([('id','=',int(float(line[1])))], limit = 1).id,
                'partner_invoice_id': self.env['res.partner'].search([('id','=',int(float(line[1])))], limit = 1).id,
                'partner_shipping_id': self.env['res.partner'].search([('id','=',int(float(line[1])))], limit = 1).id,
                'pricelist_id': self.env['res.partner'].search([('id','=',int(float(line[1])))], limit = 1).property_product_pricelist.id,
                'client_order_ref': 'AWS Rental',
                'payment_term_id': self.env['res.partner'].search([('id','=',int(float(line[1])))], limit = 1).property_payment_term_id.id,
                'note':'AWS Rental month of %s' % (format_date(self.env, self.date, date_format="MMMM y")),
                'order_line': [(0, 0, val_line)]
                    }

                mv_obj = self.env['sale.order'].create(vals)

                vals_inv = {
                'import_id':self.id,
                'sale_id':mv_obj.id,
                'amount':int(float(line[2]))
                }
                self.env['invoice.import.line'].create(vals_inv)


class InvoiceImportLine(models.Model):
    _name = 'invoice.import.line'
    _description = 'Invoice Import'

    import_id = fields.Many2one('invoice.import', 'Import')
    move_id = fields.Many2one('account.move', 'Invoice')
    sale_id = fields.Many2one('sale.order', 'Sale')
    amount = fields.Float('Amount')


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    _sql_constraints = [
        ('unique_number', 'unique(sanitized_acc_number, company_id, partner_id)', 'Account Number must be unique'),
    ]