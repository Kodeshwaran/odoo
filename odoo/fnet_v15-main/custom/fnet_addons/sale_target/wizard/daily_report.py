from odoo import models, fields, api, _
import base64
import xlsxwriter
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import io
from PIL import Image
#
# def compute_move_total(moves, credit_notes, partner_type, amount_fields):
#     moves_filtered = moves.filtered(lambda x: x.partner_id.is_new == partner_type)
#     credit_notes_filtered = credit_notes.filtered(lambda x: x.partner_id.is_new == partner_type) if credit_notes else 0
#     return sum(moves_filtered.mapped(amount_fields)) - sum(credit_notes_filtered.mapped(amount_fields))
#
#
# def compute_all_move_total(invoices, credit_notes, currency):
#     return sum(invoices.mapped(currency)) - sum(credit_notes.mapped(currency))


class DailyReport(models.TransientModel):
    _name = 'daily.report.old'
    _rec_name = 'report_details'
    _description = 'Daily Report Old'

    date_from = fields.Date('Date From', required=1)
    date_to = fields.Date('Date To', required=1)
    report_details = fields.Binary('Daily Report', readonly=True)
    report_attachment = fields.Many2one('ir.attachment', string="Report Attachment")
    report_details_name = fields.Char('Filename', size=64, readonly=True)

    def action_daily_report(self):
        url = '/tmp/'
        num_format2 = self.env.user.company_id.currency_id.excel_format
        num_format = '#0\.00,'
        workbook = xlsxwriter.Workbook(url + 'Daily Report.xlsx')
        sheet = workbook.add_worksheet('Billing Booking')
        company_format = workbook.add_format({'font_size': 12, 'bold': True, 'italic': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'right': 1,})
        title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF66', 'border': 1, 'right': 1, 'num_format': num_format + 'L'})
        sub_title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#90ee90', 'border': 1, 'right': 1, 'num_format': num_format + 'L'})
        parent_name_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'left', 'bg_color': '#F0CCB0', 'num_format': num_format})
        parent_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'right', 'valign': 'right', 'bg_color': '#F0CCB0', 'num_format': num_format})
        sale_type_name_format = workbook.add_format(
            {'font_size': 11, 'bold': True, 'align': 'left', 'valign': 'left', 'bg_color': '#D3D3D3', 'num_format': num_format})
        sale_type_format = workbook.add_format(
            {'font_size': 11, 'bold': True, 'align': 'right', 'valign': 'right', 'bg_color': '#D3D3D3', 'num_format': num_format})
        dr_amount_format = workbook.add_format(
            {'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#D3D3D3','num_format': num_format2})
        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'right', 'num_format': num_format})
        bold_1 = workbook.add_format({'align': 'right', 'valign': 'right', 'num_format': num_format})
        heading_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'num_format': num_format})
        bold_2 = workbook.add_format({'align': 'right', 'valign': 'right', 'num_format': num_format})
        format_1 = workbook.add_format({'align': 'right', 'valign': 'right'})
        format_2 = workbook.add_format({'align': 'right', 'valign': 'right'})
        format_left_align = workbook.add_format({'align': 'left', 'valign': 'left', 'num_format': num_format2})
        format_3 = workbook.add_format({'align': 'left', 'valign': 'left', 'num_format': num_format})
        format_4 = workbook.add_format({'align': 'right', 'valign': 'right', 'num_format': num_format2})
        sheet.set_row(2, 20)
        sheet.set_row(3, 40)
        sheet.set_row(5, 20)
        sheet.set_column('A:A', 20)
        sheet.set_column('B:Z', 13)
        sheet.set_column('AA:AU', 20)
        sheet.merge_range('A1:A2', '')
        # image_path = 'fnet.png'
        # image = Image.open(image_path)
        image_data = base64.b64decode(self.env.company.logo)
        image_stream = io.BytesIO(image_data)
        # sheet.add_image(image_data, 'A1')
        sheet.insert_image('A1', 'fnet.png', {'image_data': image_stream, 'x_scale': 0.5, 'y_scale': 0.5, 'object_position': 2, 'x_offset': 10, 'y_offset': 10, 'width': 200, 'height': 100})
        sheet.merge_range('B1:D2', self.env.company.name, company_format)
        sheet.merge_range('A4:D4', 'DAILY REPORT: %s to %s' % (self.date_from.strftime('%d-%m-%Y'), self.date_to.strftime('%d-%m-%Y')), heading_format)
        # sheet.write('B5:B5', 'TARGET', title_format)
        # sheet.write('C5:C5', 'BILLING AS ON...', title_format)
        # sheet.write('D5:D5', 'OPF', title_format)
        sheet.write(5, 0, 'DESCRIPTION', sub_title_format)
        # sheet.write(5, 1, 'EXISTING', sub_title_format)
        # sheet.write(5, 2, 'NEW', sub_title_format)
        sheet.write(5, 1, 'BUDGET', sub_title_format)
        # sheet.write(5, 2, 'EXISTING', sub_title_format)
        # sheet.write(5, 5, 'NEW', sub_title_format)
        sheet.write(5, 2, 'ACTUAL', sub_title_format)
        # sheet.write(5, 7, 'EXISTING', sub_title_format)
        # sheet.write(5, 8, 'NEW', sub_title_format)
        sheet.write(5, 3, 'OPF', sub_title_format)
        #Master Datas
        sale_type_ids = self.env['sale.type'].search([])

        move_search_domain = [
            ('state', 'in', ['posted']),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('sale_type_id', '!=', False),
            ('sales_sub_types', '!=', False)
        ]
        invoice_ids = self.env['account.move'].search(move_search_domain + [('move_type', '=', 'out_invoice')])
        credit_note_ids = self.env['account.move'].search(move_search_domain+[('move_type', '=', 'out_refund')])
        no_bill_invoice_ids = self.env['account.move'].search(move_search_domain+[('move_type', '=', 'out_invoice'), ('sales_sub_types.is_no_bill', '!=', False)])
        no_bill_credit_note_ids = self.env['account.move'].search(move_search_domain+[('move_type', '=', 'out_refund'), ('sales_sub_types.is_no_bill', '!=', False)])
        bill_ids = self.env['account.move'].search(move_search_domain+[('move_type', '=', 'in_invoice'), ('vendor_bill', '!=', False)])
        debit_note_ids = self.env['account.move'].search(move_search_domain+[('move_type', '=', 'in_refund'), ('vendor_bill', '!=', False)])
        expense_line_ids = self.env['account.move.line'].search([('move_id.state', 'in', ['posted']),
                                                        ('move_id.date', '>=', self.date_from),
                                                        ('move_id.date', '<=', self.date_to),
                                                        ('sale_type_id', '!=', False),
                                                        ('sales_sub_types', '!=', False),
                                                        ('move_id.move_type', '=', 'entry'),
                                                        ('move_id.reversed_entry_id', '=', False)
                                                    ])
        reversal_expense_line_ids = self.env['account.move.line'].search([('move_id.state', 'in', ['posted']),
                                                                 ('move_id.date', '>=', self.date_from),
                                                                 ('move_id.date', '<=', self.date_to),
                                                                 ('sale_type_id', '!=', False),
                                                                 ('sales_sub_types', '!=', False),
                                                                 ('move_id.move_type', '=', 'entry'),
                                                                 ('move_id.reversed_entry_id', '!=', False)
                                                                 ])
        financial_end_date = fields.Date.today().replace(day=31, month=3) + relativedelta(years=1) if fields.Date.today().month not in [1,2,3] else fields.Date.today().replace(day=31, month=3)
        sale_order_ids = self.env['sale.order'].search([('state', 'in', ['sale', 'done']),
                                                        ('date_order', '>=', self.date_from),
                                                        ('date_order', '<=', self.date_to),
                                                        ('sale_type_id', '!=', False),
                                                        ('sale_sub_type_id', '!=', False),
                                                        ('subscription_id', '=', False)])
        subscription_ids = self.env['sale.subscription'].search([('stage_category', '=', 'progress'),
                                                        ('date', '>=', fields.Date.today()),
                                                        ('date', '<=', financial_end_date),
                                                        ('template_id.code', '=', 'MON'),
                                                        ('sale_type_id', '!=', False),
                                                        ('sales_sub_types', '!=', False),
                                                        ])
        purchase_order_ids = self.env['purchase.order'].search([('state', 'in', ['purchase', 'done']),
                                                                ('date_approve', '>=', self.date_from),
                                                                ('date_approve', '<=', self.date_to),
                                                                ('sale_type_id', '!=', False),
                                                                ('sales_sub_types', '!=', False)])
        # Sale functionality section

        sheet.write(6, 0, 'A) Sales', parent_name_format)
        sheet.write(6, 1, sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_customer_target')) if sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_customer_target')) > 0 else '-', parent_format)
        # sheet.write(6, 2, sum(sale_type_ids.mapped('sales_sub_types').mapped('new_customer_target')), parent_format)
        # sheet.write(6, 3, sum(sale_type_ids.mapped('sales_sub_types').mapped('new_customer_target'))+sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_customer_target')), parent_format)

        sales_total_invoice_exist = sum(invoice_ids.mapped('amount_total_company')) - sum(credit_note_ids.mapped('amount_total_company'))
        # sales_total_invoice_exist = sum(invoice_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company'))
        # sales_total_invoice_new = sum(invoice_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company'))


        sheet.write(6, 2, sales_total_invoice_exist if sales_total_invoice_exist > 0 else '-', parent_format)
        # sheet.write(6, 5, sales_total_invoice_new, parent_format)
        # sheet.write(6, 6, sales_total_invoice_exist + sales_total_invoice_new, parent_format)

        # sheet.write(6, 7, sum(sale_order_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')), parent_format)
        # sheet.write(6, 3, sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')), parent_format)
        sheet.write(6, 3, sum(sale_order_ids.mapped('amount_residual_company')) + sum(subscription_ids.mapped('recurring_total_company')) if sum(sale_order_ids.mapped('amount_residual_company')) > 0 or sum(subscription_ids.mapped('recurring_total_company')) > 0 else '-', parent_format)
        # sheet.write(6, 9, sum(sale_order_ids.mapped('amount_total_company')), parent_format)
        row = 7
        for sale_type_id in sale_type_ids:
            sheet.write(row, 0, sale_type_id.name, sale_type_name_format)
            sheet.write(row, 1, sum(sale_type_id.mapped('sales_sub_types').mapped('existing_customer_target')) if sum(sale_type_id.mapped('sales_sub_types').mapped('existing_customer_target')) > 0 else '-', sale_type_format)
            # sheet.write(row, 2, sum(sale_type_id.mapped('sales_sub_types').mapped('new_customer_target')), sale_type_format)
            # sheet.write(row, 3, sum(sale_type_id.mapped('sales_sub_types').mapped('new_customer_target'))+sum(sale_type_id.mapped('sales_sub_types').mapped('existing_customer_target')), sale_type_format)

            sales_type_total_invoice_exist = sum(invoice_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company'))
            # sales_type_total_invoice_exist = sum(invoice_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company'))
            # sales_type_total_invoice_new = sum(invoice_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company'))

            sheet.write(row, 2, sales_type_total_invoice_exist if sales_type_total_invoice_exist > 0 else '-', sale_type_format)
            # sheet.write(row, 5, sales_type_total_invoice_new, sale_type_format)
            # sheet.write(row, 6, sales_type_total_invoice_exist + sales_type_total_invoice_new, sale_type_format)

            sheet.write(row, 3, sum(sale_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_residual_company')) + sum(subscription_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('recurring_total_company')) if sum(sale_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_residual_company')) > 0 or sum(subscription_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('recurring_total_company')) > 0 else '-', sale_type_format)
            # sheet.write(row, 7, sum(sale_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            # sheet.write(row, 8, sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            # sheet.write(row, 9, sum(sale_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            row += 1
            for sub_type_id in sale_type_id.sales_sub_types:
                sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                sheet.write(row, 0, sub_type_id.name, bold)
                sheet.write(row, 1, sub_type_id.existing_customer_target if sub_type_id.existing_customer_target > 0 else '-', bold_2)
                # sheet.write(row, 2, sub_type_id.new_customer_target, bold_2)
                # sheet.write(row, 3, sub_type_id.new_customer_target + sub_type_id.existing_customer_target, bold_2)
                sub_type_invoice_ids = invoice_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id)
                sales_subtype_total_invoice_exist = sum(invoice_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company'))
                # sales_subtype_total_invoice_exist = sum(invoice_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company'))
                # sales_subtype_total_invoice_new = sum(invoice_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company'))
                sheet.write(row, 2, sales_subtype_total_invoice_exist if sales_subtype_total_invoice_exist > 0 else '-', bold_2)
                # sheet.write(row, 5, sales_subtype_total_invoice_new, bold_2)
                # sheet.write(row, 6, sales_subtype_total_invoice_exist + sales_subtype_total_invoice_new, bold_2)

                sheet.write(row, 3, sum(sale_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')) + sum(subscription_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('recurring_total_company')) if sum(sale_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_residual_company')) > 0 or sum(subscription_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('recurring_total_company')) > 0 else '-', bold_2)
                # sheet.write(row, 8, sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')), bold_2)
                # sheet.write(row, 9, sum(sale_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')), bold_2)
                row += 1

        # Purchase functionality section

        sheet.write(row, 0, 'B) COGS', parent_name_format)
        sheet.write(row, 1, sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_vendor_target')) if sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_vendor_target')) > 0 else '-', parent_format)
        # sheet.write(row, 2, sum(sale_type_ids.mapped('sales_sub_types').mapped('new_vendor_target')), parent_format)
        # sheet.write(row, 3, sum(sale_type_ids.mapped('sales_sub_types').mapped('new_vendor_target')) + sum(bill_ids.mapped('sales_sub_types').mapped('existing_vendor_target')), parent_format)

        exist_no_bill_total = sum([(x.amount_total_company * x.sales_sub_types.existing_vendor_target_percent) for x in no_bill_invoice_ids]) - sum([(x.amount_total_company * x.sales_sub_types.existing_vendor_target_percent) for x in no_bill_credit_note_ids])
        # exist_no_bill_total = sum([(x.amount_total_company * x.sales_sub_types.existing_vendor_target_percent) for x in no_bill_invoice_ids if not x.partner_id.is_new]) - sum([(x.amount_total_company * x.sales_sub_types.existing_vendor_target_percent) for x in no_bill_credit_note_ids if not x.partner_id.is_new])
        # new_no_bill_total = sum([(x.amount_total_company * x.sales_sub_types.new_vendor_target_percent) for x in no_bill_invoice_ids if x.partner_id.is_new]) - sum([(x.amount_total_company * x.sales_sub_types.new_vendor_target_percent) for x in no_bill_credit_note_ids if x.partner_id.is_new])

        cogs_total_bill_exist = sum(bill_ids.mapped('amount_total_company')) - sum(debit_note_ids.mapped('amount_total_company'))
        # cogs_total_bill_exist = sum(bill_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company'))
        # cogs_total_bill_new = sum(bill_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company'))
        total_bill = exist_no_bill_total + cogs_total_bill_exist
        sheet.write(row, 2, total_bill if total_bill > 0 else '-', parent_format)
        # sheet.write(row, 5, new_no_bill_total + cogs_total_bill_new, parent_format)
        # sheet.write(row, 6, exist_no_bill_total + new_no_bill_total + cogs_total_bill_exist + cogs_total_bill_new, parent_format)

        sheet.write(row, 3, sum(purchase_order_ids.mapped('amount_total_company')) if sum(purchase_order_ids.mapped('amount_total_company')) > 0 else '-', parent_format)
        # sheet.write(row, 7, sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')), parent_format)
        # sheet.write(row, 8, sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')), parent_format)
        # sheet.write(row, 9, sum(purchase_order_ids.mapped('amount_total_company')), parent_format)
        row += 1
        for sale_type_id in sale_type_ids:
            sheet.write(row, 0, sale_type_id.name, sale_type_name_format)
            sheet.write(row, 1, sum(sale_type_id.mapped('sales_sub_types').mapped('existing_vendor_target')) if sum(sale_type_id.mapped('sales_sub_types').mapped('existing_vendor_target')) > 0 else '-', sale_type_format)
            # sheet.write(row, 2, sum(sale_type_id.mapped('sales_sub_types').mapped('new_vendor_target')), sale_type_format)
            # sheet.write(row, 3, sum(sale_type_id.mapped('sales_sub_types').mapped('new_vendor_target'))+sum(sale_type_id.mapped('sales_sub_types').mapped('existing_vendor_target')), sale_type_format)

            new_no_bill_type_total = 0
            exist_no_bill_type_total = 0
            for sub_type_id in sale_type_id.mapped('sales_sub_types').filtered(lambda x: x.is_no_bill):
                type_no_bill_ids = no_bill_invoice_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
                type_no_bill_credit_ids = no_bill_credit_note_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
                exist_no_bill_amount = sum(x.amount_total_company for x in type_no_bill_ids) - sum(x.amount_total_company for x in type_no_bill_credit_ids)
                # exist_no_bill_amount = sum(x.amount_total_company for x in type_no_bill_ids if not x.partner_id.is_new) - sum(x.amount_total_company for x in type_no_bill_credit_ids if not x.partner_id.is_new)
                # new_no_bill_amount = sum(x.amount_total_company for x in type_no_bill_ids if x.partner_id.is_new) - sum(x.amount_total_company for x in type_no_bill_credit_ids if x.partner_id.is_new)

                exist_no_bill_type_total += exist_no_bill_amount * sub_type_id.existing_vendor_target_percent
                # exist_no_bill_type_total += exist_no_bill_amount * sub_type_id.existing_vendor_target_percent
                # new_no_bill_type_total += new_no_bill_amount * sub_type_id.new_vendor_target_percent


            cogs_type_total_bill_exist = sum(bill_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company'))
            # cogs_type_total_bill_exist = sum(bill_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company'))
            # cogs_type_total_bill_new = sum(bill_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company'))
            total_bill2 = exist_no_bill_type_total + cogs_type_total_bill_exist
            sheet.write(row, 2, total_bill2 if total_bill2 > 0 else '-', sale_type_format)
            # sheet.write(row, 5, new_no_bill_type_total + cogs_type_total_bill_new, sale_type_format)
            # sheet.write(row, 6, exist_no_bill_type_total + new_no_bill_type_total + cogs_type_total_bill_new + cogs_type_total_bill_exist, sale_type_format)

            sheet.write(row, 3,  sum(purchase_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) if sum(purchase_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) > 0 else '-', sale_type_format)
            # sheet.write(row, 7,  sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            # sheet.write(row, 8, sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            # sheet.write(row, 9, sum(purchase_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            row += 1
            for sub_type_id in sale_type_id.sales_sub_types:
                sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                sheet.write(row, 0, sub_type_id.name, bold)
                sheet.write(row, 1, sub_type_id.existing_vendor_target if sub_type_id.existing_vendor_target > 0 else '-', bold_2)
                # sheet.write(row, 2, sub_type_id.new_vendor_target, bold_2)
                # sheet.write(row, 3, sub_type_id.new_vendor_target + sub_type_id.existing_vendor_target, bold_2)

                subtype_no_bill_ids = no_bill_invoice_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
                subtype_no_bill_credit_ids = no_bill_credit_note_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
                exist_no_bill_amount = sum(x.amount_total_company * sub_type_id.existing_vendor_target_percent for x in subtype_no_bill_ids) - sum(x.amount_total_company * sub_type_id.existing_vendor_target_percent for x in subtype_no_bill_credit_ids)
                # exist_no_bill_amount = sum(x.amount_total_company * sub_type_id.existing_vendor_target_percent for x in subtype_no_bill_ids if not x.partner_id.is_new) - sum(x.amount_total_company * sub_type_id.existing_vendor_target_percent for x in subtype_no_bill_credit_ids if not x.partner_id.is_new)
                # new_no_bill_amount = sum(x.amount_total_company - (x.amount_total_company * sub_type_id.existing_vendor_target_percent) for x in subtype_no_bill_ids if x.partner_id.is_new) - sum(x.amount_total_company - (x.amount_total_company * sub_type_id.existing_vendor_target_percent) for x in subtype_no_bill_credit_ids if x.partner_id.is_new)

                cogs_subtype_total_bill_exist = sum(bill_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company'))
                # cogs_subtype_total_bill_exist = sum(bill_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company'))
                # cogs_subtype_total_bill_new = sum(bill_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company'))
                total_bill3 = exist_no_bill_amount + cogs_subtype_total_bill_exist
                sheet.write(row, 2, total_bill3 if total_bill3 > 0 else '-', bold_2)
                # sheet.write(row, 5, new_no_bill_amount + cogs_subtype_total_bill_new, bold_2)
                # sheet.write(row, 6, new_no_bill_amount + exist_no_bill_amount + cogs_subtype_total_bill_exist + cogs_subtype_total_bill_new, bold_2)

                sheet.write(row, 3, sum(purchase_order_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company')) if sum(purchase_order_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company')) > 0 else '-', bold_2)
                # sheet.write(row, 7, sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')), bold_2)
                # sheet.write(row, 8, sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')), bold_2)
                # sheet.write(row, 9, sum(purchase_order_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')), bold_2)
                row += 1
        # Gross Margin functionalities start
        sheet.write(row, 0, 'C) Gross Margin', parent_name_format)
        gross_total = sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_customer_target')) - sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_vendor_target'))
        sheet.write(row, 1, gross_total if gross_total > 0 else '-', parent_format)
        # sheet.write(row, 2, sum(sale_type_ids.mapped('sales_sub_types').mapped('new_customer_target')) - sum(sale_type_ids.mapped('sales_sub_types').mapped('new_vendor_target')), parent_format)
        # sheet.write(row, 3, sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_customer_target')) - sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_vendor_target')) + sum(sale_type_ids.mapped('sales_sub_types').mapped('new_customer_target')) - sum(sale_type_ids.mapped('sales_sub_types').mapped('new_vendor_target')), parent_format)

        gross_total_exist = sales_total_invoice_exist - cogs_total_bill_exist - exist_no_bill_total
        # gross_total_new = sales_total_invoice_new - cogs_total_bill_new - new_no_bill_total

        sheet.write(row, 2, gross_total_exist if gross_total_exist > 0 else '-', parent_format)
        # sheet.write(row, 5, gross_total_new, parent_format)
        # sheet.write(row, 6, gross_total_exist + gross_total_new, parent_format)
        gross_total1 = sum(sale_order_ids.mapped('amount_total_company')) - sum(purchase_order_ids.mapped('amount_total_company'))
        sheet.write(row, 3, gross_total1 if gross_total1 > 0 else '-', parent_format)
        # sheet.write(row, 7, sum(sale_order_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')), parent_format)
        # sheet.write(row, 8, sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')), parent_format)
        # sheet.write(row, 9, sum(sale_order_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')) + sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')), parent_format)
        row += 1
        for sale_type_id in sale_type_ids:
            sheet.write(row, 0, sale_type_id.name, sale_type_name_format)
            gross_total3 = sum(sale_type_id.mapped('sales_sub_types').mapped('existing_customer_target')) - sum(sale_type_id.mapped('sales_sub_types').mapped('existing_vendor_target'))
            sheet.write(row, 1, gross_total3 if gross_total3 > 0 else '-', sale_type_format)
            # sheet.write(row, 2, sum(sale_type_id.mapped('sales_sub_types').mapped('new_customer_target')) - sum(sale_type_id.mapped('sales_sub_types').mapped('new_vendor_target')), sale_type_format)
            # sheet.write(row, 3, sum(sale_type_id.mapped('sales_sub_types').mapped('existing_customer_target')) - sum(sale_type_id.mapped('sales_sub_types').mapped('existing_vendor_target'))+sum(sale_type_id.mapped('sales_sub_types').mapped('new_customer_target')) - sum(sale_type_id.mapped('sales_sub_types').mapped('new_vendor_target')), sale_type_format)

            new_no_bill_type_total = 0
            exist_no_bill_type_total = 0
            for sub_type_id in sale_type_id.mapped('sales_sub_types').filtered(lambda x: x.is_no_bill):
                type_no_bill_ids = no_bill_invoice_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
                type_no_bill_credit_ids = no_bill_credit_note_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
                exist_no_bill_amount = sum(x.amount_total_company for x in type_no_bill_ids) - sum(x.amount_total_company for x in type_no_bill_credit_ids)
                # exist_no_bill_amount = sum(x.amount_total_company for x in type_no_bill_ids if not x.partner_id.is_new) - sum(x.amount_total_company for x in type_no_bill_credit_ids if not x.partner_id.is_new)
                # new_no_bill_amount = sum(x.amount_total_company for x in type_no_bill_ids if x.partner_id.is_new) - sum(x.amount_total_company for x in type_no_bill_ids if x.partner_id.is_new)

                exist_no_bill_type_total += exist_no_bill_amount * (1 - sub_type_id.existing_vendor_target_percent)
                # new_no_bill_type_total += new_no_bill_amount * (1 - sub_type_id.new_vendor_target_percent)

            gross_type_total_exist = (sum(invoice_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id and not x.sales_sub_types.is_no_bill).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and not x.sales_sub_types.is_no_bill).mapped('amount_total_company'))) - (sum(bill_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')))
            # gross_type_total_exist = (sum(invoice_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and not x.sales_sub_types.is_no_bill).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and not x.sales_sub_types.is_no_bill).mapped('amount_total_company'))) - (sum(bill_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')))
            # gross_type_total_new = (sum(invoice_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and not x.sales_sub_types.is_no_bill).mapped('amount_total_company')) - sum(credit_note_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and not x.sales_sub_types.is_no_bill).mapped('amount_total_company'))) - (sum(bill_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(debit_note_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')))
            gross_total4 = gross_type_total_exist + exist_no_bill_type_total
            sheet.write(row, 2, gross_total4 if gross_total4 > 0 else '-', sale_type_format)
            # sheet.write(row, 5, gross_type_total_new + new_no_bill_type_total, sale_type_format)
            # sheet.write(row, 6, gross_type_total_exist + gross_type_total_new + exist_no_bill_type_total + new_no_bill_type_total, sale_type_format)
            gross_total5 = sum(sale_order_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company'))
            sheet.write(row, 3, gross_total5 if gross_total5 > 0 else '-', sale_type_format)
            # sheet.write(row, 7, sum(sale_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            # sheet.write(row, 8, sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            # sheet.write(row, 9, sum(sale_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) + sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')), sale_type_format)
            row += 1
            for sub_type_id in sale_type_id.sales_sub_types:
                sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                sheet.write(row, 0, sub_type_id.name, bold)
                gross_total_sale_type = sub_type_id.existing_customer_target - sub_type_id.existing_vendor_target
                sheet.write(row, 1, gross_total_sale_type if gross_total_sale_type > 0 else '-', bold_2)
                # sheet.write(row, 2, sub_type_id.new_customer_target - sub_type_id.new_vendor_target, bold_2)
                # sheet.write(row, 3, sub_type_id.existing_customer_target - sub_type_id.existing_vendor_target + sub_type_id.new_customer_target - sub_type_id.new_vendor_target, bold_2)

                subtype_no_bill_ids = no_bill_invoice_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
                subtype_no_bill_credit_ids = no_bill_credit_note_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
                exist_no_bill_amount = sum(x.amount_total_company * (1 - sub_type_id.existing_vendor_target_percent) for x in subtype_no_bill_ids) - sum(x.amount_total_company * (1 - sub_type_id.existing_vendor_target_percent) for x in subtype_no_bill_credit_ids)
                # exist_no_bill_amount = sum(x.amount_total_company * (1 - sub_type_id.existing_vendor_target_percent) for x in subtype_no_bill_ids if not x.partner_id.is_new) - sum(x.amount_total_company * (1 - sub_type_id.existing_vendor_target_percent) for x in subtype_no_bill_credit_ids if not x.partner_id.is_new)
                # new_no_bill_amount = sum(x.amount_total_company * (1 * sub_type_id.new_vendor_target_percent) for x in subtype_no_bill_ids if x.partner_id.is_new) - sum(x.amount_total_company - (x.amount_total_company * sub_type_id.new_vendor_target_percent) for x in subtype_no_bill_credit_ids if x.partner_id.is_new)

                gross_subtype_total_exist = (sum(invoice_ids.filtered(
                    lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id and not x.sales_sub_types.is_no_bill).mapped(
                    'amount_total_company')) - sum(credit_note_ids.filtered(
                    lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id and not x.sales_sub_types.is_no_bill).mapped(
                    'amount_total_company'))) - (sum(bill_ids.filtered(
                    lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                    'amount_total_company')) - sum(debit_note_ids.filtered(
                    lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                    'amount_total_company')))
                # gross_subtype_total_new = (sum(invoice_ids.filtered(
                #     lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company')) - sum(credit_note_ids.filtered(
                #     lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company'))) - (sum(bill_ids.filtered(
                #     lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company')) - sum(debit_note_ids.filtered(
                #     lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company')))
                # gross_subtype_total_exist = (sum(invoice_ids.filtered(
                #     lambda
                #         x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id and not x.sales_sub_types.is_no_bill).mapped(
                #     'amount_total_company')) - sum(credit_note_ids.filtered(
                #     lambda
                #         x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id and not x.sales_sub_types.is_no_bill).mapped(
                #     'amount_total_company'))) - (sum(bill_ids.filtered(
                #     lambda
                #         x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company')) - sum(debit_note_ids.filtered(
                #     lambda
                #         x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company')))
                # gross_subtype_total_new = (sum(invoice_ids.filtered(
                #     lambda
                #         x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company')) - sum(credit_note_ids.filtered(
                #     lambda
                #         x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company'))) - (sum(bill_ids.filtered(
                #     lambda
                #         x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company')) - sum(debit_note_ids.filtered(
                #     lambda
                #         x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped(
                #     'amount_total_company')))
                gross_total_sale_sub_type = gross_subtype_total_exist + exist_no_bill_amount
                sheet.write(row, 2, gross_total_sale_sub_type if gross_total_sale_sub_type > 0 else '-', bold_2)
                # sheet.write(row, 5, gross_subtype_total_new + new_no_bill_amount, bold_2)
                # sheet.write(row, 6, gross_subtype_total_exist + gross_subtype_total_new + exist_no_bill_amount + new_no_bill_amount, bold_2)
                gross_total6 = sum(sale_order_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x:x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('amount_total_company'))
                sheet.write(row, 7, gross_total6 if gross_total6 > 0 else '-', bold_2)
                # sheet.write(row, 7, sum(sale_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')), bold_2)
                # sheet.write(row, 8, sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')), bold_2)
                # sheet.write(row, 9, sum(sale_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')) + sum(sale_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')) - sum(purchase_order_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id and x.sale_sub_type_id.id == sub_type_id.id).mapped('amount_total_company')), bold_2)
                row += 1
        # Expense functionality
        # sheet.write(row, 0, 'D) Direct Expenses', parent_format)
        # sheet.write(row, 1, sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_expense_target')), parent_format)
        # sheet.write(row, 2, sum(sale_type_ids.mapped('sales_sub_types').mapped('new_expense_target')), parent_format)
        # sheet.write(row, 3, sum(sale_type_ids.mapped('sales_sub_types').mapped('new_expense_target')) + sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_expense_target')), parent_format)
        #
        # sheet.write(row, 4, sum(expense_line_ids.mapped('debit')) - sum(reversal_expense_line_ids.mapped('credit')), parent_format)
        # sheet.write(row, 5, 0, parent_format)
        # sheet.write(row, 6, sum(expense_line_ids.mapped('debit')) - sum(reversal_expense_line_ids.mapped('credit')), parent_format)
        # row += 1
        # for sale_type_id in sale_type_ids:
        #     sheet.write(row, 0, sale_type_id.name, sale_type_format)
        #     sheet.write(row, 1, sum(sale_type_id.mapped('sales_sub_types').mapped('existing_expense_target')), sale_type_format)
        #     sheet.write(row, 2, sum(sale_type_id.mapped('sales_sub_types').mapped('new_expense_target')), sale_type_format)
        #     sheet.write(row, 3, sum(sale_type_id.mapped('sales_sub_types').mapped('new_expense_target')) + sum(sale_type_id.mapped('sales_sub_types').mapped('existing_expense_target')), sale_type_format)
        #
        #     sheet.write(row, 4, sum(expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('debit')) - sum(reversal_expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('credit')), sale_type_format)
        #     sheet.write(row, 5, 0,sale_type_format)
        #     sheet.write(row, 6, sum(expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('debit')) - sum(reversal_expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('credit')), sale_type_format)
        #     row += 1
        #     for sub_type_id in sale_type_id.sales_sub_types:
        #         sheet.write(row, 0, sub_type_id.name, bold)
        #         sheet.write(row, 1, sub_type_id.existing_expense_target, bold_2)
        #         sheet.write(row, 2, sub_type_id.new_expense_target, bold_2)
        #         sheet.write(row, 3, sub_type_id.new_expense_target + sub_type_id.existing_expense_target, bold_2)
        #
        #         sheet.write(row, 4, sum(expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('debit')) - sum(reversal_expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('credit')), bold_2)
        #         sheet.write(row, 5, 0, bold_2)
        #         sheet.write(row, 6, sum(expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('debit')) - sum(reversal_expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.sales_sub_types.id == sub_type_id.id).mapped('credit')), bold_2)
        #         row += 1
        #
        # #Profit Functionalities
        #
        # margin_existing_target = sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_customer_target')) - sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_vendor_target'))
        # margin_new_target = sum(sale_type_ids.mapped('sales_sub_types').mapped('new_customer_target')) - sum(sale_type_ids.mapped('sales_sub_types').mapped('new_vendor_target'))
        # margin_total_target = sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_customer_target')) - sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_vendor_target')) + sum(sale_type_ids.mapped('sales_sub_types').mapped('new_customer_target')) - sum(sale_type_ids.mapped('sales_sub_types').mapped('new_vendor_target'))
        #
        # sheet.write(row, 0, 'E) Gross Profit', parent_format)
        # sheet.write(row, 1, margin_existing_target - sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_expense_target')), parent_format)
        # sheet.write(row, 2, margin_new_target - sum(sale_type_ids.mapped('sales_sub_types').mapped('new_expense_target')), parent_format)
        # sheet.write(row, 3, margin_total_target - sum(sale_type_ids.mapped('sales_sub_types').mapped('new_expense_target')) + sum(sale_type_ids.mapped('sales_sub_types').mapped('existing_expense_target')), parent_format)
        #
        # margin_existing_amount = sales_total_invoice_exist - cogs_total_bill_exist - exist_no_bill_total
        # margin_new_amount = sales_total_invoice_new - cogs_total_bill_new - new_no_bill_total
        # margin_total_amount = sales_total_invoice_exist - cogs_total_bill_exist - exist_no_bill_total + sales_total_invoice_new - cogs_total_bill_new - new_no_bill_total
        # sheet.write(row, 4, margin_existing_amount - (sum(expense_line_ids.mapped('debit')) - sum(reversal_expense_line_ids.mapped('credit'))), parent_format)
        # sheet.write(row, 5, margin_new_amount, parent_format)
        # sheet.write(row, 6, margin_total_amount - (sum(expense_line_ids.mapped('debit')) - sum(reversal_expense_line_ids.mapped('credit'))), parent_format)
        # row += 1
        # for sale_type_id in sale_type_ids:
        #     margin_existing_sub_target = sum(sale_type_id.mapped('sales_sub_types').mapped('existing_expense_target'))
        #     margin_new_sub_target = sum(sale_type_id.mapped('sales_sub_types').mapped('new_expense_target'))
        #     margin_total_sub_target = sum(sale_type_id.mapped('sales_sub_types').mapped('new_expense_target')) + sum(sale_type_id.mapped('sales_sub_types').mapped('existing_expense_target'))
        #
        #     sheet.write(row, 0, sale_type_id.name, sale_type_format)
        #     sheet.write(row, 1, margin_existing_sub_target - sum(sale_type_id.mapped('sales_sub_types').mapped('existing_expense_target')), sale_type_format)
        #     sheet.write(row, 2, margin_new_sub_target - sum(sale_type_id.mapped('sales_sub_types').mapped('new_expense_target')), sale_type_format)
        #     sheet.write(row, 3, margin_total_sub_target - sum(sale_type_id.mapped('sales_sub_types').mapped('new_expense_target')) + sum(sale_type_id.mapped('sales_sub_types').mapped('existing_expense_target')), sale_type_format)
        #
        #     new_no_bill_type_total = 0
        #     exist_no_bill_type_total = 0
        #     for sub_type_id in sale_type_id.mapped('sales_sub_types').filtered(lambda x: x.is_no_bill):
        #         type_no_bill_ids = no_bill_invoice_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
        #         type_no_bill_credit_ids = no_bill_credit_note_ids.filtered(lambda x: x.sales_sub_types.id == sub_type_id.id)
        #         exist_no_bill_amount = sum(x.amount_total_company for x in type_no_bill_ids if not x.partner_id.is_new) - sum(x.amount_total_company for x in type_no_bill_credit_ids if not x.partner_id.is_new)
        #         new_no_bill_amount = sum(x.amount_total_company for x in type_no_bill_ids if x.partner_id.is_new) - sum(x.amount_total_company for x in type_no_bill_credit_ids if x.partner_id.is_new)
        #
        #         exist_no_bill_type_total += exist_no_bill_amount * sub_type_id.existing_vendor_target_percent
        #         new_no_bill_type_total += new_no_bill_amount * sub_type_id.existing_vendor_target_percent
        #
        #     gross_type_total_exist = (sum(invoice_ids.filtered(
        #         lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped(
        #         'amount_total_company')) - sum(credit_note_ids.filtered(
        #         lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped(
        #         'amount_total_company'))) - (sum(bill_ids.filtered(
        #         lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped(
        #         'amount_total_company')) - sum(debit_note_ids.filtered(
        #         lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped(
        #         'amount_total_company'))) - exist_no_bill_type_total
        #     gross_type_total_new = (sum(invoice_ids.filtered(
        #         lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped(
        #         'amount_total_company')) - sum(
        #         credit_note_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped(
        #             'amount_total_company'))) - (sum(bill_ids.filtered(
        #         lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped(
        #         'amount_total_company')) - sum(
        #         debit_note_ids.filtered(lambda x: x.partner_id.is_new and x.sale_type_id.id == sale_type_id.id).mapped(
        #             'amount_total_company'))) - new_no_bill_type_total
        #
        #     margin_existing_sub_amount = gross_type_total_exist
        #     margin_new_sub_amount = gross_type_total_new
        #     # margin_total_sub_amount = sum(invoice_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - sum(bill_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('amount_total_company')) - new_no_bill_type_total - new_no_bill_type_total
        #
        #     sheet.write(row, 4, margin_existing_sub_amount - (sum(expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('debit')) - sum(reversal_expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('credit'))), sale_type_format)
        #     sheet.write(row, 5, margin_new_sub_amount, sale_type_format)
        #     sheet.write(row, 6, gross_type_total_exist + margin_new_sub_amount - (sum(expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('debit')) - - sum(reversal_expense_line_ids.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('credit'))), sale_type_format)
        #     row += 1

        # DR Sheet

        sheet_2 = workbook.add_worksheet('Dr')
        sheet_2.set_column('A:A', 5)
        sheet_2.set_column('B:B', 35)
        sheet_2.set_column('C:C', 15)
        sheet_2.set_column('D:J', 13)
        sheet_2.merge_range('A1:J1', 'Sundry Debtor As On : %s' % fields.Date.today().strftime('%d-%m-%Y'), bold_1)
        sheet_2.write(2, 0, 'Sno', sub_title_format)
        sheet_2.write(2, 1, 'Customer Name', sub_title_format)
        sheet_2.write(2, 2, 'Sales Person', sub_title_format)
        sheet_2.write(2, 3, 'Sales Team', sub_title_format)
        sheet_2.write(2, 4, 'Collection Person', sub_title_format)
        sheet_2.write(2, 5, '0-30', sub_title_format)
        sheet_2.write(2, 6, '30-45', sub_title_format)
        sheet_2.write(2, 7, '45-60', sub_title_format)
        sheet_2.write(2, 8, '60-90', sub_title_format)
        sheet_2.write(2, 9, '90-120', sub_title_format)
        sheet_2.write(2, 10, 'Above 120', sub_title_format)

        invoice_ids = self.env['account.move'].search([('state', 'in', ['posted']),
                                                       ('invoice_date', '<=', self.date_to),
                                                       ('move_type', '=', 'out_invoice'),
                                                       ('amount_residual_company', '>', 0),
                                                       ])
        s_no = 1
        row = 3
        today = fields.Date.today()
        days_30 = fields.Date.today() - timedelta(days=30)
        days_45 = fields.Date.today() - timedelta(days=45)
        days_60 = fields.Date.today() - timedelta(days=60)
        days_90 = fields.Date.today() - timedelta(days=90)
        days_120 = fields.Date.today() - timedelta(days=120)
        for partner_id in invoice_ids.mapped('partner_id').sorted(key=lambda l: l.name or l.parent_id.name):
            invoice_ids_0_30 = invoice_ids.filtered(lambda x: x.invoice_date > days_30 and x.invoice_date <= today and x.partner_id.id == partner_id.id)
            invoice_ids_30_45 = invoice_ids.filtered(lambda x: x.invoice_date > days_45 and x.invoice_date < days_30 and x.partner_id.id == partner_id.id)
            invoice_ids_45_60 = invoice_ids.filtered(lambda x: x.invoice_date > days_60 and x.invoice_date < days_45 and x.partner_id.id == partner_id.id)
            invoice_ids_60_90 = invoice_ids.filtered(lambda x: x.invoice_date > days_90 and x.invoice_date < days_60 and x.partner_id.id == partner_id.id)
            invoice_ids_90_120 = invoice_ids.filtered(lambda x: x.invoice_date > days_120 and x.invoice_date < days_90 and x.partner_id.id == partner_id.id)
            invoice_ids_120_above = invoice_ids.filtered(lambda x: x.invoice_date <= days_120 and x.partner_id.id == partner_id.id)

            sheet_2.write(row, 0, s_no, format_1)
            sheet_2.write(row, 1, partner_id.name, format_left_align)
            sheet_2.write(row, 2, partner_id.user_id.name if partner_id.user_id else '', format_left_align)
            sheet_2.write(row, 3, partner_id.team_id.name if partner_id.team_id else '', format_left_align)
            sheet_2.write(row, 4, partner_id.collection_person.name if partner_id.collection_person else '', format_left_align)
            sheet_2.write(row, 5, sum(invoice_ids_0_30.mapped('amount_residual_company')), format_4)
            sheet_2.write(row, 6, sum(invoice_ids_30_45.mapped('amount_residual_company')), format_4)
            sheet_2.write(row, 7, sum(invoice_ids_45_60.mapped('amount_residual_company')), format_4)
            sheet_2.write(row, 8, sum(invoice_ids_60_90.mapped('amount_residual_company')), format_4)
            sheet_2.write(row, 9, sum(invoice_ids_90_120.mapped('amount_residual_company')), format_4)
            sheet_2.write(row, 10, sum(invoice_ids_120_above.mapped('amount_residual_company')), format_4)
            row += 1
            s_no += 1
        invoice_ids_0_30_total = invoice_ids.filtered(lambda x: x.invoice_date > days_30 and x.invoice_date <= today)
        invoice_ids_30_45_total = invoice_ids.filtered(lambda x: x.invoice_date > days_45 and x.invoice_date < days_30)
        invoice_ids_45_60_total = invoice_ids.filtered(lambda x: x.invoice_date > days_60 and x.invoice_date < days_45)
        invoice_ids_60_90_total = invoice_ids.filtered(lambda x: x.invoice_date > days_90 and x.invoice_date < days_60)
        invoice_ids_90_120_total = invoice_ids.filtered(lambda x: x.invoice_date > days_120 and x.invoice_date < days_90)
        invoice_ids_120_above_total = invoice_ids.filtered(lambda x: x.invoice_date <= days_120)
        sheet_2.write(row, 4, "Total", sale_type_format)
        sheet_2.write(row, 5, sum(invoice_ids_0_30_total.mapped('amount_residual_company')), dr_amount_format)
        sheet_2.write(row, 6, sum(invoice_ids_30_45_total.mapped('amount_residual_company')), dr_amount_format)
        sheet_2.write(row, 7, sum(invoice_ids_45_60_total.mapped('amount_residual_company')), dr_amount_format)
        sheet_2.write(row, 8, sum(invoice_ids_60_90_total.mapped('amount_residual_company')), dr_amount_format)
        sheet_2.write(row, 9, sum(invoice_ids_90_120_total.mapped('amount_residual_company')), dr_amount_format)
        sheet_2.write(row, 10, sum(invoice_ids_120_above_total.mapped('amount_residual_company')), dr_amount_format)

        # Funnel Sheet

        sheet_3 = workbook.add_worksheet('Funnel')
        sheet_3.set_column('A:A', 15)
        sheet_3.set_column('B:B', 30)
        sheet_3.set_column('C:C', 30)
        sheet_3.set_column('D:D', 25)
        sheet_3.set_column('E:E', 20)
        sheet_3.set_column('F:F', 15)
        sheet_3.set_column('G:I', 15)
        sheet_3.set_column('J:L', 10)
        sheet_3.write(0, 0, 'Sales Person', sub_title_format)
        sheet_3.write(0, 1, 'Customer', sub_title_format)
        sheet_3.write(0, 2, 'Company Name', sub_title_format)
        sheet_3.write(0, 3, 'Opportunity', sub_title_format)
        sheet_3.write(0, 4, 'Expected Revenue', sub_title_format)
        sheet_3.write(0, 5, 'Value BL', sub_title_format)
        sheet_3.write(0, 6, 'Probability', sub_title_format)
        sheet_3.write(0, 7, 'Stage', sub_title_format)
        sheet_3.write(0, 8, 'Expected Closing', sub_title_format)
        sheet_3.write(0, 9, 'Month', sub_title_format)
        sheet_3.write(0, 10, 'Year', sub_title_format)
        sheet_3.write(0, 11, 'March Billing probability', sub_title_format)

        lead_ids = self.env['crm.lead'].search([('stage_id.is_won', '=', False), ('stage_id.is_dropped', '=', False), ('stage_id.is_hold', '=', False)], order='create_date DESC')
        row = 1
        for lead in lead_ids:
            sheet_3.write(row, 0, lead.user_id.name, format_left_align)
            sheet_3.write(row, 1, lead.partner_id.name if lead.partner_id else '', format_left_align)
            sheet_3.write(row, 2, lead.partner_name if lead.partner_name else '', format_left_align)
            sheet_3.write(row, 3, lead.name, format_left_align)
            sheet_3.write(row, 4, lead.expected_revenue, format_4)
            sheet_3.write(row, 5, lead.value_bl, format_4)
            sheet_3.write(row, 6, lead.probability, format_2)
            sheet_3.write(row, 7, lead.stage_id.name, format_2)
            sheet_3.write(row, 8, lead.date_deadline.strftime('%d/%m/%Y') if lead.date_deadline else '', format_2)
            sheet_3.write(row, 9, lead.date_deadline.strftime('%b') if lead.date_deadline else '', format_3)
            sheet_3.write(row, 10, lead.date_deadline.strftime('%Y') if lead.date_deadline else '', format_3)
            sheet_3.write(row, 11, '', format_2)
            row += 1

        # DSR Sheet

        sheet_4 = workbook.add_worksheet('DSR')
        sheet_4.set_column('A:A', 5)
        sheet_4.set_column('B:C', 15)
        sheet_4.set_column('C:C', 35)
        sheet_4.set_column('D:D', 35)
        sheet_4.set_column('E:E', 15)
        sheet_4.set_column('F:F', 50)
        sheet_4.write(0, 0, 'Sno', sub_title_format)
        sheet_4.write(0, 1, 'Sales Person', sub_title_format)
        sheet_4.write(0, 2, 'Sales Team', sub_title_format)
        sheet_4.write(0, 3, 'Customers Met', sub_title_format)
        sheet_4.write(0, 4, 'Date', sub_title_format)
        sheet_4.write(0, 5, 'Out Come', sub_title_format)

        date_from = fields.Date.today() - timedelta(days=3)
        date_to = fields.Date.today() - timedelta(days=1)
        dsr_ids = self.env['voip.phonecall'].search([('call_date', '>=', date_from), ('call_date', '<=', date_to)], order='call_date DESC')
        row = 1
        s_no = 1
        for dsr in dsr_ids:
            team_id = self.env['crm.team'].search([('member_ids', 'in', [dsr.user_id.id])], limit=1)
            sheet_4.write(row, 0, s_no, format_1)
            sheet_4.write(row, 1, dsr.user_id.name, format_left_align)
            sheet_4.write(row, 2, team_id.name or '', format_left_align)
            sheet_4.write(row, 3, dsr.contact_name or '', format_left_align)
            sheet_4.write(row, 4, dsr.call_date.strftime('%d/%m/%Y'), format_2)
            sheet_4.write(row, 5, dsr.note, format_2)
            row += 1
            s_no += 1

        #Debtors

        sheet_2 = workbook.add_worksheet('Debtors')
        sheet_2.set_column('A:A', 5)
        sheet_2.set_column('B:B', 25)
        sheet_2.set_column('C:C', 30)
        sheet_2.set_column('D:D', 20)
        sheet_2.set_column('E:E', 25)
        sheet_2.set_column('F:F', 25)
        sheet_2.set_column('G:P', 20)
        # sheet_2.merge_range('A1:J1', 'Debtor As On : %s' % fields.Date.today().strftime('%d-%m-%Y'), bold_1)
        sheet_2.write(2, 0, 'Sno', sub_title_format)
        sheet_2.write(2, 1, 'Number', sub_title_format)
        sheet_2.write(2, 2, 'Customer Name', sub_title_format)
        sheet_2.write(2, 3, 'Invoice Date', sub_title_format)
        sheet_2.write(2, 4, 'Collection Person', sub_title_format)
        sheet_2.write(2, 5, 'Salesperson', sub_title_format)
        sheet_2.write(2, 6, 'Amount Due', sub_title_format)
        sheet_2.write(2, 7, 'As of: %s' % fields.Date.today().strftime('%d-%m-%Y'), sub_title_format)
        sheet_2.write(2, 8, '1-30', sub_title_format)
        sheet_2.write(2, 9, '31-60', sub_title_format)
        sheet_2.write(2, 10, '61-90', sub_title_format)
        sheet_2.write(2, 11, '91-120', sub_title_format)
        sheet_2.write(2, 12, 'Older', sub_title_format)
        # sheet_2.write(2, 13, 'Total', sub_title_format)

        invoice_ids = self.env['account.move'].search([('state', 'in', ['posted']),
                                                       ('invoice_date', '<=', self.date_to),
                                                       ('move_type', '=', 'out_invoice'),
                                                       ('amount_residual_company', '>', 0),
                                                       ])
        s_no = 1
        row = 3
        today = fields.Date.today()
        days_30 = fields.Date.today() - timedelta(days=30)
        days_45 = fields.Date.today() - timedelta(days=45)
        days_60 = fields.Date.today() - timedelta(days=60)
        days_90 = fields.Date.today() - timedelta(days=90)
        days_120 = fields.Date.today() - timedelta(days=120)
        for invoice in invoice_ids.filtered(lambda x: x.invoice_date == fields.Date.today()):
            sheet_2.write(row, 0, s_no, format_1)
            sheet_2.write(row, 1, invoice.name, format_2)
            sheet_2.write(row, 2, invoice.partner_id.name, format_2)
            sheet_2.write(row, 3, invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else '', format_2)
            sheet_2.write(row, 4, invoice.collection_person.name if invoice.collection_person else '', format_left_align)
            sheet_2.write(row, 5, invoice.user_id.name if invoice.user_id else '', format_left_align)
            sheet_2.write(row, 6, invoice.amount_residual_company, format_left_align)
            sheet_2.write(row, 7, invoice.amount_residual_company, format_4)
            sheet_2.write(row, 8, '', format_4)
            sheet_2.write(row, 9, '', format_4)
            sheet_2.write(row, 10, '', format_4)
            sheet_2.write(row, 11, '', format_4)
            sheet_2.write(row, 12, '', format_4)
            # sheet_2.write(row, 13, invoice.amount_residual_company, format_4)
            row += 1
            s_no += 1
        yesterday = fields.Date.today() - timedelta(days=1)
        for invoice in invoice_ids.filtered(lambda x: x.invoice_date > days_30 and x.invoice_date <= yesterday):
            sheet_2.write(row, 0, s_no, format_1)
            sheet_2.write(row, 1, invoice.name, format_2)
            sheet_2.write(row, 2, invoice.partner_id.name, format_2)
            sheet_2.write(row, 3, invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else '', format_2)
            sheet_2.write(row, 4, invoice.collection_person.name if invoice.collection_person else '', format_left_align)
            sheet_2.write(row, 5, invoice.user_id.name if invoice.user_id else '', format_left_align)
            sheet_2.write(row, 6, invoice.amount_residual_company, format_left_align)
            sheet_2.write(row, 7, '', format_4)
            sheet_2.write(row, 8, invoice.amount_residual_company, format_4)
            sheet_2.write(row, 9, '', format_4)
            sheet_2.write(row, 10, '', format_4)
            sheet_2.write(row, 11, '', format_4)
            sheet_2.write(row, 12, '', format_4)
            # sheet_2.write(row, 13, invoice.amount_residual_company, format_4)
            row += 1
            s_no += 1
        for invoice in invoice_ids.filtered(lambda x: x.invoice_date > days_60 and x.invoice_date <= days_30):
            sheet_2.write(row, 0, s_no, format_1)
            sheet_2.write(row, 1, invoice.name, format_2)
            sheet_2.write(row, 2, invoice.partner_id.name, format_2)
            sheet_2.write(row, 3, invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else '', format_2)
            sheet_2.write(row, 4, invoice.collection_person.name if invoice.collection_person else '', format_left_align)
            sheet_2.write(row, 5, invoice.user_id.name if invoice.user_id else '', format_left_align)
            sheet_2.write(row, 6, invoice.amount_residual_company, format_left_align)
            sheet_2.write(row, 7, '', format_4)
            sheet_2.write(row, 8, '', format_4)
            sheet_2.write(row, 9, invoice.amount_residual_company, format_4)
            sheet_2.write(row, 10, '', format_4)
            sheet_2.write(row, 11, '', format_4)
            sheet_2.write(row, 12, '', format_4)
            # sheet_2.write(row, 13, invoice.amount_residual_company, format_4)
            row += 1
            s_no += 1
        for invoice in invoice_ids.filtered(lambda x: x.invoice_date > days_90 and x.invoice_date <= days_60):
            sheet_2.write(row, 0, s_no, format_1)
            sheet_2.write(row, 1, invoice.name, format_2)
            sheet_2.write(row, 2, invoice.partner_id.name, format_2)
            sheet_2.write(row, 3, invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else '', format_2)
            sheet_2.write(row, 4, invoice.collection_person.name if invoice.collection_person else '', format_left_align)
            sheet_2.write(row, 5, invoice.user_id.name if invoice.user_id else '', format_left_align)
            sheet_2.write(row, 6, invoice.amount_residual_company, format_left_align)
            sheet_2.write(row, 7, '', format_4)
            sheet_2.write(row, 8, '', format_4)
            sheet_2.write(row, 9, '', format_4)
            sheet_2.write(row, 10, invoice.amount_residual_company, format_4)
            sheet_2.write(row, 11, '', format_4)
            sheet_2.write(row, 12, '', format_4)
            # sheet_2.write(row, 13, invoice.amount_residual_company, format_4)
            row += 1
            s_no += 1
        for invoice in invoice_ids.filtered(lambda x: x.invoice_date > days_120 and x.invoice_date <= days_90):
            sheet_2.write(row, 0, s_no, format_1)
            sheet_2.write(row, 1, invoice.name, format_2)
            sheet_2.write(row, 2, invoice.partner_id.name, format_2)
            sheet_2.write(row, 3, invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else '', format_2)
            sheet_2.write(row, 4, invoice.collection_person.name if invoice.collection_person else '', format_left_align)
            sheet_2.write(row, 5, invoice.user_id.name if invoice.user_id else '', format_left_align)
            sheet_2.write(row, 6, invoice.amount_residual_company, format_left_align)
            sheet_2.write(row, 7, '', format_4)
            sheet_2.write(row, 8, '', format_4)
            sheet_2.write(row, 9, '', format_4)
            sheet_2.write(row, 10, '', format_4)
            sheet_2.write(row, 11, invoice.amount_residual_company, format_4)
            sheet_2.write(row, 12, '', format_4)
            # sheet_2.write(row, 13, invoice.amount_residual_company, format_4)
            row += 1
            s_no += 1
        for invoice in invoice_ids.filtered(lambda x: x.invoice_date <= days_120):
            sheet_2.write(row, 0, s_no, format_1)
            sheet_2.write(row, 1, invoice.name, format_2)
            sheet_2.write(row, 2, invoice.partner_id.name, format_2)
            sheet_2.write(row, 3, invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else '', format_2)
            sheet_2.write(row, 4, invoice.collection_person.name if invoice.collection_person else '', format_left_align)
            sheet_2.write(row, 5, invoice.user_id.name if invoice.user_id else '', format_left_align)
            sheet_2.write(row, 6, invoice.amount_residual_company, format_left_align)
            sheet_2.write(row, 7, '', format_4)
            sheet_2.write(row, 8, '', format_4)
            sheet_2.write(row, 9, '', format_4)
            sheet_2.write(row, 10, '', format_4)
            sheet_2.write(row, 11, '', format_4)
            sheet_2.write(row, 12, invoice.amount_residual_company, format_4)
            # sheet_2.write(row, 13, invoice.amount_residual_company, format_4)
            row += 1
            s_no += 1

        workbook.close()
        fo = open(url + 'Daily Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodebytes(data)
        ir_values = {
            'name': "Daily Report.xlsx",
            'type': 'binary',
            'datas': out,
            'store_fname': out,
        }
        attachment = self.env['ir.attachment'].create(ir_values)
        self.write({'report_details': out, 'report_details_name': 'Daily Report.xlsx', 'report_attachment': attachment.id})
        return {
            'view_mode': 'form',
            'res_model': 'daily.report.old',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
