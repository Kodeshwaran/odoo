from odoo import models, fields, api, _
import xlsxwriter
import base64


class EmployeeReportWizard(models.TransientModel):
    _name = 'employee.report.wizard'

    department_ids = fields.Many2many('hr.department', string="Departments")
    file = fields.Binary("File")
    filename = fields.Binary("File Name")

    def print_xlsx(self):
        url = '/tmp/'
        report_name = 'Employee Details'
        workbook = xlsxwriter.Workbook(url + report_name + '.xlsx')
        worksheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 11, 'bold':1, 'valign': 'vcenter', 'align': 'center', 'font_name': 'Liberation Serif', 'fg_color': 'grey'})
        format2 = workbook.add_format({'font_size': 10, 'font_name': 'Liberation Serif'})
        worksheet.set_column('A:K', 20)
        # worksheet.merge_range('G1:H1', 'Report Date', format0)
        worksheet.write('A1', "Employee ID", format1)
        worksheet.write('B1', "Employee Name", format1)
        worksheet.write('C1', "Educational Background", format1)
        worksheet.write('D1', "Educational Qualification", format1)
        worksheet.write('E1', "Overal Expreience", format1)
        worksheet.write('F1', "Our company Expreience(Years)", format1)
        worksheet.write('G1', "Designation", format1)
        worksheet.write('H1', "Department", format1)
        worksheet.write('I1', "Certification", format1)
        worksheet.write('J1', "skills", format1)
        worksheet.write('K1', "CTC", format1)
        domain = []
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        employee_ids = self.env['hr.employee'].search(domain, order='employeeid')
        row = 2
        for employee in employee_ids:
            cotract_id = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
            worksheet.write('A' + str(row), employee.employeeid, format2)
            worksheet.write('B' + str(row), employee.name, format2)
            worksheet.write('C' + str(row), dict(employee._fields['certificate'].selection).get(employee.certificate) or '', format2)
            worksheet.write('D' + str(row), employee.study_field or '', format2)
            worksheet.write('E' + str(row), "%.2f" % (employee.experience_previous_company+(employee.experience_current_company / 12)), format2)
            worksheet.write('F' + str(row), "%.2f" % (employee.experience_current_company / 12), format2)
            worksheet.write('G' + str(row), employee.job_id.name or '', format2)
            worksheet.write('H' + str(row), employee.department_id.name or '', format2)
            worksheet.write('I' + str(row), 'Not Available', format2)
            worksheet.write('J' + str(row), 'Not Available', format2)
            worksheet.write('K' + str(row), cotract_id.wage or '', format2)
            row += 1
        workbook.close()
        fo = open(url + report_name + '.xlsx', "rb+")
        values = {
            'name': 'EPO_Details.xlsx',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'datas': base64.encodestring(fo.read()),
        }
        attachment_id = self.env['ir.attachment'].sudo().create(values)
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }
        # fo = open(url + report_name + '.xlsx', "rb+")
        # data = fo.read()
        # out = base64.encodestring(data)
        # self.write({'file': out, 'filename': report_name + '.xlsx'})
        #
        # view_ref = self.env['ir.model.data']._xmlid_to_res_model_res_id('hr_payroll_extended.employee_details_report_form')
        # view_id = view_ref and view_ref[1] or False,
        # print("\n---", view_id, "--view_id--\n")
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': _('Employee Report'),
        #     'res_model': 'employee.report.wizard',
        #     'res_id': self.id,
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'view_id': view_id,
        #     'target': 'current',
        #     'nodestroy': True,
        # }

