from odoo import models, api, fields, _
from datetime import datetime
from dateutil import relativedelta
import xlsxwriter
import decimal
import base64
import string
import logging
import operator
from num2words import num2words
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    bank_details = fields.Binary('NEFT Statement', readonly=True)
    bank_details_name = fields.Char('Filename', size=64, readonly=True)

    journal_id = fields.Many2one('account.journal', 'Salary Journal', required=True)
    journal_entry = fields.Many2one('account.move', 'Accounting Entry')
    accounting_date = fields.Date("Accounting Date")
    counter_account = fields.Integer("Account Entry", compute="compute_acc_entry")

    def compute_acc_entry(self):
        for rec in self:
            rec.counter_account = self.env['account.move'].search_count([('id', '=', rec.journal_entry.id)])

    def action_view_account_entry(self):
        acc_ent = self.env['account.move'].search([('id', '=', self.journal_entry.id)])
        return {
            'name': _('Account Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': acc_ent.id
        }

    def action_account_entry(self):
        # res = super(HrPayslipRun, self).action_account_entry()
        for batch in self:
            line_ids = []
            date = batch.date_start or batch.date_end
            month = datetime.strptime(str(self.date_start), '%Y-%m-%d').strftime("%B")
            current_year = datetime.now().year
            currency = batch.company_id.currency_id
            # print("---", slip_ids, "--slip_ids-\n")
            name = _('Salary of %s') % batch.name
            move_dict = {
                'narration': 'Salary Expenses booked for the month of %s %s' % (month, current_year),
                'ref': name,
                'journal_id': batch.journal_id.id,
                'date': date,
            }
            # print("---", move_dict['narration'], "--name-\n")
            # print("---", move_dict['date'], "--move_dict['date']-\n")
            # if currency.is_zero(amount):
            #     continue
            debit_accounts_admin = batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee' and x.employee_id.is_admin).mapped('employee_id').mapped('entry_account_id')
            debit_accounts = batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee' and not x.employee_id.is_admin).mapped('line_ids').filtered(lambda x: not x.code in ['GR','PT', 'TDS', 'EEPF', 'ESI'] and not x.category_id.code == 'DETUCTIONS').mapped('salary_rule_id').mapped(
                'account_debit')
            print("---", debit_accounts, "--debit_accounts-\n")
            credit_accounts = batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee').mapped('line_ids').mapped('salary_rule_id').mapped(
                'account_credit')
            for acc in debit_accounts_admin:
                admin_departments = batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee' and x.employee_id.is_admin).mapped('department_id')
                for dep in admin_departments:
                    total = sum(batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee' and x.employee_id.is_admin).filtered(lambda x: x.department_id.id == dep.id).mapped('line_ids').filtered(lambda x: x.code == 'GROSS').mapped('total'))
                    if total != 0:
                        debit_line = (0, 0, {
                            'name': dep.name,
                            'partner_id': False,
                            'account_id': acc.id,
                            'journal_id': batch.journal_id.id,
                            'date': date,
                            'debit': total > 0.0 and total or 0.0,
                            'credit': total < 0.0 and -total or 0.0,
                        })
                        line_ids.append(debit_line)
            for account in debit_accounts:
                departments = batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee'and not x.employee_id.is_admin).mapped('line_ids').filtered(
                    lambda x: x.salary_rule_id.account_debit.id == account.id).mapped('slip_id').mapped('department_id')
                for department in departments:
                    rules = batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee' and not x.employee_id.is_admin).filtered(lambda x: x.department_id.id == department.id).mapped('line_ids').filtered\
                                (lambda x: x.salary_rule_id.account_debit.id == account.id).mapped('salary_rule_id')
                    for rule in rules:
                        rule_tot = sum(batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee' and not x.employee_id.is_admin).filtered(lambda x: x.department_id.id == department.id).mapped('line_ids').filtered(lambda x: x.salary_rule_id == rule).mapped('total'))

                        if rule_tot != 0:
                            debit_line = (0, 0, {
                                'name': department.name,
                                'partner_id': False,
                                'account_id': account.id,
                                'journal_id': batch.journal_id.id,
                                'date': date,
                                'debit': rule_tot > 0.0 and rule_tot or 0.0,
                                'credit': rule_tot < 0.0 and -rule_tot or 0.0,
                            })
                            line_ids.append(debit_line)
                            print("---", debit_line, "--debit_line-\n")
                            # debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
            for account in credit_accounts:
                rules = batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee').mapped(
                    'line_ids').filtered(lambda x: x.salary_rule_id.account_credit.id == account.id).mapped('salary_rule_id')
                for rule in rules:
                    if rule.code == 'GROSS':
                        rule_tot = sum(batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee').mapped(
                                'line_ids').filtered(lambda x: x.salary_rule_id == rule and x.slip_id.contract_id.wage > 0).mapped('total')) - sum(batch.mapped('slip_ids').mapped(
                                'line_ids').filtered(lambda x: x.category_id.code == 'DED' and x.slip_id.contract_id.wage > 0).mapped('total'))
                    elif rule.code == 'CON':
                        rule_tot = sum(batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee').mapped('line_ids').filtered(lambda x: x.salary_rule_id == rule and x.slip_id.contract_id.consolidate_pay > 0).mapped(
                            'total')) - sum(batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee').mapped('line_ids').filtered(lambda x: x.category_id.code == 'DED' and x.slip_id.contract_id.consolidate_pay > 0).mapped('total'))
                    elif rule.code in ['GR', 'PT', 'TDS', 'EEPF', 'ESI']:
                        rule_tot = sum(batch.mapped('slip_ids').filtered(lambda x: x.employee_categ == 'employee').mapped(
                                'line_ids').filtered(lambda x: x.salary_rule_id == rule).mapped('total'))
                        print("---", rule_tot, "--rule_tot-\n")
                    if rule_tot != 0:
                        credit_line = (0, 0, {
                            'name': '%s %s' % (month, str(current_year)),
                            'partner_id': False,
                            'account_id': account.id,
                            'journal_id': batch.journal_id.id,
                            'date': date,
                            'debit': rule_tot < 0.0 and -rule_tot or 0.0,
                            'credit': rule_tot > 0.0 and rule_tot or 0.0,
                        })
                        line_ids.append(credit_line)
                        print("---", credit_line, "--credit_line-\n")
                        # credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            canteen_entry = sum(batch.mapped('slip_ids').filtered(lambda x: x.employee_id.is_canteen).mapped('line_ids').filtered(lambda x: x.code == 'GROSS').mapped('total'))
            canteen_debit_account = batch.mapped('slip_ids').filtered(lambda x: x.employee_id.is_canteen).mapped('employee_id').mapped('debit_entry_account_id')
            canteen_credit_account = batch.mapped('slip_ids').filtered(lambda x: x.employee_id.is_canteen).mapped('employee_id').mapped('credit_entry_account_id')
            if canteen_entry != 0:
                canteen_debit_line = (0, 0, {
                    'name': batch.mapped('slip_ids').filtered(lambda x: x.employee_id.is_canteen).mapped('employee_id').mapped('name'),
                    'partner_id': False,
                    'account_id': canteen_debit_account.id,
                    'journal_id': batch.journal_id.id,
                    'date': date,
                    'debit': canteen_entry > 0.0 and canteen_entry or 0.0,
                    'credit': canteen_entry < 0.0 and -canteen_entry or 0.0,
                })
                line_ids.append(canteen_debit_line)
            if canteen_entry != 0:
                canteen_credit_line = (0, 0, {
                    'name': batch.mapped('slip_ids').filtered(lambda x: x.employee_id.is_canteen).mapped('employee_id').mapped('name'),
                    'partner_id': False,
                    'account_id': canteen_credit_account.id,
                    'journal_id': batch.journal_id.id,
                    'date': date,
                    'debit': canteen_entry < 0.0 and -canteen_entry or 0.0,
                    'credit': canteen_entry > 0.0 and canteen_entry or 0.0,
                })
                line_ids.append(canteen_credit_line)
            # print("---", canteen_credit_line, "--canteen_credit_line-\n")
                        # if currency.compare_amounts(credit_sum, debit_sum) == -1:
                        #     acc_id = batch.journal_id.default_account_id.id
                        #     if not acc_id:
                        #         raise UserError(
                        #             _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                        #                 batch.journal_id.name))
                        #     adjust_credit = (0, 0, {
                        #         'name': _('Adjustment Entry'),
                        #         'partner_id': False,
                        #         'account_id': acc_id,
                        #         'journal_id': batch.journal_id.id,
                        #         'date': date,
                        #         'debit': 0.0,
                        #         'credit': currency.round(debit_sum - credit_sum),
                        #     })
                        #     line_ids.append(adjust_credit)
                        #
                        # elif currency.compare_amounts(debit_sum, credit_sum) == -1:
                        #     acc_id = batch.journal_id.default_account_id.id
                        #     if not acc_id:
                        #         raise UserError(
                        #             _('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                        #                 batch.journal_id.name))
                        #     adjust_debit = (0, 0, {
                        #         'name': _('Adjustment Entry'),
                        #         'partner_id': False,
                        #         'account_id': acc_id,
                        #         'journal_id': batch.journal_id.id,
                        #         'date': date,
                        #         'debit': currency.round(credit_sum - debit_sum),
                        #         'credit': 0.0,
                        #     })
                        #     line_ids.append(adjust_debit)
                        
        move_dict['line_ids'] = line_ids
        move = self.env['account.move'].create(move_dict)
        print("---", move, "--move-\n")
        batch.write({'journal_entry': move.id, 'accounting_date': date})
        if not move.line_ids:
            raise UserError(_("As you installed the payroll accounting module you have to choose Debit and Credit"
                  " account for at least one salary rule in the choosen Salary Structure."))




    def bank_acc_details(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'NEFT Statement.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center', 'bold': True})
        format1.set_text_wrap()
        format2 = workbook.add_format({'font_size': 12, 'align': 'center'})
        bold_1 = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
        })
        sheet.set_row(5, 50)
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 28)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 58)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 15)
        sheet.set_column('O:O', 15)
        sheet.set_column('P:P', 15)
        sheet.set_column('Q:Q', 15)
        sheet.set_column('R:R', 15)
        sheet.set_column('S:S', 15)
        sheet.set_column('T:T', 15)
        sheet.set_column('U:U', 15)
        sheet.set_column('V:V', 15)
        sheet.set_column('W:W', 15)
        sheet.set_column('X:X', 15)
        sheet.set_column('Y:Y', 15)
        sheet.set_column('AA:AA', 15)
        sheet.set_column('AB:AB', 15)
        sheet.set_column('AC:AC', 15)
        sheet.set_column('AD:AD', 15)
        sheet.set_column('AE:AE', 15)
        sheet.set_column('AF:AF', 15)
        sheet.set_column('AG:AG', 15)
        sheet.set_column('AH:AH', 15)
        sheet.set_column('AI:AI', 15)
        sheet.set_column('AJ:AJ', 15)
        sheet.set_column('AK:AK', 15)
        sheet.set_column('AL:AL', 15)
        sheet.set_column('AM:AM', 15)
        sheet.set_column('AN:AN', 15)
        sheet.set_column('AO:AO', 15)
        sheet.set_column('AP:AP', 15)
        sheet.set_column('AQ:AQ', 15)
        sheet.set_column('AR:AR', 15)
        sheet.set_column('AS:AS', 15)
        sheet.set_column('AT:AT', 15)
        sheet.set_column('AU:AU', 15)

        company = self.env.user.company_id

        sheet.merge_range('B3:E3', 'NEFT Statement', format1)
        sheet.merge_range('B1:E1', company.name, format1)
        sheet.merge_range('B2:E2', (company.street or '') + ' ' + (company.street2 or '') + ' ' + (
                company.city or '') + ' ' + (company.state_id.name if company.state_id else '') + ' ' + (
                              company.country_id.name if company.country_id else '') + ' ' + (company.zip or ''),
                          bold_1)
        banks = self.env['hr.payslip'].search([('id', 'in', self.slip_ids.ids)])
        row = 0
        col = 0
        sheet.write(row + 5, col, 'S.No', format1)
        sheet.write(row + 5, col + 1, 'IFSC Code', format1)
        sheet.write(row + 5, col + 2, 'Beneficiary Account Number', format1)
        sheet.write(row + 5, col + 3, 'Beneficiary Name', format1)
        sheet.write(row + 5, col + 4, 'Amount', format1)
        sheet.write(row + 5, col + 5, 'Remarks for Beneficiary', format1)

        s_no = 1
        for bank in banks:
            row += 1
            sheet.write(row + 5, col, s_no, format2)
            sheet.write(row + 5, col + 1, bank.employee_id.bank_account_id.ifsc_code if bank.employee_id.bank_account_id.ifsc_code else ' ' , format2)
            sheet.write(row + 5, col + 2, bank.employee_id.bank_account_id.acc_number if bank.employee_id.bank_account_id.acc_number else ' '  , format2)
            sheet.write(row + 5, col + 3, bank.employee_id.name, format2)
            sheet.write(row + 5, col + 4, bank.line_ids.filtered(lambda x: x.code == 'NET').total, format2)
            sheet.write(row + 5, col + 5, bank.name, format2)
            s_no += 1

        workbook.close()
        fo = open(url + 'NEFT Statement.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'bank_details': out, 'bank_details_name': 'NEFT Statement.xlsx'})

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    pro_forma_number = fields.Char(string='Pro-forma Number', readonly=True, copy=False)
    pro_forma_generated = fields.Boolean(string='Pro Forma Generated', default=False)