from odoo import fields, models, _
import base64
import xlsxwriter

class ApprovalStatusWizard(models.TransientModel):
    _name = 'approval.status.wizard'
    _description = 'Approval Status Report'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    user_id = fields.Many2one('res.users', "Salesperson", default=False)
    report_details = fields.Binary('Approval Status', readonly=True)
    report_details_name = fields.Char('Filename', size=64, readonly=True)

    def action_print(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Approval Status Report.xlsx')
        sheet = workbook.add_worksheet()
        # title_format = workbook.add_format(
        #     {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF66', 'border': 1, 'right': 1})
        sub_title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#90ee90', 'border': 1, 'right': 1})
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center'})
        sheet.set_column('A:A', 32)
        sheet.set_column('B:B', 32)
        sheet.set_column('C:C', 32)
        sheet.set_column('D:D', 32)
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

        sheet.merge_range('A1:A2', 'Salesperson', sub_title_format)
        sheet.merge_range('B1:B2', 'Sale Reference', sub_title_format)
        sheet.merge_range('C1:C2', 'Approval Status', sub_title_format)
        sheet.merge_range('D1:D2', 'Next Approver', sub_title_format)

        domain = list()
        if self.date_from and self.date_to:
            domain.append(('create_date', '>=', self.date_from))
            domain.append(('create_date', '<=', self.date_to))
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        sale_quotes = self.env['sale.order'].search(domain)

        row = 2
        col = 0
        if sale_quotes:
            for sale in sale_quotes:
                selection_label = dict(sale._fields['approval_state'].selection).get(sale.approval_state)
                sheet.write(row, col, sale.user_id.name, format1)
                sheet.write(row, col + 1, sale.quotation_name if sale.state not in ['sale', 'done'] else sale.name,format1)
                sheet.write(row, col + 2, selection_label, format1)
                for approval in sale.sale_order_approval_rule_ids:
                    for user in approval.users:
                        sheet.write(row, col + 3, str(approval.approval_role.name) + ": " + user.name if selection_label != 'Approved' else '', format1)
                row += 1


        workbook.close()
        fo = open(url + 'Approval Status Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'report_details': out, 'report_details_name': 'Approval Status Report.xlsx'})
        return {
            'view_mode': 'form',
            'res_model': 'approval.status.wizard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }