from odoo import api, fields, models, _
import xlsxwriter
import base64
from datetime import time, datetime


class POExpectedDelivery(models.TransientModel):
    _name = 'po.expected.delivery'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')
    filedata = fields.Binary('Download file', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)
    is_downloaded = fields.Boolean()
    incoming_picking_count = fields.Integer(related="")

    def get_po_expected_delivery(self):
        date_from = datetime.combine(fields.Date.from_string(self.date_from), time.min)
        date_to = datetime.combine(fields.Date.from_string(self.date_to), time.max)
        fo = self.print_xlsx_po_expected_delivery_report(date_from, date_to)
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'filedata': out, 'filename': 'Delivery Report', 'is_downloaded': True})
        return {
            'name': 'Delivery Report',
            'res_model': 'po.expected.delivery',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'nodestroy': True,
            'res_id': self.id,
        }

    def print_xlsx_po_expected_delivery_report(self, from_date, to_date):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Delivery Report.xlsx')
        worksheet = workbook.add_worksheet(name="Delivery Report")
        # worksheet2 = workbook.add_worksheet(name="Pending PO")
        report_head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#ADD8E6',
            'font_size': 18, })
        sub_heading_format = workbook.add_format({
            'border': 1,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#62BD69',
            'font_size': 13, })
        data_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 13, })
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:M', 20)

        worksheet.merge_range("A1:D2", 'Delivery Report', report_head_format)
        worksheet.write("A3:A3", 'SO.No', sub_heading_format)
        worksheet.write("B3:B3", 'Customer', sub_heading_format)
        worksheet.write("C3:C3", 'SO Date', sub_heading_format)
        worksheet.write("D3:D3", 'Expected Delivery', sub_heading_format)
        worksheet.write("E3:E3", 'PO.No', sub_heading_format)
        worksheet.write("F3:F3", 'Vendor', sub_heading_format)
        worksheet.write("G3:G3", 'PO Date', sub_heading_format)
        # worksheet.write("H3:H3", 'Expected Receipt', sub_heading_format)
        # worksheet.write("I3:I3", 'Actual Receipt', sub_heading_format)
        worksheet.write("H3:H3", 'Invoice Date', sub_heading_format)


        sale_rows = 3
        sale_ids = self.env['sale.order'].search([('commitment_date', '>=', from_date), ('commitment_date', '<=', to_date)])
        for sale in sale_ids:
            deliverable_lines = sale.order_line.filtered(lambda x: x.product_id.detailed_type == 'product')
            purchase = self.env['purchase.order'].search([('sale_id', '=', sale.id)], limit=1)
            if deliverable_lines and purchase:
                invoice_date = sale.invoice_ids[0].invoice_date.strftime('%d/%m/%Y') if sale.invoice_ids else ''
                worksheet.write(sale_rows, 0, sale.name, data_format)
                worksheet.write(sale_rows, 1, sale.partner_id.name, data_format)
                worksheet.write(sale_rows, 2, sale.date_order.strftime('%d/%m/%Y') if sale.date_order else '', data_format)
                worksheet.write(sale_rows, 3, sale.commitment_date.strftime('%d/%m/%Y') if sale.commitment_date else '', data_format)
                worksheet.write(sale_rows, 4, purchase.name, data_format)
                worksheet.write(sale_rows, 5, purchase.partner_id.name, data_format)
                worksheet.write(sale_rows, 6, purchase.date_approve.strftime('%d/%m/%Y') if purchase.date_approve else '', data_format)
                # worksheet.write(sale_rows, 7, purchase.date_planned.strftime('%d/%m/%Y') if purchase.date_planned else '', data_format)
                # worksheet.write(sale_rows, 8, purchase.effective_date.strftime('%d/%m/%Y') if purchase.effective_date else '', data_format)
                worksheet.write(sale_rows, 7, invoice_date, data_format)
                sale_rows += 1

        # purchase_rows = 3
        # purchase_ids = self.env['purchase.order'].search([('date_approve', '>=', from_date), ('date_approve', '<=', to_date)])
        # for purchase in purchase_ids:
        #     worksheet.write(purchase_rows, 4, purchase.name, data_format)
        #     worksheet.write(purchase_rows, 5, purchase.partner_id.name, data_format)
        #     worksheet.write(purchase_rows, 6, purchase.date_approve.strftime('%d/%m/%Y'), data_format)
        #     worksheet.write(purchase_rows, 7, purchase.date_planned.strftime('%d/%m/%Y'), data_format)
        #     purchase_rows += 1


        # worksheet2
        # worksheet2.set_column('A:A', 25)
        # worksheet2.set_column('B:B', 30)
        #
        # worksheet2.merge_range("A1:B2", 'PO Expected Delivery Report', report_head_format)
        # worksheet2.write("A3:A3", 'PO.No', sub_heading_format)
        # worksheet2.write("B3:B3", 'Expected Delivery', sub_heading_format)
        #
        # po_rows = 3
        # po_ids = self.env['purchase.order'].search([('date_approve', '>=', from_date), ('date_approve', '<=', to_date)]).filtered(lambda x: x.incoming_picking_count > 0 and x.state in ['purchase', 'done'])
        # for po in po_ids:
        #     worksheet2.write(po_rows, 0, po.name, data_format)
        #     worksheet2.write(po_rows, 1, po.date_planned.strftime('%d/%m/%Y'), data_format)
        #     po_rows += 1
        workbook.close()
        fo2 = open(url + 'Delivery Report.xlsx', "rb+")
        return fo2
