from odoo import models, fields, api, _
import base64
import xlsxwriter
from odoo.exceptions import ValidationError


class DailyReport(models.TransientModel):
    _name = 'daily.report'
    _rec_name = 'report_details'
    _description = 'Daily Report'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    report_details = fields.Binary('Daily Report', readonly=True)
    report_details_name = fields.Char('Filename', size=64, readonly=True)

    def action_daily_report(self):
        if self.date_from == False and self.date_to == False:
            raise ValidationError('Please select date from and date to')
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Daily Report.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center'})
        title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF66', 'border': 1, 'right': 1})
        sub_title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#90ee90', 'border': 1, 'right': 1})
        parent_format = workbook.add_format(
            {'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#F0CCB0'})
        sale_type_format = workbook.add_format(
            {'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#D3D3D3'})
        total_format = workbook.add_format(
            {'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#FFCCCB'})
        format1.set_text_wrap()
        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'right'})
        bold_1 = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        bold_2 = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        sheet.set_row(2, 40)
        sheet.set_row(4, 20)
        sheet.set_row(5, 20)
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 20)
        sheet.set_column('K:K', 20)
        sheet.set_column('L:L', 20)
        sheet.set_column('M:M', 20)
        sheet.set_column('N:N', 20)
        sheet.set_column('O:O', 20)
        sheet.set_column('P:P', 20)
        sheet.set_column('Q:Q', 20)
        sheet.set_column('R:R', 20)
        sheet.set_column('S:S', 20)
        sheet.set_column('T:T', 20)
        sheet.set_column('U:U', 20)
        sheet.set_column('V:V', 20)
        sheet.set_column('W:W', 20)
        sheet.set_column('X:X', 20)
        sheet.set_column('Y:Y', 20)
        sheet.set_column('Z:Z', 20)
        sheet.set_column('AA:AA', 20)
        sheet.set_column('AB:AB', 20)
        sheet.set_column('AC:AC', 20)
        sheet.set_column('AD:AD', 20)
        sheet.set_column('AE:AE', 20)
        sheet.set_column('AF:AF', 20)
        sheet.set_column('AG:AG', 20)
        sheet.set_column('AH:AH', 20)
        sheet.set_column('AI:AI', 20)
        sheet.set_column('AJ:AJ', 20)
        sheet.set_column('AK:AK', 20)
        sheet.set_column('AL:AL', 20)
        sheet.set_column('AM:AM', 20)
        sheet.set_column('AN:AN', 20)
        sheet.set_column('AO:AO', 20)
        sheet.set_column('AP:AP', 20)
        sheet.set_column('AQ:AQ', 20)
        sheet.set_column('AR:AR', 20)
        sheet.set_column('AS:AS', 20)
        sheet.set_column('AT:AT', 20)
        sheet.set_column('AU:AU', 20)

        row = 0
        col = 0
        sheet.merge_range('B3:D3', 'DAILY REPORT', bold_1)
        sheet.merge_range('B5:D5', 'TARGET', title_format)
        sheet.merge_range('E5:G5', 'BILLING AS ON...', title_format)
        sheet.merge_range('H5:J5', 'OPF', title_format)
        sheet.write(5, 0, 'DESCRIPTION', sub_title_format)
        sheet.write(5, 1, 'EXISTING', sub_title_format)
        sheet.write(5, 2, 'NEW', sub_title_format)
        sheet.write(5, 3, 'TOTAL', sub_title_format)
        sheet.write(5, 4, 'EXISTING', sub_title_format)
        sheet.write(5, 5, 'NEW', sub_title_format)
        sheet.write(5, 6, 'TOTAL', sub_title_format)
        sheet.write(5, 7, 'EXISTING', sub_title_format)
        sheet.write(5, 8, 'NEW', sub_title_format)
        sheet.write(5, 9, 'TOTAL', sub_title_format)

        sale_type = self.env['sale.type'].search([])

        # date_from = self.date_from.strftime('%d/%m/%Y')
        # date_to = self.date_to.strftime('%d/%m/%Y')

        sheet.write(6, 0, 'A) Sales', parent_format)
        exist_cust_parent_target = sum(sale_type.mapped('sales_sub_types').mapped('existing_customer_target'))
        new_cust_parent_target = sum(sale_type.mapped('sales_sub_types').mapped('new_customer_target'))
        cust_inv_parent_tot = exist_cust_parent_target + new_cust_parent_target
        sheet.write(6, 1, exist_cust_parent_target, parent_format)
        sheet.write(6, 2, new_cust_parent_target, parent_format)
        sheet.write(6, 3, cust_inv_parent_tot, parent_format)
        exist_billing_as_on_parent = self.env['account.move'].search(
            [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to),
             ('move_type', '=', 'out_invoice'), ('partner_id.is_new', '=', False), ('sales_sub_types', '!=', False),
             ('sale_type_id', '!=', False)])
        new_billing_as_on_parent = self.env['account.move'].search(
            [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to),
             ('move_type', '=', 'out_invoice'), ('partner_id.is_new', '=', True), ('sales_sub_types', '!=', False),
             ('sale_type_id', '!=', False)])
        sheet.write(6, 4, sum(exist_billing_as_on_parent.mapped('amount_total_company')), parent_format)
        sheet.write(6, 5, sum(new_billing_as_on_parent.mapped('amount_total_company')), parent_format)
        sheet.write(6, 6, sum(exist_billing_as_on_parent.mapped('amount_total_company')) + sum(
            new_billing_as_on_parent.mapped('amount_total_company')), parent_format)
        rows = 7
        total_sales_recs = exist_billing_as_on_parent | new_billing_as_on_parent
        for sale in sale_type:
            sale_type_rows = rows
            sale_type_recs = total_sales_recs.filtered(lambda x: x.sale_type_id.id == sale.id)
            sheet.write(sale_type_rows, 0, sale.name, sale_type_format)
            exist_customer_tot = sum(sale.mapped('sales_sub_types').mapped('existing_customer_target'))
            new_customer_tot = sum(sale.mapped('sales_sub_types').mapped('new_customer_target'))
            sheet.write(sale_type_rows, 1, exist_customer_tot, sale_type_format)
            sheet.write(sale_type_rows, 2, new_customer_tot, sale_type_format)
            sheet.write(sale_type_rows, 3, exist_customer_tot + new_customer_tot, sale_type_format)
            exist_billing_as_on_child = sale_type_recs.filtered(lambda x: not x.partner_id.is_new)
            new_billing_as_on_child = sale_type_recs.filtered(lambda x: x.partner_id.is_new)
            sheet.write(sale_type_rows, 4, sum(exist_billing_as_on_child.mapped('amount_total_company')),
                        sale_type_format)
            sheet.write(sale_type_rows, 5, sum(new_billing_as_on_child.mapped('amount_total_company')),
                        sale_type_format)
            sheet.write(sale_type_rows, 6, sum(exist_billing_as_on_child.mapped('amount_total_company')) + sum(
                new_billing_as_on_child.mapped('amount_total_company')), sale_type_format)

            sale_type_rows += 1
            rows += 1

            # SALES - sale sub type loop
            for sub_type in sale.sales_sub_types:
                sheet.write(rows, 0, sub_type.name, bold)
                sheet.write(rows, 1, sum(sub_type.mapped('existing_customer_target')), bold_2)
                sheet.write(rows, 2, sum(sub_type.mapped('new_customer_target')), bold_2)
                sheet.write(rows, 3,
                            sum(sub_type.mapped('existing_customer_target') + sub_type.mapped('new_customer_target')),
                            bold_2)
                sales_sub_type_recs_false = sale_type_recs.filtered(
                    lambda x: not x.partner_id.is_new and x.sales_sub_types.id == sub_type.id)
                sales_sub_type_recs_true = sale_type_recs.filtered(
                    lambda x: x.partner_id.is_new and x.sales_sub_types.id == sub_type.id)
                sheet.write(rows, 4, sum(sales_sub_type_recs_false.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 5, sum(sales_sub_type_recs_true.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 6, sum(sales_sub_type_recs_false.mapped('amount_total_company')) + sum(
                    sales_sub_type_recs_true.mapped('amount_total_company')), bold_2)
                rows += 1

        sheet.write(rows, 0, 'B) COGS', parent_format)
        exist_vendor_parent_target = sum(sale_type.mapped('sales_sub_types').mapped('existing_vendor_target'))
        new_vendor_parent_target = sum(sale_type.mapped('sales_sub_types').mapped('new_vendor_target'))
        vendor_bill_parent_tot = exist_vendor_parent_target + new_vendor_parent_target
        sheet.write(rows, 1, exist_vendor_parent_target, parent_format)
        sheet.write(rows, 2, new_vendor_parent_target, parent_format)
        sheet.write(rows, 3, vendor_bill_parent_tot, parent_format)
        exist_cogs_billing_as_on_parent = self.env['account.move'].search(
            [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to),
             ('move_type', '=', 'in_invoice'), ('vendor_bill', '!=', False), ('partner_id.is_new', '=', False),
             ('sales_sub_types', '!=', False)])
        new_cogs_billing_as_on_parent = self.env['account.move'].search(
            [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to),
             ('move_type', '=', 'in_invoice'), ('vendor_bill', '!=', False), ('partner_id.is_new', '!=', False),
             ('sales_sub_types', '!=', False)])
        grand_total_new_vendor = 0
        grand_total_exist_vendor = 0
        exit_invoice_rec = total_sales_recs.filtered(lambda x: not x.partner_id.is_new and x.sales_sub_types.is_no_bill)
        new_invoice_rec = total_sales_recs.filtered(lambda x: x.partner_id.is_new and x.sales_sub_types.is_no_bill)
        for sub_type in sale_type.mapped('sales_sub_types').filtered(lambda x: x.is_no_bill):
            grand_total_exist_vendor += (sum(exit_invoice_rec.filtered(lambda x: x.sales_sub_types.id == sub_type.id).mapped('amount_total_company')) - ((sum(exit_invoice_rec.filtered(lambda x: x.sales_sub_types.id == sub_type.id).mapped('amount_total_company')) * sub_type.existing_vendor_target_percent)))
            grand_total_new_vendor += (sum(new_invoice_rec.filtered(lambda x: x.sales_sub_types.id == sub_type.id).mapped('amount_total_company')) - ((sum(new_invoice_rec.filtered(lambda x: x.sales_sub_types.id == sub_type.id).mapped('amount_total_company')) * sub_type.new_vendor_target_percent)))

        sheet.write(rows, 4, sum(exist_cogs_billing_as_on_parent.mapped('amount_total_company'))+grand_total_exist_vendor, parent_format)
        sheet.write(rows, 5, sum(new_cogs_billing_as_on_parent.mapped('amount_total_company'))+grand_total_new_vendor, parent_format)
        sheet.write(rows, 6, sum(exist_cogs_billing_as_on_parent.mapped('amount_total_company')) + sum(
            new_cogs_billing_as_on_parent.mapped('amount_total_company'))+grand_total_exist_vendor+grand_total_new_vendor, parent_format)
        rows += 1

        # COGS - sale type loop
        total_cogs_recs = exist_cogs_billing_as_on_parent | new_cogs_billing_as_on_parent
        for sale in sale_type:
            sale_type_rows = rows
            sale_type_recs = total_cogs_recs.filtered(lambda x: x.sale_type_id.id == sale.id)
            sheet.write(sale_type_rows, 0, sale.name, sale_type_format)
            exist_vendor_tot = sum(sale.mapped('sales_sub_types').mapped('existing_vendor_target'))
            new_vendor_tot = sum(sale.mapped('sales_sub_types').mapped('new_vendor_target'))
            sheet.write(sale_type_rows, 1, exist_vendor_tot, sale_type_format)
            sheet.write(sale_type_rows, 2, new_vendor_tot, sale_type_format)
            sheet.write(sale_type_rows, 3, exist_vendor_tot + new_vendor_tot, sale_type_format)
            exist_cogs_billing_as_on_child = sale_type_recs.filtered(lambda x: not x.partner_id.is_new)
            new_cogs_billing_as_on_child = sale_type_recs.filtered(lambda x: x.partner_id.is_new)

            # Function to get total for % based invoice target
            sales_type_cogs_false = total_sales_recs.filtered(
                lambda x: not x.partner_id.is_new and x.sale_type_id.id == sale.id and x.sales_sub_types.is_no_bill)
            total_sales_type_cogs_false = 0
            for invoice in sales_type_cogs_false:
                total_sales_type_cogs_false += (invoice.amount_total_company - (invoice.amount_total_company * invoice.sales_sub_types.existing_vendor_target_percent))
            sales_type_cogs_true = total_sales_recs.filtered(
                lambda x: x.partner_id.is_new and x.sale_type_id.id == sale.id and x.sales_sub_types.is_no_bill)
            total_sales_type_cogs_true = 0
            for invoice in sales_type_cogs_true:
                total_sales_type_cogs_true += (invoice.amount_total_company - (invoice.amount_total_company * invoice.sales_sub_types.new_vendor_target_percent))

            sheet.write(sale_type_rows, 4, sum(exist_cogs_billing_as_on_child.mapped(
                'amount_total_company')) + total_sales_type_cogs_false, sale_type_format)
            sheet.write(sale_type_rows, 5,
                        sum(new_cogs_billing_as_on_child.mapped('amount_total_company')) + total_sales_type_cogs_true,
                        sale_type_format)
            sheet.write(sale_type_rows, 6, sum(exist_cogs_billing_as_on_child.mapped('amount_total_company')) + sum(
                new_cogs_billing_as_on_child.mapped(
                    'amount_total_company')) + total_sales_type_cogs_false + total_sales_type_cogs_true,
                        sale_type_format)

            sale_type_rows += 1
            rows += 1

            # COGS - sale sub type loop
            for sub_type in sale.sales_sub_types:
                sheet.write(rows, 0, sub_type.name, bold)
                sheet.write(rows, 1, sum(sub_type.mapped('existing_vendor_target')), bold_2)
                sheet.write(rows, 2, sum(sub_type.mapped('new_vendor_target')), bold_2)
                sheet.write(rows, 3,
                            sum(sub_type.mapped('existing_vendor_target')) + sum(sub_type.mapped('new_vendor_target')),
                            bold_2)
                sales_sub_type_cogs_false = sale_type_recs.filtered(
                    lambda x: not x.partner_id.is_new and x.sales_sub_types.id == sub_type.id)
                sales_sub_type_cogs_true = sale_type_recs.filtered(
                    lambda x: x.partner_id.is_new and x.sales_sub_types.id == sub_type.id)
                if sub_type.is_no_bill:
                    subtype_sales_records = total_sales_recs.filtered(lambda x: x.sales_sub_types.id == sub_type.id)
                    exist_vendor_sales_target = sum(
                        subtype_sales_records.filtered(lambda x: not x.partner_id.is_new).mapped(
                            'amount_total_company')) * sub_type.existing_vendor_target_percent
                    new_vendor_sales_target = sum(subtype_sales_records.filtered(lambda x: x.partner_id.is_new).mapped(
                        'amount_total_company')) * sub_type.existing_vendor_target_percent
                    sheet.write(rows, 4, sum(subtype_sales_records.filtered(lambda x: not x.partner_id.is_new).mapped('amount_total_company')) - exist_vendor_sales_target, bold_2)
                    sheet.write(rows, 5, sum(subtype_sales_records.filtered(lambda x: x.partner_id.is_new).mapped('amount_total_company')) - new_vendor_sales_target, bold_2)
                    sheet.write(rows, 6, exist_vendor_sales_target + new_vendor_sales_target, bold_2)
                else:
                    sheet.write(rows, 4, sum(sales_sub_type_cogs_false.mapped('amount_total_company')), bold_2)
                    sheet.write(rows, 5, sum(sales_sub_type_cogs_true.mapped('amount_total_company')), bold_2)
                    sheet.write(rows, 6, sum(sales_sub_type_cogs_false.mapped('amount_total_company')) + sum(
                        sales_sub_type_cogs_true.mapped('amount_total_company')), bold_2)
                rows += 1

        sheet.write(rows, 0, 'C) Gross Margin', parent_format)
        exist_gross_marg_target = sum(sale_type.mapped('sales_sub_types').mapped('existing_customer_target')) - (
            sum(sale_type.mapped('sales_sub_types').mapped('existing_vendor_target')))
        new_gross_marg_target = sum(sale_type.mapped('sales_sub_types').mapped('new_customer_target')) - (
            sum(sale_type.mapped('sales_sub_types').mapped('new_vendor_target')))
        gross_margin_parent_tot = exist_gross_marg_target + new_gross_marg_target
        sheet.write(rows, 1, exist_cust_parent_target - exist_vendor_parent_target, parent_format)
        sheet.write(rows, 2, new_cust_parent_target - new_vendor_parent_target, parent_format)
        sheet.write(rows, 3, cust_inv_parent_tot - vendor_bill_parent_tot, parent_format)

        sheet.write(rows, 4, sum(exist_billing_as_on_parent.mapped('amount_total_company')) - sum(
            exist_cogs_billing_as_on_parent.mapped('amount_total_company'))-grand_total_exist_vendor, parent_format)
        sheet.write(rows, 5, sum(new_billing_as_on_parent.mapped('amount_total_company')) - sum(
            new_cogs_billing_as_on_parent.mapped('amount_total_company'))-grand_total_new_vendor, parent_format)
        sheet.write(rows, 6, (sum(exist_billing_as_on_parent.mapped('amount_total_company')) - sum(
            exist_cogs_billing_as_on_parent.mapped('amount_total_company'))) - grand_total_exist_vendor + (sum(new_billing_as_on_parent.mapped('amount_total_company')) - sum(new_cogs_billing_as_on_parent.mapped('amount_total_company')))-grand_total_new_vendor, parent_format)
        rows += 1

        # GROSS MARGIN - sale type loop
        for sale in sale_type:
            sale_type_rows = rows
            sale_type_recs_of_sales = new_billing_as_on_parent.filtered(lambda x: x.sale_type_id.id == sale.id)|exist_billing_as_on_parent.filtered(lambda x: x.sale_type_id.id == sale.id)
            # sale_type_recs_of_sales = self.env['account.move'].search(
            #     [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from),
            #      ('invoice_date', '<=', self.date_to), ('move_type', '=', 'out_invoice'),
            #      ('sale_type_id', 'in', sale.ids), ('sales_sub_types', '!=', False)])
            sale_type_recs_of_cogs = new_cogs_billing_as_on_parent.filtered(lambda x: x.sale_type_id.id == sale.id)|exist_cogs_billing_as_on_parent.filtered(lambda x: x.sale_type_id.id == sale.id)
            # sale_type_recs_of_cogs = self.env['account.move'].search(
            #     [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from),
            #      ('invoice_date', '<=', self.date_to), ('move_type', '=', 'in_invoice'), ('vendor_bill', '!=', False),
            #      ('sale_type_id', 'in', sale.ids), ('sales_sub_types', '!=', False)])
            sheet.write(rows, 0, sale.name, sale_type_format)
            exist_gross_margin_result = sum(sale.mapped('sales_sub_types').mapped('existing_customer_target')) - (
                sum(sale.mapped('sales_sub_types').mapped('existing_vendor_target')))
            new_gross_margin_result = sum(sale.mapped('sales_sub_types').mapped('new_customer_target')) - (
                sum(sale.mapped('sales_sub_types').mapped('new_vendor_target')))
            sheet.write(sale_type_rows, 1, exist_gross_margin_result, sale_type_format)
            sheet.write(sale_type_rows, 2, new_gross_margin_result, sale_type_format)
            sheet.write(sale_type_rows, 3, exist_gross_margin_result + new_gross_margin_result, sale_type_format)

            exist_customer_margin_billing = sale_type_recs_of_sales.filtered(lambda x: not x.partner_id.is_new and not x.sales_sub_types.is_no_bill)
            new_customer_margin_billing = sale_type_recs_of_sales.filtered(lambda x: x.partner_id.is_new and not x.sales_sub_types.is_no_bill)
            exist_vendor_margin_billing = sale_type_recs_of_cogs.filtered(lambda x: not x.partner_id.is_new and not x.sales_sub_types.is_no_bill)
            new_vendor_margin_billing = sale_type_recs_of_cogs.filtered(lambda x: x.partner_id.is_new and not x.sales_sub_types.is_no_bill)

            total_exist_customer_margin_billing = sum(exist_customer_margin_billing.mapped('amount_total_company'))
            total_new_customer_margin_billing = sum(new_customer_margin_billing.mapped('amount_total_company'))
            total_exist_vendor_margin_billing = sum(exist_vendor_margin_billing.mapped('amount_total_company'))
            total_new_vendor_margin_billing = sum(new_vendor_margin_billing.mapped('amount_total_company'))
            for subtype in sale.sales_sub_types:
                new_customer_invoice_no_bill = sale_type_recs_of_sales.filtered(lambda x: x.partner_id.is_new and x.sales_sub_types.id == subtype.id and x.sales_sub_types.is_no_bill)
                exist_customer_invoice_no_bill = sale_type_recs_of_sales.filtered(lambda x: not x.partner_id.is_new and x.sales_sub_types.id == subtype.id and x.sales_sub_types.is_no_bill)
                total_exist_vendor_margin_billing += (sum(exist_customer_invoice_no_bill.mapped('amount_total_company')) * subtype.existing_vendor_target_percent)
                total_new_vendor_margin_billing += (sum(new_customer_invoice_no_bill.mapped('amount_total_company')) * subtype.new_vendor_target_percent)
            sheet.write(sale_type_rows, 4, total_exist_customer_margin_billing + total_exist_vendor_margin_billing, sale_type_format)
            sheet.write(sale_type_rows, 5, total_new_customer_margin_billing + total_new_vendor_margin_billing, sale_type_format)
            sheet.write(sale_type_rows, 6, total_exist_customer_margin_billing + total_exist_vendor_margin_billing + total_new_customer_margin_billing + total_new_vendor_margin_billing, sale_type_format)
            sale_type_rows += 1
            rows += 1

            # GROSS MARGIN - sale subtype loop
            for subtype in sale.sales_sub_types:
                get_exist_cust_target = sum(subtype.mapped('existing_customer_target'))
                get_exist_vendor_target = sum(subtype.mapped('existing_customer_target')) * sum(
                    subtype.mapped('existing_vendor_target_percent'))
                get_new_cust_target = sum(subtype.mapped('new_customer_target'))
                get_new_vendor_target = sum(subtype.mapped('new_customer_target')) * sum(
                    subtype.mapped('new_vendor_target_percent'))
                total_exist_gross_margin = get_exist_cust_target - get_exist_vendor_target
                total_new_gross_margin = get_new_cust_target - get_new_vendor_target

                sheet.write(rows, 0, subtype.name, bold)
                sheet.write(rows, 1, get_exist_cust_target - get_exist_vendor_target, bold_2)
                sheet.write(rows, 2, get_new_cust_target - get_new_vendor_target, bold_2)
                sheet.write(rows, 3, total_exist_gross_margin + total_new_gross_margin, bold_2)

                exist_customer_sub_type_margin_false = sale_type_recs_of_sales.filtered(
                    lambda x: not x.partner_id.is_new and x.sales_sub_types.id == subtype.id)
                new_customer_sub_type_margin_true = sale_type_recs_of_sales.filtered(
                    lambda x: x.partner_id.is_new and x.sales_sub_types.id == subtype.id)
                exist_vendor_sub_type_margin_false = sale_type_recs_of_cogs.filtered(
                    lambda x: not x.partner_id.is_new and x.sales_sub_types.id == subtype.id)
                new_vendor_sub_type_margin_true = sale_type_recs_of_cogs.filtered(
                    lambda x: x.partner_id.is_new and x.sales_sub_types.id == subtype.id)
                if subtype.is_no_bill:
                    new_actual_value = sum(exist_customer_sub_type_margin_false.mapped(
                        'amount_total_company')) * subtype.existing_vendor_target_percent
                    exist_actual_value = sum(new_customer_sub_type_margin_true.mapped(
                        'amount_total_company')) * subtype.new_vendor_target_percent
                    sheet.write(rows, 4, new_actual_value, bold_2)
                    sheet.write(rows, 5, exist_actual_value, bold_2)
                    sheet.write(rows, 6, new_actual_value + exist_actual_value, bold_2)
                else:
                    sheet.write(rows, 4, sum(exist_customer_sub_type_margin_false.mapped('amount_total_company')) - sum(
                        exist_vendor_sub_type_margin_false.mapped('amount_total_company')), bold_2)
                    sheet.write(rows, 5, sum(new_customer_sub_type_margin_true.mapped('amount_total_company')) - sum(
                        new_vendor_sub_type_margin_true.mapped('amount_total_company')), bold_2)
                    sheet.write(rows, 6,
                                (sum(exist_customer_sub_type_margin_false.mapped('amount_total_company')) - sum(
                                    exist_vendor_sub_type_margin_false.mapped('amount_total_company'))) + (
                                        sum(new_customer_sub_type_margin_true.mapped('amount_total_company')) - sum(
                                    new_vendor_sub_type_margin_true.mapped('amount_total_company'))), bold_2)
                rows += 1

        sheet.write(rows, 0, 'D) Direct Expenses', parent_format)
        exist_exp_parent_target = sum(sale_type.mapped('sales_sub_types').mapped('existing_expense_target'))
        new_exp_parent_target = sum(sale_type.mapped('sales_sub_types').mapped('new_expense_target'))
        dir_exp_parent_tot = exist_exp_parent_target + new_exp_parent_target
        sheet.write(rows, 1, exist_exp_parent_target, parent_format)
        sheet.write(rows, 2, new_exp_parent_target, parent_format)
        sheet.write(rows, 3, dir_exp_parent_tot, parent_format)

        exist_expense_billing_as_on_parent = self.env['account.move'].search(
            [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to),
             ('move_type', '=', 'in_invoice'), ('expense_bill', '!=', False), ('partner_id.is_new', '!=', False),
             ('sales_sub_types', '!=', False)])
        new_expense_billing_as_on_parent = self.env['account.move'].search(
            [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to),
             ('move_type', '=', 'in_invoice'), ('expense_bill', '!=', False), ('partner_id.is_new', '=', False),
             ('sales_sub_types', '!=', False)])

        sheet.write(rows, 4, sum(new_expense_billing_as_on_parent.mapped('amount_total_company')), parent_format)
        sheet.write(rows, 5, sum(exist_expense_billing_as_on_parent.mapped('amount_total_company')), parent_format)
        sheet.write(rows, 6, sum(exist_expense_billing_as_on_parent.mapped('amount_total_company')) + sum(
            new_expense_billing_as_on_parent.mapped('amount_total_company')), parent_format)
        rows += 1

        # DIRECT EXPENSES - sale type loop
        for sale in sale_type:
            sale_type_rows = rows
            sale_type_recs = self.env['account.move'].search(
                [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from),
                 ('invoice_date', '<=', self.date_to), ('move_type', '=', 'in_invoice'), ('expense_bill', '!=', False),
                 ('sale_type_id', 'in', sale.ids), ('sales_sub_types', '!=', False)])
            sheet.write(rows, 0, sale.name, sale_type_format)
            exist_exp_tot = sum(sale.mapped('sales_sub_types').mapped('existing_expense_target'))
            new_exp_tot = sum(sale.mapped('sales_sub_types').mapped('new_expense_target'))
            sheet.write(sale_type_rows, 1, exist_exp_tot, sale_type_format)
            sheet.write(sale_type_rows, 2, new_exp_tot, sale_type_format)
            sheet.write(sale_type_rows, 3, exist_exp_tot + new_exp_tot, sale_type_format)

            exist_expense_billing_as_on_child = sale_type_recs.filtered(lambda x: not x.partner_id.is_new)
            new_expense_billing_as_on_child = sale_type_recs.filtered(lambda x: x.partner_id.is_new)
            sheet.write(sale_type_rows, 4, sum(exist_expense_billing_as_on_child.mapped('amount_total_company')),
                        sale_type_format)
            sheet.write(sale_type_rows, 5, sum(new_expense_billing_as_on_child.mapped('amount_total_company')),
                        sale_type_format)
            sheet.write(sale_type_rows, 6, sum(exist_expense_billing_as_on_child.mapped('amount_total_company')) + sum(
                new_expense_billing_as_on_child.mapped('amount_total_company')), sale_type_format)
            sale_type_rows += 1
            rows += 1

            for calc in sale.sales_sub_types:
                sheet.write(rows, 0, calc.name, bold)
                sheet.write(rows, 1, sum(calc.mapped('existing_expense_target')), bold_2)
                sheet.write(rows, 2, sum(calc.mapped('new_expense_target')), bold_2)
                sheet.write(rows, 3, sum(calc.mapped('existing_expense_target') + calc.mapped('new_expense_target')),
                            bold_2)

                sales_sub_type_expense_false = sale_type_recs.filtered(
                    lambda x: not x.partner_id.is_new and x.sales_sub_types.id == calc.id)
                sales_sub_type_expense_true = sale_type_recs.filtered(
                    lambda x: x.partner_id.is_new and x.sales_sub_types.id == calc.id)
                sheet.write(rows, 4, sum(sales_sub_type_expense_false.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 5, sum(sales_sub_type_expense_true.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 6, sum(sales_sub_type_expense_false.mapped('amount_total_company')) + sum(
                    sales_sub_type_expense_true.mapped('amount_total_company')), bold_2)
                rows += 1
        #Gross profit print
        sheet.write(rows, 0, 'E) Gross Profit', parent_format)
        sheet.write(rows, 1, exist_gross_marg_target - exist_exp_parent_target, parent_format)
        sheet.write(rows, 2, new_gross_marg_target - new_exp_parent_target, parent_format)
        sheet.write(rows, 3, gross_margin_parent_tot - dir_exp_parent_tot, parent_format)
        profit_exist_grant_total = (sum(exist_billing_as_on_parent.mapped('amount_total_company')) - grand_total_exist_vendor - sum(
            exist_cogs_billing_as_on_parent.mapped('amount_total_company'))) - sum(
            exist_expense_billing_as_on_parent.mapped('amount_total_company'))
        profit_new_grant_total = (sum(new_billing_as_on_parent.mapped('amount_total_company')) - grand_total_new_vendor - sum(
            new_cogs_billing_as_on_parent.mapped('amount_total_company'))) - sum(
            new_expense_billing_as_on_parent.mapped('amount_total_company'))

        sheet.write(rows, 4, profit_exist_grant_total, parent_format)
        sheet.write(rows, 5,profit_new_grant_total, parent_format)
        sheet.write(rows, 6, profit_new_grant_total+profit_exist_grant_total, parent_format)
        rows += 1
        for sale in sale_type:
            sale_type_rows = rows
            sheet.write(rows, 0, sale.name, sale_type_format)
            exist_gross_profit_result = (sum(sale.mapped('sales_sub_types').mapped('existing_customer_target')) - sum(
                sale.mapped('sales_sub_types').mapped('existing_vendor_target_percent'))) - sum(
                sale.mapped('sales_sub_types').mapped('existing_expense_target'))
            new_gross_profit_result = (sum(sale.mapped('sales_sub_types').mapped('new_customer_target')) - sum(
                sale.mapped('sales_sub_types').mapped('new_vendor_target_percent'))) - sum(
                sale.mapped('sales_sub_types').mapped('new_expense_target'))
            sheet.write(sale_type_rows, 1, exist_gross_profit_result, sale_type_format)
            sheet.write(sale_type_rows, 2, new_gross_profit_result, sale_type_format)
            sheet.write(sale_type_rows, 3, exist_gross_profit_result + new_gross_profit_result, sale_type_format)

            sale_type_recs_of_sales = self.env['account.move'].search(
                [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from),
                 ('invoice_date', '<=', self.date_to), ('move_type', '=', 'out_invoice'),
                 ('sale_type_id', 'in', sale.ids), ('sales_sub_types', '!=', False)])
            exist_customer_margin_billing = sale_type_recs_of_sales.filtered(lambda x: not x.partner_id.is_new)
            sale_type_recs_of_cogs = self.env['account.move'].search(
                [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from),
                 ('invoice_date', '<=', self.date_to), ('move_type', '=', 'in_invoice'), ('vendor_bill', '!=', False),
                 ('sale_type_id', 'in', sale.ids), ('sales_sub_types', '!=', False)])
            exist_vendor_margin_billing = sale_type_recs_of_cogs.filtered(lambda x: not x.partner_id.is_new)
            sale_type_recs = self.env['account.move'].search(
                [('state', 'in', ['posted']), ('invoice_date', '>=', self.date_from),
                 ('invoice_date', '<=', self.date_to), ('move_type', '=', 'in_invoice'), ('expense_bill', '!=', False),
                 ('sale_type_id', 'in', sale.ids), ('sales_sub_types', '!=', False)])
            exist_expense_billing_as_on_child = sale_type_recs.filtered(lambda x: not x.partner_id.is_new)
            new_customer_margin_billing = sale_type_recs_of_sales.filtered(lambda x: x.partner_id.is_new)
            new_vendor_margin_billing = sale_type_recs_of_cogs.filtered(lambda x: x.partner_id.is_new)
            new_expense_billing_as_on_child = sale_type_recs.filtered(lambda x: x.partner_id.is_new)
            profit_exist_vendor_subtotal = (sum(exist_customer_margin_billing.mapped('amount_total_company')) - sum(
                exist_vendor_margin_billing.mapped('amount_total_company'))) - sum(
                exist_expense_billing_as_on_child.mapped('amount_total_company'))
            profit_new_vendor_subtotal = (sum(new_customer_margin_billing.mapped('amount_total_company')) - sum(
                new_vendor_margin_billing.mapped('amount_total_company'))) - sum(
                new_expense_billing_as_on_child.mapped('amount_total_company'))

            for subtype in sale.sales_sub_types:
                new_customer_invoice_no_bill = sale_type_recs_of_sales.filtered(lambda x: x.partner_id.is_new and x.sales_sub_types.id == subtype.id and x.sales_sub_types.is_no_bill)
                profit_new_vendor_subtotal -= (sum(new_customer_invoice_no_bill.mapped('amount_total_company')) - (sum(new_customer_invoice_no_bill.mapped('amount_total_company')) * subtype.new_vendor_target_percent))
                exist_customer_invoice_no_bill = sale_type_recs_of_sales.filtered(lambda x: not x.partner_id.is_new and x.sales_sub_types.id == subtype.id and x.sales_sub_types.is_no_bill)
                profit_exist_vendor_subtotal -= (sum(exist_customer_invoice_no_bill.mapped('amount_total_company')) - (sum(exist_customer_invoice_no_bill.mapped('amount_total_company')) * subtype.existing_vendor_target_percent))
            sheet.write(sale_type_rows, 4, profit_exist_vendor_subtotal, sale_type_format)
            sheet.write(sale_type_rows, 5, profit_new_vendor_subtotal, sale_type_format)
            sheet.write(sale_type_rows, 6, profit_exist_vendor_subtotal + profit_new_vendor_subtotal, sale_type_format)
            rows += 1

        # SALE ORDER LOOP
        sale_order_recs = self.env['sale.order'].search([])
        exist_so_opf = sale_order_recs.search([('state', 'in', ['sale', 'done']), ('date_order', '>=', self.date_from),
                                               ('date_order', '<=', self.date_to), ('sale_type_id', '!=', False),
                                               ('partner_id.is_new', '!=', False), ('sale_sub_type_id', '!=', False)])
        new_so_opf = sale_order_recs.search([('state', 'in', ['sale', 'done']), ('date_order', '>=', self.date_from),
                                             ('date_order', '<=', self.date_to), ('sale_type_id', '!=', False),
                                             ('partner_id.is_new', '=', False), ('sale_sub_type_id', '!=', False)])
        sheet.write(6, 7, sum(new_so_opf.mapped('amount_total_company')), parent_format)
        sheet.write(6, 8, sum(exist_so_opf.mapped('amount_total_company')), parent_format)
        sheet.write(6, 9,
                    sum(exist_so_opf.mapped('amount_total_company')) + sum(new_so_opf.mapped('amount_total_company')),
                    parent_format)
        rows = 7
        for sale in sale_type:
            sale_type_rows = rows
            sheet.write(sale_type_rows, 7,
                        sum(new_so_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')),
                        sale_type_format)
            sheet.write(sale_type_rows, 8, sum(exist_so_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped(
                'amount_total_company')), sale_type_format)
            sheet.write(sale_type_rows, 9, sum(exist_so_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped(
                'amount_total_company')) + sum(
                new_so_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')),
                        sale_type_format)
            sale_type_rows += 1
            rows += 1
            for calc in sale.sales_sub_types:
                sales_sub_type_opf_sale_false = exist_so_opf.filtered(lambda x: x.sale_sub_type_id.id == calc.id)
                sales_sub_type_opf_sale_true = new_so_opf.filtered(lambda x: x.sale_sub_type_id.id == calc.id)
                sheet.write(rows, 7, sum(sales_sub_type_opf_sale_true.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 8, sum(sales_sub_type_opf_sale_false.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 9, sum(sales_sub_type_opf_sale_false.mapped('amount_total_company')) + sum(
                    sales_sub_type_opf_sale_true.mapped('amount_total_company')), bold_2)
                rows += 1

        # PURCHASE ORDER LOOP
        purchase_order_recs = self.env['purchase.order'].search([])
        exist_po_opf = purchase_order_recs.search(
            [('state', 'in', ['purchase', 'done']), ('date_approve', '>=', self.date_from),
             ('date_approve', '<=', self.date_to), ('partner_id.is_new', '=', False), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
        new_po_opf = purchase_order_recs.search(
            [('state', 'in', ['purchase', 'done']), ('date_approve', '>=', self.date_from),
             ('date_approve', '<=', self.date_to), ('partner_id.is_new', '=', True), ('sale_type_id', '!=', False), ('sales_sub_types', '!=', False)])
        sheet.write(rows, 7, sum(new_po_opf.mapped('amount_total_company')), parent_format)
        sheet.write(rows, 8, sum(exist_po_opf.mapped('amount_total_company')), parent_format)
        sheet.write(rows, 9,
                    sum(exist_po_opf.mapped('amount_total_company')) + sum(new_po_opf.mapped('amount_total_company')),
                    parent_format)
        rows += 1
        for sale in sale_type:
            sale_type_rows = rows
            sheet.write(sale_type_rows, 7, sum(exist_po_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')), sale_type_format)
            sheet.write(sale_type_rows, 8, sum(new_po_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')), sale_type_format)
            sheet.write(sale_type_rows, 9, sum(exist_po_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')) + sum(new_po_opf.mapped('amount_total_company')), sale_type_format)
            sale_type_rows += 1
            rows += 1

            for calc in sale.sales_sub_types:
                sales_sub_type_opf_purchase_false = exist_po_opf.filtered(lambda x: x.sales_sub_types.id == calc.id)
                sales_sub_type_opf_purchase_true = new_po_opf.filtered(lambda x: x.sales_sub_types.id == calc.id)
                sheet.write(rows, 7, sum(sales_sub_type_opf_purchase_true.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 8, sum(sales_sub_type_opf_purchase_false.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 9, sum(sales_sub_type_opf_purchase_false.mapped('amount_total_company')) + sum(
                    sales_sub_type_opf_purchase_true.mapped('amount_total_company')), bold_2)
                rows += 1

        # SO & PO - GROSS MARGIN LOOP
        sheet.write(rows, 7,
                    sum(new_so_opf.mapped('amount_total_company')) - sum(new_po_opf.mapped('amount_total_company')),
                    parent_format)
        sheet.write(rows, 8,
                    sum(exist_so_opf.mapped('amount_total_company')) - sum(exist_po_opf.mapped('amount_total_company')),
                    parent_format)
        sheet.write(rows, 9, (
                    sum(new_so_opf.mapped('amount_total_company')) - sum(new_po_opf.mapped('amount_total_company'))) + (
                                sum(exist_so_opf.mapped('amount_total_company')) - sum(
                            exist_po_opf.mapped('amount_total_company'))), parent_format)
        rows += 1
        for sale in sale_type:
            sale_type_rows = rows
            sheet.write(sale_type_rows, 7,
                        sum(new_so_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')) - sum(new_po_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')),
                        sale_type_format)
            sheet.write(sale_type_rows, 8, sum(exist_so_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')) - sum(
                exist_po_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')), sale_type_format)
            sheet.write(sale_type_rows, 9, (sum(new_so_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')) - sum(
                new_po_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company'))) + (sum(exist_so_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company')) - sum(
                exist_po_opf.filtered(lambda x: x.sale_type_id.id == sale.id).mapped('amount_total_company'))), sale_type_format)
            sale_type_rows += 1
            rows += 1

            for calc in sale.sales_sub_types:
                sales_sub_type_opf_sale_false = exist_so_opf.filtered(lambda x: x.sale_sub_type_id.id == calc.id)
                sales_sub_type_opf_sale_true = new_so_opf.filtered(lambda x: x.sale_sub_type_id.id == calc.id)
                sales_sub_type_opf_purchase_false = exist_po_opf.filtered(lambda x: x.sales_sub_types.id == calc.id)
                sales_sub_type_opf_purchase_true = new_po_opf.filtered(lambda x: x.sales_sub_types.id == calc.id)
                sheet.write(rows, 7, sum(sales_sub_type_opf_sale_true.mapped('amount_total_company')) - sum(
                    sales_sub_type_opf_purchase_true.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 8, sum(sales_sub_type_opf_sale_false.mapped('amount_total_company')) - sum(
                    sales_sub_type_opf_purchase_false.mapped('amount_total_company')), bold_2)
                sheet.write(rows, 9, (sum(sales_sub_type_opf_sale_true.mapped('amount_total_company')) - sum(
                    sales_sub_type_opf_purchase_true.mapped('amount_total_company'))) + (
                                        sum(sales_sub_type_opf_sale_false.mapped('amount_total_company')) - sum(
                                    sales_sub_type_opf_purchase_false.mapped('amount_total_company'))), bold_2)
                rows += 1

        workbook.close()
        fo = open(url + 'Daily Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodebytes(data)
        self.write({'report_details': out, 'report_details_name': 'Daily Report.xlsx'})
        return {
            'view_mode': 'form',
            'res_model': 'daily.report',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
