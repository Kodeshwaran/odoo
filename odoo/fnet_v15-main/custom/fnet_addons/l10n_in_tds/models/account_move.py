from odoo import models, fields, api, _
# from decimal import Decimal, ROUND_HALF_UP
from odoo.exceptions import UserError, RedirectWarning
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero,round
import pdb


class Partner(models.Model):
    _inherit = 'res.partner'

    pan_no = fields.Char(string='PAN No', size=32, help='Permanent Account Number')
    tan_no = fields.Char(string='TAN No', size=32, help='Tax Account Number')


class AccountTax(models.Model):
    _inherit = 'account.tax'

    amount = fields.Float(required=True, digits=(16, 5))

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        res = super(AccountMove, self)._onchange_purchase_auto_complete()
        if self.invoice_line_ids:
            self.invoice_line_ids.onchange_move_product()
        return res

    # TDS amount Total

    @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.tds_amount', 'invoice_line_ids.tds_section_id')
    def _compute_tds(self):
        for each in self:
            each.amount_tds = 0.0
            each.amount_tds = round(sum(line.tds_amount for line in each.invoice_line_ids))
            each.amount_net = each.amount_total - abs(each.amount_tds)

    @api.depends('partner_id','amount_untaxed')
    def _compute_tcs(self):
        self.amount_tcs = 0.0
        total = 0
        # tcs_month = self.partner_id.tcs_section_id.starting_month
        # tdy_dt = date.today()
        # for each in self:
        #     if each.partner_id and each.partner_id.tcs_applicable and each.partner_id.tcs_section_id:
        #         if self.partner_id.tcs_section_id.starting_month:
        #             st_dt = tdy_dt + relativedelta(day=1, month=int(each.partner_id.tcs_section_id.starting_month))
        #             end_dt = st_dt + relativedelta(days=-1, year=tdy_dt.year+1)
        #         ml_sr = self.env['account.move.line'].search([
        #             ('move_id.state','=','posted'),
        #             ('move_id.partner_id','=',each.partner_id.id),
        #             ('move_id.type','in',('out_invoice','out_refund')),
        #             ('move_id.invoice_date','>=',tcs_line.from_dt),
        #             ('move_id.invoice_date','<=',tcs_line.to_dt)
        #             ])
        for each in self:
            tcs_sr = self.env['section.tcs'].search([]).limit=1
            tcs_br = self.env['section.tcs'].browse(tcs_sr)
            tdy_dt = date.today()
            if each.partner_id:
                tcs_section_val = each.partner_id.tcs_section_id or tcs_br
                print(tcs_section_val,"************tcs_section_val")
                if tcs_section_val and tcs_section_val.tcs_line_ids:
                    for tcs_line in tcs_section_val.tcs_line_ids:
                    # st_dt = tdy_dt + relativedelta(day=1, month=int(tcs_section_val.starting_month))
                    # end_dt = st_dt + relativedelta(days=-1, year=tdy_dt.year+1)
                        ml_sr = self.env['account.move.line'].search([
                            ('parent_state','=','posted'),
                            ('move_id.partner_id','=',each.partner_id.id),
                            ('move_id.move_type','in',('out_invoice','out_refund')),
                            ('move_id.invoice_date','>=',tcs_line.from_dt),
                            ('move_id.invoice_date','<=',tcs_line.to_dt)])
                        print(ml_sr,"-----------------ml_sr")
                    debit_tt = 0
                    ref_debit_tt = 0
                    credit_tt = 0
                    ref_credit_tt = 0
                    tt_diff = 0
                    for ml in ml_sr:
                        if ml.move_id.type == 'out_invoice':
                            if ml.debit > 0:
                                debit_tt +=ml.debit
                            if ml.credit >0:
                                credit_tt += ml.credit
                        if ml.move_id.type == 'out_refund':
                            if ml.debit > 0:
                                ref_debit_tt +=ml.debit
                            if ml.credit >0:
                                ref_credit_tt += ml.credit
                    if debit_tt >= 0 and ref_debit_tt >= 0:
                        tt_diff = (debit_tt - ref_debit_tt) + each.amount_untaxed
                    if tt_diff > 0:
                        if tt_diff > each.partner_id.tcs_section_id.limit_amt:
                            tcs_amount = each.amount_untaxed * each.partner_id.tcs_section_id.tcs_percentage/100
                            each.amount_tcs = tcs_amount
                            print(tcs_amount,"*********************_compute_tcs")

    amount_tds = fields.Float(compute='_compute_tds', string='TDS', digits=(16, 2), store=True)
    tds_related = fields.Boolean(string='TDS Applicable ?')
    tds_section_id = fields.Many2one('section.tds', string='TDS Section')
    amount_net = fields.Float(compute='_compute_tds', string='Net Amount', digits=(16, 2))
    amount_tcs = fields.Monetary(string="TCS", digits=(16, 2), copy=False, store=True, invisible=True)

    # inherited function to pass tds appplicable

    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None):
        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self._prepare_refund(invoice, date_invoice=date_invoice, date=date,
                                          description=description, journal_id=journal_id)
            values.update({'tds_related': self.tds_related or False})
            refund_invoice = self.create(values)
            invoice_type = {'out_invoice': ('customer invoices credit note'),
                            'in_invoice': ('vendor bill credit note')}
            message = _(
                "This %s has been created from: <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a>") % (
                      invoice_type[invoice.type], invoice.id, invoice.number)
            refund_invoice.message_post(body=message)
            new_invoices += refund_invoice
        return new_invoices

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False
        tds_related = False
        tds_section_id = False
        p = self.partner_id
        company_id = self.company_id.id
        type = self.move_type
        if p:
            partner_id = p.id
            rec_account = p.property_account_receivable_id
            pay_account = p.property_account_payable_id
            if p.tds_applicable == True:
                tds_related = True
                tds_section_id = p.tds_section_id.id or False
            if company_id:
                if p.property_account_receivable_id.company_id and \
                        p.property_account_receivable_id.company_id.id != company_id and \
                        p.property_account_payable_id.company_id and \
                        p.property_account_payable_id.company_id.id != company_id:
                    prop = self.env['ir.property']
                    rec_dom = [('name', '=', 'property_account_receivable_id'), ('company_id', '=', company_id)]
                    pay_dom = [('name', '=', 'property_account_payable_id'), ('company_id', '=', company_id)]
                    res_dom = [('res_id', '=', 'res.partner,%s' % partner_id)]
                    rec_prop = prop.search(rec_dom + res_dom) or prop.search(rec_dom, limit=1)
                    pay_prop = prop.search(pay_dom + res_dom) or prop.search(pay_dom, limit=1)
                    rec_account = rec_prop.get_by_record(rec_prop)
                    pay_account = pay_prop.get_by_record(pay_prop)
                    if not rec_account and not pay_account:
                        action = self.env.ref('account.action_account_config')
                        msg = _(
                            'Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                        raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('out_invoice', 'out_refund'):
                account_id = rec_account.id
                payment_term_id = p.property_payment_term_id.id
            else:
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term_id.id
            addr = p.address_get(['delivery'])
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(p.id,
                                                                                      delivery_id=addr['delivery'])
        # pdb.set_trace()
        print("---", account_id, "--account_id--")
        # self.account_id = account_id
        self.invoice_payment_term_id = payment_term_id
        self.fiscal_position_id = fiscal_position
        self.tds_related = tds_related
        self.tds_section_id = tds_section_id

        if type in ('in_invoice', 'out_refund'):
            bank_ids = p.commercial_partner_id.bank_ids
            bank_id = bank_ids[0].id if bank_ids else False
            self.partner_bank_id = bank_id
            return {'domain': {'partner_bank_id': [('id', 'in', bank_ids.ids)]}}
        return {}

    def action_post(self):
        if self.partner_id.tds_applicable:
            for each in self.invoice_line_ids:
                if each.tds_section_id:
                    payable_journal = payable_journal_ids = self.line_ids.filtered(
                        lambda line: line.account_internal_type in ('payable'))
                    for payable_journal_id in payable_journal_ids:
                        if payable_journal_id.name == 'TDS':
                            continue
                        else:
                            payable_journal = payable_journal_id
                    account_id = each.tds_section_id.acc_receivable_id.id or False
                    if self.move_type in ('in_invoice', 'out_refund'):
                        price = round(abs(each.tds_amount))
                        print(each.tds_amount,"*********************************************",round(each.tds_amount),round(abs(each.tds_amount)))
                        tds_move_line = {
                            'line_ids': [[0, 0, {
                                'sequence': 10,
                                'credit': price,
                                'product_id': each.product_id.id,
                                'partner_id': self.partner_id.id,
                                'debit': 0.0,
                                'price_unit': price,
                                'exclude_from_invoice_tab': True,
                                'name': 'TDS',
                                'account_id': account_id or False,
                                'date_maturity': False,
                                'currency_id': False,
                                'parent_state': 'draft',
                                'analytic_account_id': each.analytic_account_id.id,
                                'analytic_tag_ids': [(6, 0, each.analytic_tag_ids.ids)] or False
                            }],
                                 [1, payable_journal.id, {
                                     'sequence': 10,
                                     'credit': payable_journal.credit - price,
                                     'product_id': payable_journal.product_id.id,
                                     'partner_id': payable_journal.partner_id.id,
                                     'price_unit': payable_journal.price_unit,
                                     'exclude_from_invoice_tab': payable_journal.exclude_from_invoice_tab,
                                     'name': payable_journal.name,
                                     'account_id': payable_journal.account_id.id or False,
                                     'date_maturity': payable_journal.date_maturity,
                                     'currency_id': payable_journal.currency_id.id,
                                     'ref': payable_journal.ref,
                                     'parent_state': 'draft',
                                     'analytic_account_id': payable_journal.analytic_account_id.id,
                                     'analytic_tag_ids': [(6, 0, payable_journal.analytic_tag_ids.ids)] or False
                                 }]]}
                    if self.move_type in ('out_invoice', 'in_refund'):
                        account_id = each.tds_section_id.acc_payable_id.id or False
                        price = round(abs(each.tds_amount))
                        tds_move_line = {'line_ids': [[0, 0, {
                            'sequence': 10,
                            'credit': 0.0,
                            'product_id': each.product_id.id,
                            'partner_id': self.partner_id.id,
                            'debit': price,
                            'price_unit': price,
                            'exclude_from_invoice_tab': True,
                            'name': 'TDS',
                            'account_id': account_id or False,
                            'date_maturity': False,
                            'currency_id': False,
                            'parent_state': 'draft',
                            'analytic_account_id': each.analytic_account_id.id,
                            'analytic_tag_ids': [(6, 0, each.analytic_tag_ids.ids)] or False
                        }, ], [1, payable_journal.id, {
                            'sequence': 10,
                            'debit': payable_journal.debit - price,
                            'product_id': payable_journal.product_id.id,
                            'partner_id': payable_journal.partner_id.id,
                            'price_unit': payable_journal.price_unit,
                            'exclude_from_invoice_tab': payable_journal.exclude_from_invoice_tab,
                            'name': payable_journal.name,
                            'account_id': payable_journal.account_id.id or False,
                            'date_maturity': payable_journal.date_maturity,
                            'currency_id': payable_journal.currency_id.id,
                            'ref': payable_journal.ref,
                            'parent_state': 'draft',
                            'analytic_account_id': payable_journal.analytic_account_id.id,
                            'analytic_tag_ids': [(6, 0, payable_journal.analytic_tag_ids.ids)] or False
                        }]]}
                    lines = self.write(tds_move_line)
        for each in self:
            if each.partner_id.tds_applicable:
                for line in each.invoice_line_ids:
                    if line.tds_section_id:
                        if not line.tds_section_id.company_id:
                            raise UserError(_("Please set company in TDS section : %s" % (line.tds_section_id.name)))
                        elif line.tds_section_id.company_id.id != self.env.user.company_id.id:
                            raise UserError(_(
                                "The current users company and company configured in TDS section : %s does not match" % (
                                    line.tds_section_id.name)))
                        if not (line.tds_section_id.acc_payable_id or line.tds_section_id.acc_receivable_id):
                            raise UserError(_(
                                "You have not configured reversal or payable account for the TDS section : %s. Kindly configure it to proceed further" % line.tds_section_id.name))
        self.amount_tcs = 0.0
        total = 0
        tcs_sr = self.env['section.tcs'].search([], limit=1)
        tcs_br = self.env['section.tcs'].browse(tcs_sr)
        # llll
        # tcs_month = self.partner_id.tcs_section_id.starting_month
        print(self.partner_id.tcs_section_id ,'================', tcs_br)
        tcs_section_val = self.partner_id.tcs_section_id or tcs_br
        print(tcs_section_val,"************tcs_section_val")
        tdy_dt = date.today()
        # if self.partner_id and tcs_section_val:
        #     ml_sr = []
        #     if tcs_section_val.tcs_line_ids:
        #         for tcs_line in tcs_section_val.tcs_line_ids:
        #             print(tcs_line.from_dt,"=================fsfs",tcs_line.to_dt,self.partner_id,self.type)
        #         # st_dt = tdy_dt + relativedelta(day=1, month=int(tcs_section_val.starting_month))
        #         # end_dt = st_dt + relativedelta(days=-1, year=tdy_dt.year+1)
        #             ml_sr.append(self.env['account.move.line'].search([
        #                 ('parent_state','=','posted'),
        #                 ('move_id.partner_id','=',self.partner_id.id),
        #                 ('move_id.type','in',('out_invoice','out_refund')),
        #                 ('move_id.invoice_date','>=',tcs_line.from_dt),
        #                 ('move_id.invoice_date','<=',tcs_line.to_dt)]))
        #             print(ml_sr,"-----------------ml_sr")
        #     # ml_sr = self.env['account.move.line'].search([('parent_state','=','posted'),('move_id.partner_id','=',self.partner_id.id),('move_id.type','in',('out_invoice','out_refund')),('move_id.invoice_date','>=',st_dt),('move_id.invoice_date','<=',end_dt)])
        #     debit_tt = 0
        #     ref_debit_tt = 0
        #     credit_tt = 0
        #     ref_credit_tt = 0
        #     tt_diff = 0
        #     for ml in ml_sr:
        #         if ml.move_id.type == 'out_invoice':
        #             if ml.debit > 0:
        #                 debit_tt +=ml.debit
        #             if ml.credit > 0:
        #                 credit_tt += ml.credit
        #         if ml.move_id.type == 'out_refund':
        #             if ml.debit > 0:
        #                 ref_debit_tt +=ml.debit
        #             if ml.credit >0:
        #                 ref_credit_tt += ml.credit
        #     print(debit_tt,"debit amounttttttttttttttttt")
        #     print(ref_debit_tt,"debit amounttttttttttttttttt")
        #     if debit_tt > 0 and ref_debit_tt > 0:
        #         tt_diff = debit_tt - ref_debit_tt
        #     print(tt_diff,"---------------tt_diff",tcs_section_val.limit_amt)
        #     if tt_diff > 0:
        #         if tt_diff > tcs_section_val.limit_amt:
        #             tcs_amount = self.amount_total * tcs_section_val.tcs_percentage/100
        #             self.amount_tcs = tcs_amount
        #             print("\n\n\n\n\n",tcs_amount)
        #             if not self.partner_id.tcs_applicable:
        #                 self.partner_id.tcs_applicable = True
        #                 self.partner_id.tcs_section_id = tcs_section_val
        #                 self.partner_id.tcs_type = 'company'
        #                 print(self.partner_id.tcs_applicable,'///////////////////////',self.partner_id.tcs_section_id)
        #             self.create_tcs_journal(tcs_amount)

        res = super(AccountMove, self).action_post()
        return res

    def create_tcs_journal(self, tcs_amount):
        price = abs(self.tcs_amount)
        print(price,"++++++++++++++++++++++$$$$$$$$$$$$$$$$$$$$$$$$$")
        # if self.partner_id.tcs_applicable and price > 0:
        #     payable_journal = payable_journal_ids = self.line_ids.filtered(
        #         lambda line: line.account_internal_type in ('receivable'))
        #     for payable_journal_id in payable_journal_ids:
        #         if payable_journal_id.name == 'TCS':
        #             continue
        #         else:
        #             payable_journal = payable_journal_id
        #     account_id = self.partner_id.tcs_section_id.acc_payable_id.id or False
        for move in self:
            account_id = move.partner_id.tcs_section_id.acc_payable_id.id
            # account_id = int(self.env['ir.config_parameter'].sudo().get_param("account.roundoff_account_id"))
            # amount_total = round((move.amount_total + move.amount_tcs + move.amount_tds))
            # amount_round_off = amount_total - (move.amount_total + move.amount_tcs + move.amount_tds)
            # print(amount_total,"============rrr==========",move,move.amount_tcs,move.amount_tds,amount_round_off)
            # move.round_off_value = amount_round_off
            # move.round_off_amount = amount_round_off
            tax_obj = self.env['account.tax'].search([('name', '=', 'TCS 0.075%')], limit=1)
            if price != 0.00:
                values = [0,0,{
                    'name': 'TCS',
                    'account_id': account_id,
                    'quantity': 1,
                    'price_unit': price,
                    'display_type': False,
                    'exclude_from_invoice_tab': False,
                    'is_rounding_line': False,
                    'move_id': move.id,
                }]
                if values:
                    move.invoice_line_ids = [values]
        #     if move.round_active and move.amount_total:
        #         amount_total = round((move.amount_total + move.amount_tcs + move.amount_tds))
        #         amount_round_off = amount_total - (move.amount_total + move.amount_tcs + move.amount_tds)
        #         move.rounded_total = amount_total
        #         move.amount_total = amount_total
        #         move.amount_total_signed = move.amount_untaxed
        #     else:
        #         move.round_off_value = 0.00
        #         move.round_off_amount = 0.00
        #         move.rounded_total =0.00            
        #     print(amount_total,"============end==========",move,move.amount_tcs,move.amount_tds,amount_round_off)
        # res = super(AccountMove, self).action_post()
        # return res

    # def create_tcs_journal(self):
    #     price = abs(self.amount_tcs)
    #     if self.partner_id.tcs_applicable and price > 0:
    #         payable_journal = payable_journal_ids = self.line_ids.filtered(
    #             lambda line: line.account_internal_type in ('receivable'))
    #         for payable_journal_id in payable_journal_ids:
    #             if payable_journal_id.name == 'TCS':
    #                 continue
    #             else:
    #                 payable_journal = payable_journal_id
    #         account_id = self.partner_id.tcs_section_id.acc_payable_id.id or False
    #         # if self.type in ('in_invoice', 'out_refund'):
    #         if self.type == 'in_invoice':
    #             tcs_move_line = {
    #                 'line_ids': [[0, 0, {
    #                     'sequence': 10,
    #                     'debit': price,
    #                     'partner_id': self.partner_id.id,
    #                     'price_unit': price,
    #                     'exclude_from_invoice_tab': True,
    #                     'name': 'TCS',
    #                     'account_id': account_id or False,
    #                     'date_maturity': False,
    #                     'currency_id': False,
    #                     'parent_state': 'draft',
    #                 }],
    #                      [1, payable_journal.id, {
    #                          'sequence': 10,
    #                          'credit': payable_journal.credit + price,
    #                          'partner_id': payable_journal.partner_id.id,
    #                          'price_unit': payable_journal.price_unit,
    #                          'exclude_from_invoice_tab': payable_journal.exclude_from_invoice_tab,
    #                          'name': payable_journal.name,
    #                          'account_id': payable_journal.account_id.id or False,
    #                          'date_maturity': payable_journal.date_maturity,
    #                          'currency_id': payable_journal.currency_id.id,
    #                          'ref': payable_journal.ref,
    #                          'parent_state': 'draft',
    #                          'analytic_account_id': payable_journal.analytic_account_id.id,
    #                          'analytic_tag_ids': [(6, 0, payable_journal.analytic_tag_ids.ids)] or False
    #                      }]]}
    #             lines = self.write(tcs_move_line)
    #         if self.type in ('out_invoice', 'in_refund'):
    #             account_id = self.partner_id.tcs_section_id.acc_receivable_id.id or False
    #             tcs_move_line = {'line_ids': [[0, 0, {
    #                 'sequence': 10,
    #                 'credit': price,
    #                 'partner_id': self.partner_id.id,
    #                 'debit': 0.0,
    #                 'price_unit': price,
    #                 'exclude_from_invoice_tab': True,
    #                 'name': 'TCS',
    #                 'account_id': account_id or False,
    #                 'date_maturity': False,
    #                 'currency_id': False,
    #                 'parent_state': 'draft',
    #             }, ], [1, payable_journal.id, {
    #                 'sequence': 10,
    #                 'debit': payable_journal.debit + price,
    #                 'partner_id': payable_journal.partner_id.id,
    #                 'price_unit': payable_journal.price_unit,
    #                 'exclude_from_invoice_tab': payable_journal.exclude_from_invoice_tab,
    #                 'name': payable_journal.name,
    #                 'account_id': payable_journal.account_id.id or False,
    #                 'date_maturity': payable_journal.date_maturity,
    #                 'currency_id': payable_journal.currency_id.id,
    #                 'ref': payable_journal.ref,
    #                 'parent_state': 'draft',
    #                 'analytic_account_id': payable_journal.analytic_account_id.id,
    #                 'analytic_tag_ids': [(6, 0, payable_journal.analytic_tag_ids.ids)] or False
    #             }]]}
    #             lines = self.write(tcs_move_line)


class AccountLines(models.Model):
    _inherit = 'account.move.line'
    _description = 'Account Move Line'

    # TDS amount total on line subtotal

    def compute_narration(self):
        for rec in self:
            rec.narration = rec.move_id.narration

    def compute_warehouse(self):
        for rec in self:
            rec.warehouse_id = rec.move_id.warehouse_id.name

    def compute_bill_date(self):
        for rec in self:
            rec.bill_dt = rec.move_id.bill_dt

    def compute_bill_no(self):
        for rec in self:
            rec.bill_no = rec.move_id.bill_no

    @api.depends('price_unit', 'price_subtotal', 'tds_section_id')
    def _compute_tds_amount(self):
        inv = []
        for each in self:
            each.tds_amount = 0.0
            each.tds_rate = 0.0
            if each.move_id.partner_id and each.move_id.tds_related:
                each.partner_id = each.move_id.partner_id
            if each.move_id.partner_id.tds_applicable:
                if each.tds_section_id:
                    tds_line_sr = self.env['section.tds.line'].search([('tds_id','=',each.tds_section_id.id),('from_dt',"<=", each.move_id.invoice_date),('to_dt','>=',each.move_id.invoice_date)])
                    if tds_line_sr:
                        tds_line_sr = tds_line_sr[0]
                        if each.move_id.partner_id.pan_no:
                            if each.partner_id.tds_type == 'company':
                                each.tds_amount = -(each.price_subtotal - (each.price_subtotal - (
                                            each.price_subtotal * (tds_line_sr.company_percent * 0.01))))
                                each.tds_rate = tds_line_sr.company_percent or 0.00
                            else:
                                each.tds_amount = -(each.price_subtotal - (each.price_subtotal - (
                                            each.price_subtotal * (tds_line_sr.individual_percent * 0.01))))
                                each.tds_rate = tds_line_sr.individual_percent or 0.00
                        else:
                            each.tds_amount = -(each.price_subtotal - (each.price_subtotal - (
                                        each.price_subtotal * (tds_line_sr.others_percent * 0.01))))
                            each.tds_rate = tds_line_sr.others_percent or 0.00

    tds_section_id = fields.Many2one('section.tds', string='TDS Section')
    invoice_type = fields.Selection(related='move_id.move_type', readonly=True)
    tds_rate = fields.Float(string="Tax Rate", digits=(16, 2), compute='_compute_tds_amount')
    tds_amount = fields.Float('Income Tax', digits=(16, 2), compute='_compute_tds_amount')
    inv_number = fields.Char(string='Internal Reference', related='move_id.name', store=True)
    vendor_ref = fields.Char(string='Vendor Bill No', related='move_id.payment_reference', store=True)
    bill_date = fields.Date(string='Bill Date', related='move_id.invoice_date', store=True)
    pan_no = fields.Char(string='PAN No', related='partner_id.pan_no', store=True)
    tan_no = fields.Char(string='TAN No', related='partner_id.tan_no', store=True)
    tds_type = fields.Selection([('company', 'Company'), ('individual', 'Individual')], string='Company/Individual',
                                related='partner_id.tds_type', store=True)
    payment_nature = fields.Char(string='Nature of Payment', related='tds_section_id.nature', store=True)

    street = fields.Char(string="Street1", related='partner_id.street')
    street2 = fields.Char(string="Street2", related='partner_id.street2')

    city = fields.Char(string="City", related='partner_id.city')
    state_id = fields.Char(string="State", related='partner_id.state_id.name')
    zip = fields.Char(string="Pin Code", related='partner_id.zip')
    is_transporter = fields.Char(string="Is Transporter",)
    invoice_date = fields.Date(string="Invoice Date" , related='move_id.invoice_date' )
    Invoice_date2 = fields.Date("Amount Paid/Credited Date", related='move_id.invoice_date')
    phone = fields.Char(string="Phone", related='partner_id.phone')
    mobile = fields.Char(string="Mobile Number", related='partner_id.mobile')
    email = fields.Char(string="Addl. Email ID", related='partner_id.email')
    warehouse_id = fields.Char(string='Branch',compute='compute_warehouse')
    bill_no = fields.Char(stiring="Reference No.", compute='compute_bill_no')
    bill_dt = fields.Date(string="Ref Date", compute='compute_bill_date')
    narration = fields.Text(string="Narration", compute='compute_narration')




    @api.onchange('product_id')
    def onchange_move_product(self):
        for mvl in self:
            if mvl.product_id and mvl.partner_id and mvl.partner_id.tds_applicable and mvl.partner_id.tds_section_id:
                mvl.tds_section_id = mvl.partner_id.tds_section_id.id

    # def _get_computed_taxes(self):
    #     res = super(AccountLines,self)._get_computed_taxes()
    #     tax_obj = self.env['account.tax'].search([('name','=','TCS 0.075%')], limit=1)
    #     tax_lis = []
    #     if self.move_id.type == 'out_invoice' and self.move_id.partner_id.tcs_applicable:
    #         for tax_id in self.tax_ids:
    #             tax_lis.append(tax_id.id)
    #         tax_lis.append(tax_obj.id)
    #         self.update({'tax_ids': [( 6, 0, tax_lis)]})
    #     return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     tax_obj = self.env['account.tax'].search([('name', '=', 'TCS 0.075%')], limit=1)
    #     for item in vals_list:
    #         move = self.env['account.move'].browse(item['move_id'])
    #         if move.type == 'out_invoice' and move.partner_id.tcs_applicable:
    #             tax_lis = item.get('tax_ids')[0][2]
    #             tax_pa_line = self.env['account.tax.repartition.line'].search([('invoice_tax_id', '=', tax_obj.id)], limit=1)
    #             tax_lis.append(tax_pa_line.invoice_tax_id.id)
    #             # item['tax_ids'] = [(6, 0, tax_lis)]
    #     return super(AccountLines, self).create(vals_list)


