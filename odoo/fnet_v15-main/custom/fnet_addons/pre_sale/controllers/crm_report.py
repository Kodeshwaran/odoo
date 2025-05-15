import io
import xlsxwriter
from odoo import http, fields
from odoo.http import request

class CRMReportController(http.Controller):

    @http.route('/crm/daily_report/download', type='http', auth='user')
    def download_crm_daily_report(self, **kwargs):
        """Generate and return an Excel file for the daily CRM report."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Daily CRM Report')

        # Define styles
        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        normal = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'border': 1})

        # Define headers
        headers = [
            "Sl No", "Opportunity Created Date", "BDM", "Customer Name",
            "Opportunity", "Pre Sale Request Date", "Pre Sale Submit Date"
        ]

        # Write headers
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        # Fetch today's CRM leads
        leads = request.env['crm.lead'].sudo().search([('create_date', '>=', fields.Date.today())])

        row = 1
        for index, lead in enumerate(leads, start=1):
            sheet.write(row, 0, index, normal)  # Sl No
            sheet.write(row, 1, str(lead.create_date) if lead.create_date else '', normal)  # Created Date
            sheet.write(row, 2, lead.user_id.name or '', normal)  # BDM
            sheet.write(row, 3, lead.partner_id.name or '', normal)  # Customer Name
            sheet.write(row, 4, lead.name, normal)  # Opportunity
            sheet.write(row, 5, str(lead.pre_sale_request_date) if lead.pre_sale_request_date else '', normal)  # Request Date
            sheet.write(row, 6, str(lead.pre_sale_submit_date) if lead.pre_sale_submit_date else '', normal)  # Submit Date
            row += 1

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="CRM_Daily_Report.xlsx"')
            ]
        )
