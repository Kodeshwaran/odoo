from odoo import models, fields, api, _
import base64
import xlsxwriter
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import rrule
import io
from PIL import Image


class DailyReportNew(models.TransientModel):
    _name = 'daily.report.new'
    _rec_name = 'report_details'
    _description = 'Daily Report'

    date_from = fields.Date('Date From', required=1)
    date_to = fields.Date('Date To', required=1)
    report_details = fields.Binary('Daily Report New', readonly=True)
    report_attachment = fields.Many2one('ir.attachment', string="Report Attachment")
    report_details_name = fields.Char('Filename', size=64, readonly=True)

    def action_daily_report1(self):
        previous_year_budget = self.env['sale.budget'].search([('date_from', '<=', self.date_to - relativedelta(years=1)),('date_to', '>=', self.date_to - relativedelta(years=1))], limit=1)
        current_year_budget = self.env['sale.budget'].search([('date_from', '<=', self.date_to), ('date_to', '>=', self.date_to)], limit=1)
        url = '/tmp/'
        num_format2 = self.env.user.company_id.currency_id.excel_format
        num_format = '#0\.00,'
        workbook = xlsxwriter.Workbook(url + 'Daily Report New.xlsx')
        sheet = workbook.add_worksheet('Billing Booking')
        company_format = workbook.add_format({'font_size': 12, 'bold': True, 'italic': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'right': 1,})
        title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF66', 'border': 1, 'right': 1, 'num_format': num_format + 'L'})
        sub_title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#90ee90', 'border': 1, 'right': 1, 'num_format': num_format + 'L'})
        parent_name_format_team = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'left', 'bg_color': '#e47078', 'num_format': num_format})
        parent_name_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'left', 'bg_color': '#F0CCB0', 'num_format': num_format})
        parent_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'right', 'valign': 'right', 'bg_color': '#F0CCB0', 'num_format': num_format})
        sale_type_name_format = workbook.add_format(
            {'font_size': 11, 'bold': True, 'align': 'left', 'valign': 'left', 'bg_color': '#D3D3D3', 'num_format': num_format})
        sale_type_format = workbook.add_format(
            {'font_size': 11, 'bold': True, 'align': 'right', 'valign': 'right', 'bg_color': '#D3D3D3', 'num_format': num_format})
        dr_amount_format = workbook.add_format(
            {'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#D3D3D3','num_format': num_format2})
        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'right', 'num_format': num_format})
        head_bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'center', 'num_format': num_format})
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
        sheet.merge_range('D3:F3', 'DAILY REPORT: %s to %s' % (self.date_from.strftime('%d-%m-%Y'), self.date_to.strftime('%d-%m-%Y')), heading_format)
        sheet.write(5, 0, 'DESCRIPTION', sub_title_format)
        if previous_year_budget:
            # sheet.merge_range(4, 1, 4, 2, (self.date_to - relativedelta(years=1)).strftime('%B %Y'), head_bold)
            # sheet.write(5, 1, 'BUDGET', sub_title_format)
            # sheet.write(5, 2, 'ACTUAL', sub_title_format)
            # sheet.merge_range(4, 3, 4, 4, 'UPTO ' + (self.date_to - relativedelta(years=1)).strftime('%B %Y'), head_bold)
            # sheet.write(5, 3, 'BUDGET', sub_title_format)
            # sheet.write(5, 4, 'ACTUAL', sub_title_format)
            sheet.merge_range(4, 1, 4, 2, self.date_to.strftime('%B %Y'), head_bold)
            sheet.write(5, 1, 'BUDGET', sub_title_format)
            sheet.write(5, 2, 'ACTUAL', sub_title_format)
            sheet.merge_range(4, 3, 4, 4, 'UPTO ' + self.date_to.strftime('%B %Y'), head_bold)
            sheet.write(5, 3, 'BUDGET', sub_title_format)
            sheet.write(5, 4, 'ACTUAL', sub_title_format)
        else:
            sheet.merge_range(4, 1, 4, 2, self.date_to.strftime('%B %Y'), head_bold)
            sheet.write(5, 1, 'BUDGET', sub_title_format)
            sheet.write(5, 2, 'ACTUAL', sub_title_format)
            sheet.merge_range(4, 3, 4, 4, 'UPTO ' + self.date_to.strftime('%B %Y'), head_bold)
            sheet.write(5, 3, 'BUDGET', sub_title_format)
            sheet.write(5, 4, 'ACTUAL', sub_title_format)
        #Master Datas
        sale_type_ids = self.env['sale.type'].search([])
        team_ids = self.env['crm.team'].search([])

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

        sheet.write(6, 0, 'A) Sales', parent_name_format_team)
        if previous_year_budget:
            sales_total_budget_exist_previous = sum(previous_year_budget.sale_budget_lines.mapped('existing_customer_target')) / 12
            # sheet.write(6, 1, sales_total_budget_exist_previous if sales_total_budget_exist_previous != 0 else '-', parent_format)
            inv_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            cred_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            sales_total_invoice_exist_previous = sum(inv_ids_previous.mapped('amount_total_company')) - sum(cred_ids_previous.mapped('amount_total_company'))
            # sheet.write(6, 2, sales_total_invoice_exist_previous if sales_total_invoice_exist_previous != 0 else '-', parent_format)
            date_start = self.date_from
            date_end = self.date_to
            sales_total_budget_exist_previous1 = (sum(previous_year_budget.sale_budget_lines.mapped('existing_customer_target')) / 12) * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
            # sheet.write(6, 3, sales_total_budget_exist_previous1 if sales_total_budget_exist_previous1 != 0 else '-', parent_format)
            inv_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            cred_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            sales_total_invoice_exist_previous1 = sum(inv_ids_previous1.mapped('amount_total_company')) - sum(cred_ids_previous1.mapped('amount_total_company'))
            # sheet.write(6, 4, sales_total_invoice_exist_previous1 if sales_total_invoice_exist_previous1 != 0 else '-',parent_format)
            sales_total_budget_exist_current = sum(current_year_budget.sale_budget_lines.mapped('existing_customer_target')) / 12
            sheet.write(6, 1, sales_total_budget_exist_current if sales_total_budget_exist_current != 0 else '-', parent_format)
            inv_ids = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            cred_ids = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            sales_total_invoice_exist_current = sum(inv_ids.mapped('amount_total_company')) - sum(cred_ids.mapped('amount_total_company'))
            sheet.write(6, 2, sales_total_invoice_exist_current if sales_total_invoice_exist_current != 0 else '-',parent_format)
            sales_total_budget_exist_current1 = (sum(current_year_budget.sale_budget_lines.mapped('existing_customer_target')) / 12) * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
            sheet.write(6, 3, sales_total_budget_exist_current1 if sales_total_budget_exist_current1 != 0 else '-', parent_format)
            inv_ids1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            cred_ids1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            sales_total_invoice_exist_current1 = sum(inv_ids1.mapped('amount_total_company')) - sum(cred_ids1.mapped('amount_total_company'))
            sheet.write(6, 4, sales_total_invoice_exist_current1 if sales_total_invoice_exist_current1 != 0 else '-',parent_format)
            row = 7
            # Writing to Excel for each team
            for team_id in team_ids:
                sheet.write(row, 0, team_id.name, parent_name_format)

                # Previous year's sales budget (existing_customer_target) for the team
                sales_type_total_budget_exist_previous = sum(
                    previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped(
                        'existing_customer_target')) / 12
                # sheet.write(row, 1,
                #             sales_type_total_budget_exist_previous if sales_type_total_budget_exist_previous != 0 else '-',
                #             sale_type_name_format)

                # Previous year's actual sales (invoices - credits) for the team
                invoice_ids_previous = self.env['account.move'].search(
                    [('move_type', '=', 'out_invoice'),
                     ('state', '=', 'posted'),
                     ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)),
                     ('invoice_date', '<=',
                      self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(
                          days=1)),
                     ('team_id', '=', team_id.id),
                     ('sales_sub_types', '!=', False)])
                credit_ids_previous = self.env['account.move'].search(
                    [('move_type', '=', 'out_refund'),
                     ('state', '=', 'posted'),
                     ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)),
                     ('invoice_date', '<=',
                      self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(
                          days=1)),
                     ('team_id', '=', team_id.id),
                     ('sales_sub_types', '!=', False)])
                sales_type_total_invoice_exist_previous = sum(
                    invoice_ids_previous.mapped('amount_total_company')) - sum(
                    credit_ids_previous.mapped('amount_total_company'))
                # sheet.write(row, 2,
                #             sales_type_total_invoice_exist_previous if sales_type_total_invoice_exist_previous != 0 else '-',
                #             sale_type_name_format)

                # Sales budget for the team with date range calculation
                sales_type_total_budget_exist_previous1 = sum(
                    previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped(
                        'existing_customer_target')) / 12 * ((
                                                                     date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                # sheet.write(row, 3,
                #             sales_type_total_budget_exist_previous1 if sales_type_total_budget_exist_previous1 != 0 else '-',
                #             sale_type_name_format)

                # Previous year's sales data for a broader range
                invoice_ids_previous1 = self.env['account.move'].search(
                    [('move_type', '=', 'out_invoice'),
                     ('state', '=', 'posted'),
                     ('invoice_date', '>=', self.date_from - relativedelta(years=1)),
                     ('invoice_date', '<=',
                      self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(
                          days=1)),
                     ('team_id', '=', team_id.id),
                     ('sales_sub_types', '!=', False)])
                credit_ids_previous1 = self.env['account.move'].search(
                    [('move_type', '=', 'out_refund'),
                     ('state', '=', 'posted'),
                     ('invoice_date', '>=', self.date_from - relativedelta(years=1)),
                     ('invoice_date', '<=',
                      self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(
                          days=1)),
                     ('team_id', '=', team_id.id),
                     ('sales_sub_types', '!=', False)])
                sales_type_total_invoice_exist_previous1 = sum(
                    invoice_ids_previous1.mapped('amount_total_company')) - sum(
                    credit_ids_previous1.mapped('amount_total_company'))
                # sheet.write(row, 4,
                #             sales_type_total_invoice_exist_previous1 if sales_type_total_invoice_exist_previous1 != 0 else '-',
                #             sale_type_name_format)

                # Current year's sales budget for the team
                sales_type_total_budget_exist_current = sum(
                    current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped(
                        'existing_customer_target')) / 12
                sheet.write(row, 1,
                            sales_type_total_budget_exist_current if sales_type_total_budget_exist_current != 0 else '-',
                            sale_type_name_format)

                # Current year's actual sales (invoices - credits) for the team
                invoice_ids_current = self.env['account.move'].search(
                    [('move_type', '=', 'out_invoice'),
                     ('state', '=', 'posted'),
                     ('invoice_date', '>=', self.date_to.replace(day=1)),
                     ('invoice_date', '<=', self.date_to),
                     ('team_id', '=', team_id.id),
                     ('sales_sub_types', '!=', False)])
                credit_ids_current = self.env['account.move'].search(
                    [('move_type', '=', 'out_refund'),
                     ('state', '=', 'posted'),
                     ('invoice_date', '>=', self.date_to.replace(day=1)),
                     ('invoice_date', '<=', self.date_to),
                     ('team_id', '=', team_id.id),
                     ('sales_sub_types', '!=', False)])
                sales_type_total_invoice_exist_current = sum(
                    invoice_ids_current.mapped('amount_total_company')) - sum(
                    credit_ids_current.mapped('amount_total_company'))
                sheet.write(row, 2,
                            sales_type_total_invoice_exist_current if sales_type_total_invoice_exist_current != 0 else '-',
                            sale_type_name_format)

                # Current year's sales budget with date range calculation
                sales_type_total_budget_exist_current1 = sum(
                    current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped(
                        'existing_customer_target')) / 12 * ((
                                                                     date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                sheet.write(row, 3,
                            sales_type_total_budget_exist_current1 if sales_type_total_budget_exist_current1 != 0 else '-',
                            sale_type_name_format)

                # Sales data for the broader range
                invoice_ids_current1 = self.env['account.move'].search(
                    [('move_type', '=', 'out_invoice'),
                     ('state', '=', 'posted'),
                     ('invoice_date', '>=', self.date_from),
                     ('invoice_date', '<=', self.date_to),
                     ('team_id', '=', team_id.id),
                     ('sales_sub_types', '!=', False)])
                credit_ids_current1 = self.env['account.move'].search(
                    [('move_type', '=', 'out_refund'),
                     ('state', '=', 'posted'),
                     ('invoice_date', '>=', self.date_from),
                     ('invoice_date', '<=', self.date_to),
                     ('team_id', '=', team_id.id),
                     ('sales_sub_types', '!=', False)])
                sales_type_total_invoice_exist_current1 = sum(
                    invoice_ids_current1.mapped('amount_total_company')) - sum(
                    credit_ids_current1.mapped('amount_total_company'))
                sheet.write(row, 4,
                            sales_type_total_invoice_exist_current1 if sales_type_total_invoice_exist_current1 != 0 else '-',
                            sale_type_name_format)

                row += 1

                # Now, handle the sale types under each team
                for sale_type_id in sale_type_ids:
                    sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                    sheet.write(row, 0, sale_type_id.name, sale_type_name_format)

                    # Repeat the same process for sale types as done for teams
                    # Previous year's sales budget (existing_customer_target) for the sale type
                    sales_type_total_budget_exist_previous = sum(
                        previous_year_budget.sale_budget_lines.filtered(
                            lambda x: x.team_id.id == team_id.id and x.sale_type_id.id == sale_type_id.id).mapped('existing_customer_target')) / 12
                    # sheet.write(row, 1,
                    #             sales_type_total_budget_exist_previous if sales_type_total_budget_exist_previous != 0 else '-',
                    #             sale_type_format)

                    invoice_ids_previous = self.env['account.move'].search(
                        [('move_type', '=', 'out_invoice'),
                         ('state', '=', 'posted'),
                         ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)),
                         ('invoice_date', '<=',
                          self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(
                              days=1)),
                         ('sale_type_id', '=', sale_type_id.id),
                         ('team_id', '=', team_id.id),
                         ('sales_sub_types', '!=', False)])
                    credit_ids_previous = self.env['account.move'].search(
                        [('move_type', '=', 'out_refund'),
                         ('state', '=', 'posted'),
                         ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)),
                         ('invoice_date', '<=',
                          self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(
                              days=1)),
                         ('sale_type_id', '=', sale_type_id.id),
                         ('team_id', '=', team_id.id),
                         ('sales_sub_types', '!=', False)])
                    sales_type_total_invoice_exist_previous = sum(
                        invoice_ids_previous.mapped('amount_total_company')) - sum(
                        credit_ids_previous.mapped('amount_total_company'))
                    # sheet.write(row, 2,
                    #             sales_type_total_invoice_exist_previous if sales_type_total_invoice_exist_previous != 0 else '-',
                    #             sale_type_format)

                    # Sales budget for the sale type with date range calculation
                    sales_type_total_budget_exist_previous1 = sum(
                        previous_year_budget.sale_budget_lines.filtered(
                            lambda x: x.team_id.id == team_id.id and x.sale_type_id.id == sale_type_id.id).mapped('existing_customer_target')) / 12 * (
                                                                          (
                                                                                  date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                    # sheet.write(row, 3,
                    #             sales_type_total_budget_exist_previous1 if sales_type_total_budget_exist_previous1 != 0 else '-',
                    #             sale_type_format)

                    # Previous year's sales data for a broader range (previous1)
                    invoice_ids_previous1 = self.env['account.move'].search(
                        [('move_type', '=', 'out_invoice'),
                         ('state', '=', 'posted'),
                         ('invoice_date', '>=', self.date_from - relativedelta(years=1)),
                         ('invoice_date', '<=',
                          self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(
                              days=1)),
                         ('sale_type_id', '=', sale_type_id.id),
                         ('team_id', '=', team_id.id),
                         ('sales_sub_types', '!=', False)])
                    credit_ids_previous1 = self.env['account.move'].search(
                        [('move_type', '=', 'out_refund'),
                         ('state', '=', 'posted'),
                         ('invoice_date', '>=', self.date_from - relativedelta(years=1)),
                         ('invoice_date', '<=',
                          self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(
                              days=1)),
                         ('sale_type_id', '=', sale_type_id.id),
                         ('team_id', '=', team_id.id),
                         ('sales_sub_types', '!=', False)])
                    sales_type_total_invoice_exist_previous1 = sum(
                        invoice_ids_previous1.mapped('amount_total_company')) - sum(
                        credit_ids_previous1.mapped('amount_total_company'))
                    # sheet.write(row, 4,
                    #             sales_type_total_invoice_exist_previous1 if sales_type_total_invoice_exist_previous1 != 0 else '-',
                    #             sale_type_format)
                    #
                    # Current year's sales budget for the sale type
                    sales_type_total_budget_exist_current = sum(
                        current_year_budget.sale_budget_lines.filtered(
                            lambda x: x.team_id.id == team_id.id and x.sale_type_id.id == sale_type_id.id).mapped('existing_customer_target')) / 12
                    sheet.write(row, 1,
                                sales_type_total_budget_exist_current if sales_type_total_budget_exist_current != 0 else '-',
                                sale_type_format)

                    # Current year's actual sales (invoices - credits) for the sale type
                    invoice_ids_current = self.env['account.move'].search(
                        [('move_type', '=', 'out_invoice'),
                         ('state', '=', 'posted'),
                         ('invoice_date', '>=', self.date_to.replace(day=1)),
                         ('invoice_date', '<=', self.date_to),
                         ('sale_type_id', '=', sale_type_id.id),
                         ('team_id', '=', team_id.id),
                         ('sales_sub_types', '!=', False)])
                    credit_ids_current = self.env['account.move'].search(
                        [('move_type', '=', 'out_refund'),
                         ('state', '=', 'posted'),
                         ('invoice_date', '>=', self.date_to.replace(day=1)),
                         ('invoice_date', '<=', self.date_to),
                         ('sale_type_id', '=', sale_type_id.id),
                         ('team_id', '=', team_id.id),
                         ('sales_sub_types', '!=', False)])
                    sales_type_total_invoice_exist_current = sum(
                        invoice_ids_current.mapped('amount_total_company')) - sum(
                        credit_ids_current.mapped('amount_total_company'))
                    sheet.write(row, 2,
                                sales_type_total_invoice_exist_current if sales_type_total_invoice_exist_current != 0 else '-',
                                sale_type_format)

                    # Current year's sales budget with date range calculation
                    sales_type_total_budget_exist_current1 = sum(
                        current_year_budget.sale_budget_lines.filtered(
                            lambda x: x.team_id.id == team_id.id and x.sale_type_id.id == sale_type_id.id).mapped('existing_customer_target')) / 12 * (
                                                                         (
                                                                                 date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                    sheet.write(row, 3,
                                sales_type_total_budget_exist_current1 if sales_type_total_budget_exist_current1 != 0 else '-',
                                sale_type_format)

                    # Sales data for the broader range (current1)
                    invoice_ids_current1 = self.env['account.move'].search(
                        [('move_type', '=', 'out_invoice'),
                         ('state', '=', 'posted'),
                         ('invoice_date', '>=', self.date_from),
                         ('invoice_date', '<=', self.date_to),
                         ('sale_type_id', '=', sale_type_id.id),
                         ('team_id', '=', team_id.id),
                         ('sales_sub_types', '!=', False)])
                    credit_ids_current1 = self.env['account.move'].search(
                        [('move_type', '=', 'out_refund'),
                         ('state', '=', 'posted'),
                         ('invoice_date', '>=', self.date_from),
                         ('invoice_date', '<=', self.date_to),
                         ('sale_type_id', '=', sale_type_id.id),
                         ('team_id', '=', team_id.id),
                         ('sales_sub_types', '!=', False)])
                    sales_type_total_invoice_exist_current1 = sum(
                        invoice_ids_current1.mapped('amount_total_company')) - sum(
                        credit_ids_current1.mapped('amount_total_company'))
                    sheet.write(row, 4,
                                sales_type_total_invoice_exist_current1 if sales_type_total_invoice_exist_current1 != 0 else '-',
                                sale_type_format)

                    row += 1

                    for sub_type_id in sale_type_id.sales_sub_types:
                        sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                        sheet.write(row, 0, sub_type_id.name, bold)
                        sales_subtype_total_budget_exist_previous = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12
                        # sheet.write(row, 1, sales_subtype_total_budget_exist_previous if sales_subtype_total_budget_exist_previous != 0 else '-', bold_2)
                        sub_invoice_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id),('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sub_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id),('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sales_subtype_total_invoice_exist_previous = sum(sub_invoice_ids_previous.mapped('amount_total_company')) - sum(sub_credit_ids_previous.mapped('amount_total_company'))
                        # sheet.write(row, 2, sales_subtype_total_invoice_exist_previous if sales_subtype_total_invoice_exist_previous != 0 else '-', bold_2)
                        sales_subtype_total_budget_exist_previous1 = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                        # sheet.write(row, 3, sales_subtype_total_budget_exist_previous1 if sales_subtype_total_budget_exist_previous1 != 0 else '-', bold_2)
                        sub_invoice_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)),('team_id', '=', team_id.id), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sub_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)),('team_id', '=', team_id.id), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sales_subtype_total_invoice_exist_previous1 = sum(sub_invoice_ids_previous1.mapped('amount_total_company')) - sum(sub_credit_ids_previous1.mapped('amount_total_company'))
                        # sheet.write(row, 4, sales_subtype_total_invoice_exist_previous1 if sales_subtype_total_invoice_exist_previous1 != 0 else '-', bold_2)
                        sales_subtype_total_budget_exist_current = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12
                        sheet.write(row, 1, sales_subtype_total_budget_exist_current if sales_subtype_total_budget_exist_current != 0 else '-', bold_2)
                        sub_invoice_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id),('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sub_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to),('team_id', '=', team_id.id), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sales_subtype_total_invoice_exist_current = sum(sub_invoice_ids_current.mapped('amount_total_company')) - sum(sub_credit_ids_current.mapped('amount_total_company'))
                        sheet.write(row, 2, sales_subtype_total_invoice_exist_current if sales_subtype_total_invoice_exist_current != 0 else '-', bold_2)
                        sales_subtype_total_budget_exist_current1 = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                        sheet.write(row, 3, sales_subtype_total_budget_exist_current1 if sales_subtype_total_budget_exist_current1 != 0 else '-', bold_2)
                        sub_invoice_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id),('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sub_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id),('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sales_subtype_total_invoice_exist_current1 = sum(sub_invoice_ids_current1.mapped('amount_total_company')) - sum(sub_credit_ids_current1.mapped('amount_total_company'))
                        sheet.write(row, 4, sales_subtype_total_invoice_exist_current1 if sales_subtype_total_invoice_exist_current1 != 0 else '-', bold_2)
                        row += 1

        # # Purchase functionality section
        
            sheet.write(row, 0, 'B) COGS', parent_name_format_team)
            total_bill_budget_previous = sum(previous_year_budget.sale_budget_lines.mapped('existing_vendor_target')) / 12
            # sheet.write(row, 1, total_bill_budget_previous  if total_bill_budget_previous != 0 else '-', parent_format)
            no_bill_invoice_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False), ('sales_sub_types.is_no_bill', '!=', False)])
            no_bill_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False), ('sales_sub_types.is_no_bill', '!=', False)])
            exist_no_bill_type_total_previous = 0
            for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.is_no_bill != False).mapped('sale_sub_type_id'):
                type_no_bill_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '=', sub_type_id.id)])
                type_no_bill_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '=', sub_type_id.id)])
                exist_no_bill_amount_previous = sum(x.amount_total_company for x in type_no_bill_ids_previous) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous)

                exist_no_bill_type_total_previous += exist_no_bill_amount_previous * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
            # exist_no_bill_total_previous = sum([(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda l: l.sale_sub_type_id.id == x.sales_sub_types.id).existing_vendor_target_percent) for x in no_bill_invoice_ids_previous]) - sum([(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda l: l.sale_sub_type_id.id == x.sales_sub_types.id).existing_vendor_target_percent) for x in no_bill_credit_ids_previous])
            bill_invoice_ids_previous = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            bill_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            cogs_total_bill_exist_previous = sum(bill_invoice_ids_previous.mapped('amount_total_company')) - sum(bill_credit_ids_previous.mapped('amount_total_company'))
            total_bill_previous = exist_no_bill_type_total_previous + cogs_total_bill_exist_previous
            # sheet.write(row, 2, total_bill_previous if total_bill_previous != 0 else '-', parent_format)
            total_bill_budget_previous1 = sum(previous_year_budget.sale_budget_lines.mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
            # sheet.write(row, 3, total_bill_budget_previous1 if total_bill_budget_previous1 != 0 else '-', parent_format)
            no_bill_invoice_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to - relativedelta(years=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False), ('sales_sub_types.is_no_bill', '!=', False)])
            no_bill_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to - relativedelta(years=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False), ('sales_sub_types.is_no_bill', '!=', False)])
            exist_no_bill_type_total_previous1 = 0
            for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.is_no_bill != False).mapped('sale_sub_type_id'):
                type_no_bill_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '=', sub_type_id.id)])
                type_no_bill_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '=', sub_type_id.id)])
                exist_no_bill_amount_previous1 = sum(x.amount_total_company for x in type_no_bill_ids_previous1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous1)

                exist_no_bill_type_total_previous1 += exist_no_bill_amount_previous1 * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
            # exist_no_bill_total_previous1 = sum([(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda l: l.sale_sub_type_id.id == x.sales_sub_types.id).existing_vendor_target_percent) for x in no_bill_invoice_ids_previous1]) - sum([(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda l: l.sale_sub_type_id.id == x.sales_sub_types.id).existing_vendor_target_percent) for x in no_bill_credit_ids_previous1])
            bill_invoice_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            bill_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            cogs_total_bill_exist_previous1 = sum(bill_invoice_ids_previous1.mapped('amount_total_company')) - sum(bill_credit_ids_previous1.mapped('amount_total_company'))
            total_bill_previous1 = exist_no_bill_type_total_previous1 + cogs_total_bill_exist_previous1
            # sheet.write(row, 4, total_bill_previous1 if total_bill_previous1 != 0 else '-', parent_format)
            total_bill_budget_current = sum(current_year_budget.sale_budget_lines.mapped('existing_vendor_target')) / 12
            sheet.write(row, 1, total_bill_budget_current if total_bill_budget_current != 0 else '-', parent_format)
            no_bill_invoice_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False), ('sales_sub_types.is_no_bill', '!=', False)])
            no_bill_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False), ('sales_sub_types.is_no_bill', '!=', False)])
            exist_no_bill_type_total_current = 0
            for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.is_no_bill != False).mapped('sale_sub_type_id'):
                type_no_bill_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '=', sub_type_id.id)])
                type_no_bill_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '=', sub_type_id.id)])
                exist_no_bill_amount_current = sum(x.amount_total_company for x in type_no_bill_ids_current) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current)

                exist_no_bill_type_total_current += exist_no_bill_amount_current * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
            # exist_no_bill_total_current = sum([(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda l: l.sale_sub_type_id.id == x.sales_sub_types.id).existing_vendor_target_percent) for x in no_bill_invoice_ids_current]) - sum([(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda l: l.sale_sub_type_id.id == x.sales_sub_types.id).existing_vendor_target_percent) for x in no_bill_credit_ids_current])
            bill_invoice_ids_current = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            bill_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            cogs_total_bill_exist_current = sum(bill_invoice_ids_current.mapped('amount_total_company')) - sum(bill_credit_ids_current.mapped('amount_total_company'))
            total_bill_current = exist_no_bill_type_total_current + cogs_total_bill_exist_current
            sheet.write(row, 2, total_bill_current if total_bill_current != 0 else '-', parent_format)
            total_bill_budget_current1 = sum(current_year_budget.sale_budget_lines.mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
            sheet.write(row, 3, total_bill_budget_current1 if total_bill_budget_current1 != 0 else '-', parent_format)
            no_bill_invoice_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False), ('sales_sub_types.is_no_bill', '!=', False)])
            no_bill_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False), ('sales_sub_types.is_no_bill', '!=', False)])
            exist_no_bill_type_total_current1 = 0
            for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.is_no_bill != False).mapped('sale_sub_type_id'):
                type_no_bill_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '=', sub_type_id.id)])
                type_no_bill_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '=', sub_type_id.id)])
                exist_no_bill_amount_current1 = sum(x.amount_total_company for x in type_no_bill_ids_current1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current1)

                exist_no_bill_type_total_current1 += exist_no_bill_amount_current1 * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
            # exist_no_bill_total_current1 = sum([(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda l: l.sale_sub_type_id.id == x.sales_sub_types.id).existing_vendor_target_percent) for x in no_bill_invoice_ids_current1]) - sum([(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda l: l.sale_sub_type_id.id == x.sales_sub_types.id).existing_vendor_target_percent) for x in no_bill_credit_ids_current1])
            bill_invoice_ids_current1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            bill_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
            cogs_total_bill_exist_current1 = sum(bill_invoice_ids_current1.mapped('amount_total_company')) - sum(bill_credit_ids_current1.mapped('amount_total_company'))
            total_bill_current1 = exist_no_bill_type_total_current1 + cogs_total_bill_exist_current1
            sheet.write(row, 4, total_bill_current1 if total_bill_current1 != 0 else '-', parent_format)
            row += 1
            for team_id in team_ids:
                sheet.write(row, 0, team_id.name, parent_name_format)
                total_bill_sale_type_budget_previous = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id == team_id.id).mapped('existing_vendor_target')) / 12
                # sheet.write(row, 1, total_bill_sale_type_budget_previous if total_bill_sale_type_budget_previous != 0 else '-', sale_type_format)
                exist_no_bill_type_total_previous = 0
                for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                    type_no_bill_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    type_no_bill_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    exist_no_bill_amount_previous = sum(x.amount_total_company for x in type_no_bill_ids_previous) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous)

                    exist_no_bill_type_total_previous += exist_no_bill_amount_previous * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                cogs_type_bill_exist_previous = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_debit_note_exist_previous = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_total_exist_previous = sum(x.amount_total_company for x in cogs_type_bill_exist_previous) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_previous)
                total_bill_sale_type_previous = exist_no_bill_type_total_previous + cogs_type_total_exist_previous
                # sheet.write(row, 2, total_bill_sale_type_previous if total_bill_sale_type_previous != 0 else '-', sale_type_format)
                total_bill_sale_type_budget_previous1 = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                # sheet.write(row, 3, total_bill_sale_type_budget_previous1 if total_bill_sale_type_budget_previous1 != 0 else '-', sale_type_format)
                exist_no_bill_type_total_previous1 = 0
                for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                    type_no_bill_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    type_no_bill_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    exist_no_bill_amount_previous1 = sum(x.amount_total_company for x in type_no_bill_ids_previous1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous1)

                    exist_no_bill_type_total_previous1 += exist_no_bill_amount_previous1 * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                cogs_type_bill_exist_previous1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_debit_note_exist_previous1 = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_total_exist_previous1 = sum(x.amount_total_company for x in cogs_type_bill_exist_previous1) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_previous1)
                total_bill_sale_type_previous1 = exist_no_bill_type_total_previous1 + cogs_type_total_exist_previous1
                # sheet.write(row, 4, total_bill_sale_type_previous1 if total_bill_sale_type_previous1 != 0 else '-', sale_type_format)
                total_bill_sale_type_budget_current = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12
                sheet.write(row, 1, total_bill_sale_type_budget_current if total_bill_sale_type_budget_current != 0 else '-', sale_type_format)
                exist_no_bill_type_total_current = 0
                for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                    type_no_bill_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    type_no_bill_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    exist_no_bill_amount_current = sum(x.amount_total_company for x in type_no_bill_ids_current) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current)

                    exist_no_bill_type_total_current += exist_no_bill_amount_current * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                cogs_type_bill_exist_current = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_debit_note_exist_current = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_total_exist_current = sum(x.amount_total_company for x in cogs_type_bill_exist_current) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_current)
                total_bill_sale_type_current = exist_no_bill_type_total_current + cogs_type_total_exist_current
                sheet.write(row, 2, total_bill_sale_type_current if total_bill_sale_type_current != 0 else '-', sale_type_format)
                total_bill_sale_type_budget_current1 = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                sheet.write(row, 3,total_bill_sale_type_budget_current1 if total_bill_sale_type_budget_current1 != 0 else '-', sale_type_format)
                exist_no_bill_type_total_current1 = 0
                for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                    type_no_bill_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    type_no_bill_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    exist_no_bill_amount_current1 = sum(x.amount_total_company for x in type_no_bill_ids_current1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current1)

                    exist_no_bill_type_total_current1 += exist_no_bill_amount_current1 * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                cogs_type_bill_exist_current1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_debit_note_exist_current1 = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_total_exist_current1 = sum(x.amount_total_company for x in cogs_type_bill_exist_current1) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_current1)
                total_bill_sale_type_current1 = exist_no_bill_type_total_current1 + cogs_type_total_exist_current1
                sheet.write(row, 4, total_bill_sale_type_current1 if total_bill_sale_type_current1 != 0 else '-', sale_type_format)
                row += 1
                for sale_type_id in sale_type_ids:
                    sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                    sheet.write(row, 0, sale_type_id.name, sale_type_name_format)
                    total_bill_sale_type_budget_previous = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12
                    # sheet.write(row, 1, total_bill_sale_type_budget_previous if total_bill_sale_type_budget_previous != 0 else '-', sale_type_format)
                    exist_no_bill_type_total_previous = 0
                    for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and  x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                        type_no_bill_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        type_no_bill_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        exist_no_bill_amount_previous = sum(x.amount_total_company for x in type_no_bill_ids_previous) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous)

                        exist_no_bill_type_total_previous += exist_no_bill_amount_previous * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100
                    cogs_type_bill_exist_previous = self.env['account.move'].search([('move_type', '=', 'in_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_debit_note_exist_previous = self.env['account.move'].search([('move_type', '=', 'in_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_total_exist_previous = sum(x.amount_total_company for x in cogs_type_bill_exist_previous) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_previous)
                    total_bill_sale_type_previous = exist_no_bill_type_total_previous + cogs_type_total_exist_previous
                    # sheet.write(row, 2, total_bill_sale_type_previous if total_bill_sale_type_previous != 0 else '-', sale_type_format)
                    total_bill_sale_type_budget_previous1 = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                    # sheet.write(row, 3, total_bill_sale_type_budget_previous1 if total_bill_sale_type_budget_previous1 != 0 else '-', sale_type_format)
                    exist_no_bill_type_total_previous1 = 0
                    for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                        type_no_bill_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        type_no_bill_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        exist_no_bill_amount_previous1 = sum(x.amount_total_company for x in type_no_bill_ids_previous1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous1)

                        exist_no_bill_type_total_previous1 += exist_no_bill_amount_previous1 * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100
                    cogs_type_bill_exist_previous1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_debit_note_exist_previous1 = self.env['account.move'].search([('move_type', '=', 'in_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_total_exist_previous1 = sum(x.amount_total_company for x in cogs_type_bill_exist_previous1) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_previous1)
                    total_bill_sale_type_previous1 = exist_no_bill_type_total_previous1 + cogs_type_total_exist_previous1
                    # sheet.write(row, 4, total_bill_sale_type_previous1 if total_bill_sale_type_previous1 != 0 else '-', sale_type_format)
                    total_bill_sale_type_budget_current = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12
                    sheet.write(row, 2, total_bill_sale_type_budget_current if total_bill_sale_type_budget_current != 0 else '-', sale_type_format)
                    exist_no_bill_type_total_current = 0
                    for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                        type_no_bill_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        type_no_bill_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        exist_no_bill_amount_current = sum(x.amount_total_company for x in type_no_bill_ids_current) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current)

                        exist_no_bill_type_total_current += exist_no_bill_amount_current * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100
                    cogs_type_bill_exist_current = self.env['account.move'].search([('move_type', '=', 'in_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_debit_note_exist_current = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_total_exist_current = sum(x.amount_total_company for x in cogs_type_bill_exist_current) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_current)
                    total_bill_sale_type_current = exist_no_bill_type_total_current + cogs_type_total_exist_current
                    sheet.write(row, 2, total_bill_sale_type_current if total_bill_sale_type_current != 0 else '-', sale_type_format)
                    total_bill_sale_type_budget_current1 = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                    sheet.write(row, 3,total_bill_sale_type_budget_current1 if total_bill_sale_type_budget_current1 != 0 else '-', sale_type_format)
                    exist_no_bill_type_total_current1 = 0
                    for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                        type_no_bill_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        type_no_bill_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        exist_no_bill_amount_current1 = sum(x.amount_total_company for x in type_no_bill_ids_current1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current1)

                        exist_no_bill_type_total_current1 += exist_no_bill_amount_current1 * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                    cogs_type_bill_exist_current1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_debit_note_exist_current1 = self.env['account.move'].search([('move_type', '=', 'in_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_total_exist_current1 = sum(x.amount_total_company for x in cogs_type_bill_exist_current1) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_current1)
                    total_bill_sale_type_current1 = exist_no_bill_type_total_current1 + cogs_type_total_exist_current1
                    sheet.write(row, 4, total_bill_sale_type_current1 if total_bill_sale_type_current1 != 0 else '-', sale_type_format)
                    row += 1

                    for sub_type_id in sale_type_id.sales_sub_types:
                        sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                        sheet.write(row, 0, sub_type_id.name, bold)
                        total_bill_sub_budget_previous = previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target / 12
                        # sheet.write(row, 1, total_bill_sub_budget_previous if total_bill_sub_budget_previous != 0 else '-', bold_2)
                        subtype_no_bill_ids_sub_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        subtype_no_bill_credit_ids_sub_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        exist_no_bill_amount_sub_previous = sum(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_ids_sub_previous) - sum(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_credit_ids_sub_previous)
                        cogs_subtype_bill_exist_sub_previous = sum(self.env['account.move'].search([('move_type', '=', 'in_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_debit_exist_sub_previous = sum(self.env['account.move'].search([('move_type', '=', 'in_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_total_bill_exist_sub_previous = cogs_subtype_bill_exist_sub_previous - cogs_subtype_debit_exist_sub_previous
                        total_bill_sub_previous = exist_no_bill_amount_sub_previous + cogs_subtype_total_bill_exist_sub_previous
                        # sheet.write(row, 2, total_bill_sub_previous if total_bill_sub_previous != 0 else '-', bold_2)
                        total_bill_sub_budget_previous1 = previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                        # sheet.write(row, 3, total_bill_sub_budget_previous1 if total_bill_sub_budget_previous1 != 0 else '-', bold_2)
                        subtype_no_bill_ids_sub_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        subtype_no_bill_credit_ids_sub_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        exist_no_bill_amount_sub_previous1 = sum(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_ids_sub_previous1) - sum(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_credit_ids_sub_previous1)
                        cogs_subtype_bill_exist_sub_previous1 = sum(self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_debit_exist_sub_previous1 = sum(self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_total_bill_exist_sub_previous1 = cogs_subtype_bill_exist_sub_previous1 - cogs_subtype_debit_exist_sub_previous1
                        total_bill_sub_previous1 = exist_no_bill_amount_sub_previous1 + cogs_subtype_total_bill_exist_sub_previous1
                        # sheet.write(row, 4, total_bill_sub_previous1 if total_bill_sub_previous1 != 0 else '-', bold_2)
                        total_bill_sub_budget_current = current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target / 12
                        sheet.write(row, 1, total_bill_sub_budget_current if total_bill_sub_budget_current != 0 else '-', bold_2)
                        subtype_no_bill_ids_sub_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        subtype_no_bill_credit_ids_sub_current = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        exist_no_bill_amount_sub_current = sum(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_ids_sub_current) - sum(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_credit_ids_sub_current)
                        cogs_subtype_bill_exist_sub_current = sum(self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_debit_exist_sub_current = sum(self.env['account.move'].search([('move_type', '=', 'in_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_total_bill_exist_sub_current = cogs_subtype_bill_exist_sub_current - cogs_subtype_debit_exist_sub_current
                        total_bill_sub_current = exist_no_bill_amount_sub_current + cogs_subtype_total_bill_exist_sub_current
                        sheet.write(row, 2, total_bill_sub_current if total_bill_sub_current != 0 else '-', bold_2)
                        total_bill_sub_budget_current1 = current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                        sheet.write(row, 3, total_bill_sub_budget_current1 if total_bill_sub_budget_current1 != 0 else '-', bold_2)
                        subtype_no_bill_ids_sub_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        subtype_no_bill_credit_ids_sub_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        exist_no_bill_amount_sub_current1 = sum(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_ids_sub_current1) - sum(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_credit_ids_sub_current1)
                        cogs_subtype_bill_exist_sub_current1 = sum(self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_debit_exist_sub_current1 = sum(self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_total_bill_exist_sub_current1 = cogs_subtype_bill_exist_sub_current1 - cogs_subtype_debit_exist_sub_current1
                        total_bill_sub_current1 = exist_no_bill_amount_sub_current1 + cogs_subtype_total_bill_exist_sub_current1
                        sheet.write(row, 4, total_bill_sub_current1 if total_bill_sub_current1 != 0 else '-', bold_2)
                        row += 1
        # Gross Margin functionalities start
            sheet.write(row, 0, 'C) Gross Margin', parent_name_format_team)
            gross_total_budget_previous = sales_total_budget_exist_previous - total_bill_budget_previous
            # sheet.write(row, 1, gross_total_budget_previous if gross_total_budget_previous != 0 else '-', parent_format)
            gross_total_exist_previous = sales_total_invoice_exist_previous - total_bill_previous
            # sheet.write(row, 2, gross_total_exist_previous if gross_total_exist_previous != 0 else '-', parent_format)
            gross_total_budget_previous1 = sales_total_budget_exist_previous1 - total_bill_budget_previous1
            # sheet.write(row, 3, gross_total_budget_previous1 if gross_total_budget_previous1 != 0 else '-', parent_format)
            gross_total_exist_previous1 = sales_total_invoice_exist_previous1 - total_bill_previous1
            # sheet.write(row, 4, gross_total_exist_previous1 if gross_total_exist_previous1 != 0 else '-', parent_format)
            gross_total_budget_current = sales_total_budget_exist_current - total_bill_budget_current
            sheet.write(row, 1, gross_total_budget_current if gross_total_budget_current != 0 else '-', parent_format)
            gross_total_exist_current = sales_total_invoice_exist_current - total_bill_current
            sheet.write(row, 2, gross_total_exist_current if gross_total_exist_current != 0 else '-', parent_format)
            gross_total_budget_current1 = sales_total_budget_exist_current1 - total_bill_budget_current1
            sheet.write(row, 3, gross_total_budget_current1 if gross_total_budget_current1 != 0 else '-', parent_format)
            gross_total_exist_current1 = sales_total_invoice_exist_current1 - total_bill_current1
            sheet.write(row, 4, gross_total_exist_current1 if gross_total_exist_current1 != 0 else '-', parent_format)
            row += 1
            for team_id in team_ids:
                sheet.write(row, 0, team_id.name, parent_name_format)
                gross_sale_type_total_budget_previous = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 - sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12
                # sheet.write(row, 1, gross_sale_type_total_budget_previous if gross_sale_type_total_budget_previous != 0 else '-', sale_type_format)
                invoice_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                sales_type_total_invoice_exist_previous = sum(invoice_ids_previous.mapped('amount_total_company')) - sum(credit_ids_previous.mapped('amount_total_company'))
                exist_no_bill_type_total_previous = 0
                for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                    type_no_bill_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    type_no_bill_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    exist_no_bill_amount_previous = sum(x.amount_total_company for x in type_no_bill_ids_previous) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous)

                    exist_no_bill_type_total_previous += exist_no_bill_amount_previous * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                cogs_type_bill_exist_previous = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_debit_note_exist_previous = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_total_exist_previous = sum(x.amount_total_company for x in cogs_type_bill_exist_previous) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_previous)
                total_bill_sale_type_previous = exist_no_bill_type_total_previous + cogs_type_total_exist_previous
                gross_sale_type_total_exist_previous = sales_type_total_invoice_exist_previous - total_bill_sale_type_previous
                # sheet.write(row, 2, gross_sale_type_total_exist_previous if gross_sale_type_total_exist_previous != 0 else '-', sale_type_format)
                gross_sale_type_total_budget_previous1 = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1) - sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                # sheet.write(row, 3, gross_sale_type_total_budget_previous1 if gross_sale_type_total_budget_previous1 != 0 else '-', sale_type_format)
                invoice_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                sales_type_total_invoice_exist_previous1 = sum(invoice_ids_previous1.mapped('amount_total_company')) - sum(credit_ids_previous1.mapped('amount_total_company'))
                exist_no_bill_type_total_previous1 = 0
                for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                    type_no_bill_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    type_no_bill_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    exist_no_bill_amount_previous1 = sum(x.amount_total_company for x in type_no_bill_ids_previous1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous1)

                    exist_no_bill_type_total_previous1 += exist_no_bill_amount_previous1 * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                cogs_type_bill_exist_previous1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_debit_note_exist_previous1 = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_total_exist_previous1 = sum(x.amount_total_company for x in cogs_type_bill_exist_previous1) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_previous1)
                total_bill_sale_type_previous1 = exist_no_bill_type_total_previous1 + cogs_type_total_exist_previous1
                gross_sale_type_total_exist_previous1 = sales_type_total_invoice_exist_previous1 - total_bill_sale_type_previous1
                # sheet.write(row, 4, gross_sale_type_total_exist_previous1 if gross_sale_type_total_exist_previous1 != 0 else '-', sale_type_format)
                gross_sale_type_total_budget_current = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 - sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12
                sheet.write(row, 1, gross_sale_type_total_budget_current if gross_sale_type_total_budget_current != 0 else '-', sale_type_format)
                invoice_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                sales_type_total_invoice_exist_current = sum(invoice_ids_current.mapped('amount_total_company')) - sum(credit_ids_current.mapped('amount_total_company'))
                exist_no_bill_type_total_current = 0
                for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                    type_no_bill_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    type_no_bill_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    exist_no_bill_amount_current = sum(x.amount_total_company for x in type_no_bill_ids_current) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current)

                    exist_no_bill_type_total_current += exist_no_bill_amount_current * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                cogs_type_bill_exist_current = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_debit_note_exist_current = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_total_exist_current = sum(x.amount_total_company for x in cogs_type_bill_exist_current) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_current)
                total_bill_sale_type_current = exist_no_bill_type_total_current + cogs_type_total_exist_current
                gross_sale_type_total_exist_current = sales_type_total_invoice_exist_current - total_bill_sale_type_current
                sheet.write(row, 2, gross_sale_type_total_exist_current if gross_sale_type_total_exist_current != 0 else '-', sale_type_format)
                gross_sale_type_total_budget_current1 = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1) - sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                sheet.write(row, 3, gross_sale_type_total_budget_current1 if gross_sale_type_total_budget_current1 != 0 else '-', sale_type_format)
                invoice_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                sales_type_total_invoice_exist_current1 = sum(invoice_ids_current1.mapped('amount_total_company')) - sum(credit_ids_current1.mapped('amount_total_company'))
                exist_no_bill_type_total_current1 = 0
                for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                    type_no_bill_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    type_no_bill_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                    exist_no_bill_amount_current1 = sum(x.amount_total_company for x in type_no_bill_ids_current1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current1)

                    exist_no_bill_type_total_current1 += exist_no_bill_amount_current1 * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100
                cogs_type_bill_exist_current1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_debit_note_exist_current1 = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('team_id', '=', team_id.id), ('sales_sub_types', '!=', False)])
                cogs_type_total_exist_current1 = sum(x.amount_total_company for x in cogs_type_bill_exist_current1) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_current1)
                total_bill_sale_type_current1 = exist_no_bill_type_total_current1 + cogs_type_total_exist_current1
                gross_sale_type_total_exist_current1 = sales_type_total_invoice_exist_current1 - total_bill_sale_type_current1
                sheet.write(row, 4, gross_sale_type_total_exist_current1 if gross_sale_type_total_exist_current1 != 0 else '-', sale_type_format)
                row += 1
                for sale_type_id in sale_type_ids:
                    sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                    sheet.write(row, 0, sale_type_id.name, sale_type_name_format)
                    gross_sale_type_total_budget_previous = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 - sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('existing_vendor_target')) / 12
                    # sheet.write(row, 1, gross_sale_type_total_budget_previous if gross_sale_type_total_budget_previous != 0 else '-', sale_type_format)
                    invoice_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    sales_type_total_invoice_exist_previous = sum(invoice_ids_previous.mapped('amount_total_company')) - sum(credit_ids_previous.mapped('amount_total_company'))
                    exist_no_bill_type_total_previous = 0
                    for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                        type_no_bill_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        type_no_bill_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        exist_no_bill_amount_previous = sum(x.amount_total_company for x in type_no_bill_ids_previous) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous)

                        exist_no_bill_type_total_previous += exist_no_bill_amount_previous * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100
                    cogs_type_bill_exist_previous = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_debit_note_exist_previous = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_total_exist_previous = sum(x.amount_total_company for x in cogs_type_bill_exist_previous) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_previous)
                    total_bill_sale_type_previous = exist_no_bill_type_total_previous + cogs_type_total_exist_previous
                    gross_sale_type_total_exist_previous = sales_type_total_invoice_exist_previous - total_bill_sale_type_previous
                    # sheet.write(row, 2, gross_sale_type_total_exist_previous if gross_sale_type_total_exist_previous != 0 else '-', sale_type_format)
                    gross_sale_type_total_budget_previous1 = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1) - sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                    # sheet.write(row, 3, gross_sale_type_total_budget_previous1 if gross_sale_type_total_budget_previous1 != 0 else '-', sale_type_format)
                    invoice_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    sales_type_total_invoice_exist_previous1 = sum(invoice_ids_previous1.mapped('amount_total_company')) - sum(credit_ids_previous1.mapped('amount_total_company'))
                    exist_no_bill_type_total_previous1 = 0
                    for sub_type_id in previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                        type_no_bill_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        type_no_bill_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        exist_no_bill_amount_previous1 = sum(x.amount_total_company for x in type_no_bill_ids_previous1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_previous1)

                        exist_no_bill_type_total_previous1 += exist_no_bill_amount_previous1 * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100
                    cogs_type_bill_exist_previous1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_debit_note_exist_previous1 = self.env['account.move'].search([('move_type', '=', 'in_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_total_exist_previous1 = sum(x.amount_total_company for x in cogs_type_bill_exist_previous1) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_previous1)
                    total_bill_sale_type_previous1 = exist_no_bill_type_total_previous1 + cogs_type_total_exist_previous1
                    gross_sale_type_total_exist_previous1 = sales_type_total_invoice_exist_previous1 - total_bill_sale_type_previous1
                    # sheet.write(row, 4, gross_sale_type_total_exist_previous1 if gross_sale_type_total_exist_previous1 != 0 else '-', sale_type_format)
                    gross_sale_type_total_budget_current = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 - sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('existing_vendor_target')) / 12
                    sheet.write(row, 1, gross_sale_type_total_budget_current if gross_sale_type_total_budget_current != 0 else '-', sale_type_format)
                    invoice_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    sales_type_total_invoice_exist_current = sum(invoice_ids_current.mapped('amount_total_company')) - sum(credit_ids_current.mapped('amount_total_company'))
                    exist_no_bill_type_total_current = 0
                    for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                        type_no_bill_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        type_no_bill_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        exist_no_bill_amount_current = sum(x.amount_total_company for x in type_no_bill_ids_current) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current)

                        exist_no_bill_type_total_current += exist_no_bill_amount_current * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100
                    cogs_type_bill_exist_current = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_debit_note_exist_current = self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_total_exist_current = sum(x.amount_total_company for x in cogs_type_bill_exist_current) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_current)
                    total_bill_sale_type_current = exist_no_bill_type_total_current + cogs_type_total_exist_current
                    gross_sale_type_total_exist_current = sales_type_total_invoice_exist_current - total_bill_sale_type_current
                    sheet.write(row, 2, gross_sale_type_total_exist_current if gross_sale_type_total_exist_current != 0 else '-', sale_type_format)
                    gross_sale_type_total_budget_current1 = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1) - sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                    sheet.write(row, 3, gross_sale_type_total_budget_current1 if gross_sale_type_total_budget_current1 != 0 else '-', sale_type_format)
                    invoice_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    sales_type_total_invoice_exist_current1 = sum(invoice_ids_current1.mapped('amount_total_company')) - sum(credit_ids_current1.mapped('amount_total_company'))
                    exist_no_bill_type_total_current1 = 0
                    for sub_type_id in current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_type_id.id == sale_type_id.id and x.team_id.id == team_id.id and x.is_no_bill != False).mapped('sale_sub_type_id'):
                        type_no_bill_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        type_no_bill_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        exist_no_bill_amount_current1 = sum(x.amount_total_company for x in type_no_bill_ids_current1) - sum(x.amount_total_company for x in type_no_bill_credit_ids_current1)

                        exist_no_bill_type_total_current1 += exist_no_bill_amount_current1 * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100
                    cogs_type_bill_exist_current1 = self.env['account.move'].search([('move_type', '=', 'in_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_debit_note_exist_current1 = self.env['account.move'].search([('move_type', '=', 'in_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '!=', False)])
                    cogs_type_total_exist_current1 = sum(x.amount_total_company for x in cogs_type_bill_exist_current1) - sum(x.amount_total_company for x in cogs_type_debit_note_exist_current1)
                    total_bill_sale_type_current1 = exist_no_bill_type_total_current1 + cogs_type_total_exist_current1
                    gross_sale_type_total_exist_current1 = sales_type_total_invoice_exist_current1 - total_bill_sale_type_current1
                    sheet.write(row, 4, gross_sale_type_total_exist_current1 if gross_sale_type_total_exist_current1 != 0 else '-', sale_type_format)
                    row += 1
                    for sub_type_id in sale_type_id.mapped('sales_sub_types'):
                        sheet.set_row(row, None, None, {'level': 1, 'hidden': True})
                        sheet.write(row, 0, sub_type_id.name, bold)
                        gross_sub_type_total_budget_previous = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 - sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).mapped('existing_vendor_target')) / 12
                        # sheet.write(row, 1, gross_sub_type_total_budget_previous if gross_sub_type_total_budget_previous != 0 else '-', bold_2)
                        sub_invoice_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sub_credit_ids_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sales_subtype_total_invoice_exist_previous = sum(sub_invoice_ids_previous.mapped('amount_total_company')) - sum(sub_credit_ids_previous.mapped('amount_total_company'))
                        subtype_no_bill_ids_sub_previous = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        subtype_no_bill_credit_ids_sub_previous = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        exist_no_bill_amount_sub_previous = sum(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_ids_sub_previous) - sum(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_credit_ids_sub_previous)
                        cogs_subtype_bill_exist_sub_previous = sum(self.env['account.move'].search([('move_type', '=', 'in_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_debit_exist_sub_previous = sum(self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'), ('invoice_date', '>=', self.date_to.replace(day=1) - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_total_bill_exist_sub_previous = cogs_subtype_bill_exist_sub_previous - cogs_subtype_debit_exist_sub_previous
                        total_bill_sub_previous = exist_no_bill_amount_sub_previous + cogs_subtype_total_bill_exist_sub_previous
                        gross_sub_type_total_exist_previous = sales_subtype_total_invoice_exist_previous - total_bill_sub_previous
                        # sheet.write(row, 2, gross_sub_type_total_exist_previous if gross_sub_type_total_exist_previous != 0 else '-', bold_2)
                        gross_sub_type_total_budget_previous1 = sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1) - sum(previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                        # sheet.write(row, 3, gross_sub_type_total_budget_previous1 if gross_sub_type_total_budget_previous1 != 0 else '-', bold_2)
                        sub_invoice_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sub_credit_ids_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sales_subtype_total_invoice_exist_previous1 = sum(sub_invoice_ids_previous1.mapped('amount_total_company')) - sum(sub_credit_ids_previous1.mapped('amount_total_company'))
                        subtype_no_bill_ids_sub_previous1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        subtype_no_bill_credit_ids_sub_previous1 = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        exist_no_bill_amount_sub_previous1 = sum(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_ids_sub_previous1) - sum(x.amount_total_company * previous_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_credit_ids_sub_previous1)
                        cogs_subtype_bill_exist_sub_previous1 = sum(self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_debit_exist_sub_previous1 = sum(self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from - relativedelta(years=1)), ('invoice_date', '<=', self.date_to.replace(day=1) - relativedelta(years=1) + relativedelta(months=1) - timedelta(days=1)), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_total_bill_exist_sub_previous1 = cogs_subtype_bill_exist_sub_previous1 - cogs_subtype_debit_exist_sub_previous1
                        total_bill_sub_previous1 = exist_no_bill_amount_sub_previous1 + cogs_subtype_total_bill_exist_sub_previous1
                        gross_sub_type_total_exist_previous1 = sales_subtype_total_invoice_exist_previous1 - total_bill_sub_previous1
                        # sheet.write(row, 4, gross_sub_type_total_exist_previous1 if gross_sub_type_total_exist_previous1 != 0 else '-', bold_2)
                        gross_sub_type_total_budget_current = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 - sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).mapped('existing_vendor_target')) / 12
                        sheet.write(row, 1, gross_sub_type_total_budget_current if gross_sub_type_total_budget_current != 0 else '-', bold_2)
                        sub_invoice_ids_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sub_credit_ids_current = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sales_subtype_total_invoice_exist_current = sum(sub_invoice_ids_current.mapped('amount_total_company')) - sum(sub_credit_ids_current.mapped('amount_total_company'))
                        subtype_no_bill_ids_sub_current = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        subtype_no_bill_credit_ids_sub_current = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        exist_no_bill_amount_sub_current = sum(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_ids_sub_current) - sum(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_credit_ids_sub_current)
                        cogs_subtype_bill_exist_sub_current = sum(self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_debit_exist_sub_current = sum(self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_to.replace(day=1)), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_total_bill_exist_sub_current = cogs_subtype_bill_exist_sub_current - cogs_subtype_debit_exist_sub_current
                        total_bill_sub_current = exist_no_bill_amount_sub_current + cogs_subtype_total_bill_exist_sub_current
                        gross_sub_type_total_exist_current = sales_subtype_total_invoice_exist_current - total_bill_sub_current
                        sheet.write(row, 2, gross_sub_type_total_exist_current if gross_sub_type_total_exist_current != 0 else '-', bold_2)
                        gross_sub_type_total_budget_current1 = sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).mapped('existing_customer_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1) - sum(current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).mapped('existing_vendor_target')) / 12 * ((date_end.year - date_start.year) * 12 + date_end.month - date_start.month + 1)
                        sheet.write(row, 3, gross_sub_type_total_budget_current1 if gross_sub_type_total_budget_current1 != 0 else '-', bold_2)
                        sub_invoice_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sub_credit_ids_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)])
                        sales_subtype_total_invoice_exist_current1 = sum(sub_invoice_ids_current1.mapped('amount_total_company')) - sum(sub_credit_ids_current1.mapped('amount_total_company'))
                        subtype_no_bill_ids_sub_current1 = self.env['account.move'].search([('move_type', '=', 'out_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        subtype_no_bill_credit_ids_sub_current1 = self.env['account.move'].search([('move_type', '=', 'out_refund'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id), ('sales_sub_types.is_no_bill', '!=', False)])
                        exist_no_bill_amount_sub_current1 = sum(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id and x.team_id.id == team_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_ids_sub_current1) - sum(x.amount_total_company * current_year_budget.sale_budget_lines.filtered(lambda x: x.sale_sub_type_id.id == sub_type_id.id).existing_vendor_target_percent / 100 for x in subtype_no_bill_credit_ids_sub_current1)
                        cogs_subtype_bill_exist_sub_current1 = sum(self.env['account.move'].search([('move_type', '=', 'in_invoice'),('team_id', '=', team_id.id), ('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_debit_exist_sub_current1 = sum(self.env['account.move'].search([('move_type', '=', 'in_refund'), ('team_id', '=', team_id.id),('state', '=', 'posted'),('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to), ('sale_type_id', '=', sale_type_id.id), ('sales_sub_types', '=', sub_type_id.id)]).mapped('amount_total_company'))
                        cogs_subtype_total_bill_exist_sub_current1 = cogs_subtype_bill_exist_sub_current1 - cogs_subtype_debit_exist_sub_current1
                        total_bill_sub_current1 = exist_no_bill_amount_sub_current1 + cogs_subtype_total_bill_exist_sub_current1
                        gross_sub_type_total_exist_current1 = sales_subtype_total_invoice_exist_current1 - total_bill_sub_current1
                        sheet.write(row, 4, gross_sub_type_total_exist_current1 if gross_sub_type_total_exist_current1 != 0 else '-', bold_2)
                        row += 1


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
        fo = open(url + 'Daily Report New.xlsx', "rb+")
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
            'res_model': 'daily.report.new',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
