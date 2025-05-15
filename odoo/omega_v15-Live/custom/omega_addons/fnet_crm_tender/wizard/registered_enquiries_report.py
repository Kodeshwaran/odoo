from odoo import fields, models, _
import base64
import xlsxwriter

class RegisteredEnquiriesWizard(models.TransientModel):
    _name = 'registered.enquiries.wizard'
    _description = 'Registered Enquiries'

    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    user_id = fields.Many2one('res.users', "Purchase Representative", default=False)
    report_details = fields.Binary('Enquiries Registered', readonly=True)
    report_details_name = fields.Char('Filename', size=64, readonly=True)


    def action_print(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Registered Enquiries Report.xlsx')
        sheet = workbook.add_worksheet()
        title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF66', 'border': 1, 'right': 1})
        sub_title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#90ee90', 'border': 1, 'right': 1})
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center'})
        sheet.set_column('A:A', 32)
        sheet.set_column('B:B', 32)
        sheet.set_column('C:C', 32)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 10)
        sheet.set_column('K:K', 10)
        sheet.set_column('L:L', 10)
        sheet.set_column('M:M', 10)
        sheet.set_column('N:N', 10)
        sheet.set_column('O:O', 10)
        sheet.set_column('P:P', 10)
        sheet.set_column('Q:Q', 10)
        sheet.set_column('R:R', 10)
        sheet.set_column('S:S', 10)
        sheet.set_column('T:T', 10)
        sheet.set_column('U:U', 10)
        sheet.set_column('V:V', 10)
        sheet.set_column('W:W', 10)
        sheet.set_column('X:X', 10)
        sheet.set_column('Y:Y', 10)
        sheet.set_column('Z:Z', 10)
        sheet.set_column('AA:AA', 10)
        sheet.set_column('AB:AB', 10)
        sheet.set_column('AC:AC', 10)
        sheet.set_column('AD:AD', 10)
        sheet.set_column('AE:AE', 10)
        sheet.set_column('AF:AF', 10)
        sheet.set_column('AG:AG', 10)
        sheet.set_column('AH:AH', 10)
        sheet.set_column('AI:AI', 10)
        sheet.set_column('AJ:AJ', 10)
        sheet.set_column('AK:AK', 10)
        sheet.set_column('AL:AL', 10)
        sheet.set_column('AM:AM', 10)
        sheet.set_column('AN:AN', 10)
        sheet.set_column('AO:AO', 10)
        sheet.set_column('AP:AP', 10)
        sheet.set_column('AQ:AQ', 10)

        sheet.merge_range('A1:A2', 'Enquiry Reference', title_format)
        sheet.merge_range('B1:B2', 'Salesperson', title_format)
        sheet.merge_range('C1:C2', 'Quotation Number(Approved)', title_format)

        domain = list()
        if self.date_from and self.date_to:
            domain.append(('create_date', '>=', self.date_from))
            domain.append(('create_date', '<=', self.date_to))
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        opportunities = self.env['crm.lead'].search(domain)
        row = 2
        col = 0
        if opportunities:
            for lead in opportunities:
                sp_col = col + 1
                sheet.write(row, col, lead.opportunity_name if lead.opportunity_name else lead.name, format1)
                sheet.write(row, sp_col, lead.user_id.name, format1)
                sale_quotes = self.env['sale.order'].search([('enquiry_id', '=', lead.id), ('approval_state', '=', 'approved')])
                quote_col = sp_col + 1
                for sale in sale_quotes:
                    sheet.write(row, quote_col, sale.quotation_name if sale.state not in ['sale', 'done'] else sale.name, format1)
                row += 1
        workbook.close()
        fo = open(url + 'Registered Enquiries Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'report_details': out, 'report_details_name': 'Registered Enquiries Report.xlsx'})
        return {
            'view_mode': 'form',
            'res_model': 'registered.enquiries.wizard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }