from odoo import models, fields, api
import xlsxwriter
import base64


class SaleCostingWarning(models.TransientModel):
    _name = 'sale.costing.warning'

    requisition_id = fields.Many2one('purchase.requisition', string="Vendor Enquiry")

    def action_confirm(self):
        costing_id = self.env['sale.costing'].create({
            'opportunity_id': self.requisition_id.id,
            'partner_id': self.requisition_id.customer_id.id,
            'currency_id': self.requisition_id.currency_id.id,
        })
        for line in self.requisition_id.line_ids:
            self.env['sale.cost.line'].create({
                'costing_id': costing_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.price_unit,
            })
        action = self.env.ref('sale_costing.action_sale_costing').read()[0]
        action['domain'] = [('id', '=', costing_id.id)]
        return action


class SaleReportWizard(models.TransientModel):
    _name = 'sale.report.wizard'

    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)

    def action_sale_report(self):
        url = '/tmp/'
        report_name = "Sale Report"
        workbook = xlsxwriter.Workbook(url + report_name + '.xlsx')
        sheet = workbook.add_worksheet('Spent Data')
        format = workbook.add_format({'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter'})
        format_left = workbook.add_format({'font_name': 'Arial', 'align': 'left', 'valign': 'vcenter'})
        format1 = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'bg_color': '#BCBCBC', 'font_color': 'black', 'bottom': 2,
             'align': 'center', 'valign': 'vcenter'})
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:G', 15)
        sheet.set_column('H:J', 25)
        sheet.set_column('K:M', 15)
        sheet.set_row(0, 25)

        sheet.write('A1', 'S.No', format1)
        sheet.write('B1', 'Customer Enquiry', format1)
        sheet.write('C1', 'Quotation Number', format1)
        sheet.write('D1', 'Create Date', format1)
        sheet.write('E1', 'Delivery Date', format1)
        sheet.write('F1', 'Order Date', format1)
        sheet.write('G1', 'Expected Date', format1)
        sheet.write('H1', 'Customer', format1)
        sheet.write('I1', 'Sales Person', format1)
        sheet.write('J1', 'Company', format1)
        sheet.write('K1', 'Total', format1)
        sheet.write('L1', 'Amount\n(Local Currency)', format1)
        sheet.write('M1', 'Status', format1)

        n = 2
        s_no = 1

        if self.from_date and self.to_date:
            sale_orders = self.env['sale.order'].sudo().search([
                ('date_order', '>=', self.from_date),
                ('date_order', '<=', self.to_date)
            ])

            for order in sale_orders:
                currency_symbol = order.currency_id.symbol if order.currency_id.symbol else ""
                company_currency = order.company_currency_id.symbol if order.company_currency_id.symbol else ""

                sheet.write('A' + str(n), s_no, format)
                sheet.write('B' + str(n), order.enquiry_id.name if order.enquiry_id else "", format_left)
                sheet.write('C' + str(n), order.name if order.name else "", format)
                sheet.write('D' + str(n), order.create_date.strftime('%Y-%m-%d') if order.create_date else '', format)
                sheet.write('E' + str(n), order.commitment_date.strftime('%Y-%m-%d') if order.commitment_date else '', format)
                sheet.write('F' + str(n), order.date_order.strftime('%Y-%m-%d') if order.date_order else '', format)
                sheet.write('G' + str(n), order.expected_date.strftime('%Y-%m-%d') if order.expected_date else '', format)
                sheet.write('H' + str(n), order.partner_id.name if order.partner_id else "", format_left)
                sheet.write('I' + str(n), order.user_id.name if order.user_id else "", format)
                sheet.write('J' + str(n), order.company_id.name if order.company_id else "", format_left)
                sheet.write('K' + str(n), f"{currency_symbol} {order.amount_total:.2f}" if order.amount_total else "", format)
                sheet.write('L' + str(n), f"{company_currency} {order.base_currency_amount:.2f}" if order.base_currency_amount else "", format)
                sheet.write('M' + str(n), order.state.title() if order.state else "", format)

                n += 1
                s_no += 1

        workbook.close()

        with open(url + report_name + '.xlsx', "rb") as fo:
            values = {
                'name': report_name + '.xlsx',
                'res_model': 'ir.ui.view',
                'res_id': False,
                'type': 'binary',
                'public': True,
                'datas': base64.b64encode(fo.read()).decode('utf-8'),
            }
            attachment_id = self.env['ir.attachment'].sudo().create(values)
            download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "new",
            }