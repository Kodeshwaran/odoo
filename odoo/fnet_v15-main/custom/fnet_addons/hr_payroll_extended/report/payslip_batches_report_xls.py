from odoo import models, api, fields, _
from datetime import datetime
from dateutil import relativedelta
import xlsxwriter
import tempfile
import decimal
import base64
import string
import logging
import operator
from num2words import num2words
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    amount_text = fields.Char(compute="amount_in_words")
    employee_categ = fields.Selection([('employee', 'Employee'), ('intern', 'Internship'), ('consultant', 'Consultant')], string="Employee Type", related="employee_id.employee_categ", store=True)

    def amount_in_words(self):
        for rec in self:
            rec.amount_text = str(self.env.user.company_id.currency_id.amount_to_text(
                self.line_ids.filtered(lambda x: x.code == 'NET').total))

    def get_amount_in_words(self):
        return self.env.user.company_id.currency_id.amount_to_text(self.line_ids.filtered(lambda x: x.code == 'NET').total)

    def calculate_deductions(self):
        total_deductions = sum(self.line_ids.filtered(lambda x: x.category_id.code == 'DED').mapped('total'))
        return total_deductions

    def payslip_mail(self):
        for payslip in self:
            pdf = self.env.ref('hr_payroll_extended.payslip_report')._render_qweb_pdf(payslip.ids)
            att = self.env['ir.attachment'].create({
                'name': payslip.name + ".pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf[0]),
                'res_model': 'hr.payslip',
                'res_id': payslip.id,
                'mimetype': 'application/x-pdf'
            })
            try:
                email_to = payslip.employee_id.work_email
                email_from = self.env.user.company_id.payslip_mail
                subject = "Employee Payslip"
                body = _("Hi,<br/>")
                body += _("<br/> %s is been attached,Kindly find the Attachment." % payslip.name)
                footer = "With Regards,<br/>HR<br/>"
                mail = {
                    'email_to': email_to,
                    'email_from': email_from,
                    'model': 'hr.payslip',
                    'res_id': payslip.id,
                    'record_name': 'Employee Payslip',
                    'subject': subject,
                    'attachment_ids': [(6, 0, [att.id])],
                    'body_html': '''<span  style="font-size:14px"><br/>
                  <br/>%s<br/>
                  <br/>%s</span>''' % (body, footer),
                }
                self.env['mail.mail'].sudo().create(mail).send()
            except Exception as E:
                print("Exception", E)
        # ~ raise UserError(_("Employee Payslip Mail Has Been Send Successfully!!!"))
        return True


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    filedata = fields.Binary('Excel Report', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)
    get_department_total = fields.Binary('Department Report', readonly=True)
    get_department_total_name = fields.Char('Filename', size=64, readonly=True)
    data_esi = fields.Binary('Download file ESI', readonly=True)
    esi_name = fields.Char('Filename', size=64, readonly=True)
    data_live_pf = fields.Binary('Download file PF', readonly=True)
    data_pf = fields.Char('Filename', size=64, readonly=True)

    def sent_status_mail(self, data):
        pay_val = self.env['hr.payslip'].search([('payslip_run_id', '=', data.id)])
        print("---", pay_val, "--pay_val-\n")
        success_val = []
        for i in pay_val:
            mail_val = self.env['mail.mail'].search([('model', '=', 'hr.payslip'), ('res_id', '=', i.id)] , limit=1)
            if mail_val.state == 'sent':
                success_val.append({
                    's_emp': i.employee_id.name,
                    'u_emp': None,
                })
            elif mail_val.state != 'sent':
                success_val.append({
                    's_emp': None,
                    'u_emp': i.employee_id.name,
                })
        return success_val

    def close_payslip_run(self):
        self.write({'state': 'done'})
        res = super(HrPayslipRun, self).close_payslip_run()
        for payslip in self.slip_ids:
            payslip.action_payslip_done()
        return res

    def payslip_mail(self):
        payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', self.id), ('employee_categ', '=', 'employee')])
        for payslip in payslips:
            pdf = self.env.ref('hr_payroll_extended.payslip_report')._render_qweb_pdf(payslip.ids)
            if not self.env.user.company_id.payslip_mail:
                raise ValidationError("Please configure Email(From) in settings menu, under 'Mail Configuration'.")
            att = self.env['ir.attachment'].create({
                'name': payslip.name + ".pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf[0]),
                'res_model': 'hr.payslip',
                'res_id': payslip.id,
                'mimetype': 'application/x-pdf'
            })
            try:
                email_to = payslip.employee_id.work_email
                email_from = self.env.user.company_id.payslip_mail
                subject = "Employee Payslip"
                body = _("Hi,<br/>")
                body += _("<br/> %s is been attached,Kindly find the Attachment." % payslip.name)
                footer = "With Regards,<br/>HR<br/>"
                mail = {
                    'email_to': email_to,
                    'email_from': email_from,
                    'model': 'hr.payslip',
                    'res_id': payslip.id,
                    'record_name': 'Employee Payslip',
                    'subject': subject,
                    'attachment_ids': [(6, 0, [att.id])],
                    'body_html': '''<span  style="font-size:14px"><br/>
                <br/>%s<br/>
                <br/>%s</span>''' % (body, footer),
                }
                self.env['mail.mail'].sudo().create(mail).send()
            except Exception as E:
                print("Exception", E)
        # ~ raise UserError(_("Employee Payslip Mail Has Been Send Successfully!!!"))
        return True

    def generate_dept_report(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Department Total Report.xlsx')
        sheet = workbook.add_worksheet()
        # departments =  self.slip_ids.read_group(domain=[], fields=['employee_id.department_id.parent_id.name'], groupby =[])
        # departments =  self.env['hr.department'].read_group(domain=[], fields=['parent_id'], groupby =['parent_id'])
        # print("dddddddddddddddddddddddddddddddddddddd", departments)
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center'})
        parent_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#ADD8E6'})
        child_format = workbook.add_format({'font_size': 11, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#90EE90'})
        total_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#FFCCCB'})
        format1.set_text_wrap()
        format2 = workbook.add_format({'font_size': 12, 'align': 'center'})
        format3 = workbook.add_format({'font_size': 12, 'align': 'left', 'num_format': 'dd-mm-yyyy'})

        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        bold_1 = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        sheet.set_row(6, 40)
        sheet.set_row(7, 30)
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
        sheet.merge_range('B3:E3', 'DEPARTMENT TOTAL REPORT', bold)
        sheet.write(5, 1, 'BASIC', bold)
        sheet.write(5, 2, 'Bonus', bold)
        sheet.write(5, 3, 'HRA', bold)
        sheet.write(5, 4, 'Conveyance Allowance', bold)
        sheet.write(5, 5, 'Other Allowance', bold)
        sheet.write(5, 6, 'Travel Allowance', bold)
        sheet.write(5, 7, 'Medical Allowance', bold)
        sheet.write(5, 8, 'Earnings Allowance', bold)
        sheet.write(5, 9, 'Data Card Allowance', bold)
        sheet.write(5, 10, 'Overtime Allowance', bold)
        sheet.write(5, 11, 'Arrears', bold)
        sheet.write(5, 12, 'Arrear', bold)
        sheet.write(5, 13, 'Consolidate Pay', bold)
        sheet.write(5, 14, 'Gross', bold)
        sheet.write(5, 15, 'Employee PF', bold)
        sheet.write(5, 16, 'Employer PF', bold)
        sheet.write(5, 17, 'Employee ESI', bold)
        sheet.write(5, 18, 'Employer ESI', bold)
        sheet.write(5, 19, 'Gratuity', bold)
        sheet.write(5, 20, 'Non-Cash Component', bold)
        sheet.write(5, 21, 'Mobile Deduction', bold)
        sheet.write(5, 22, 'Advance Salary', bold)
        sheet.write(5, 23, 'TDS', bold)
        sheet.write(5, 24, 'Other Deduction', bold)
        sheet.write(5, 25, 'PT', bold)
        sheet.write(5, 26, 'Total Deduction', bold)
        sheet.write(5, 27, 'Net', bold)
        sheet.write(5, 28, 'Actual CTC', bold)
        departments = self.slip_ids.mapped('employee_id').mapped('department_id')
        parent_departments = departments.mapped('parent_id')
        other_deps = departments.filtered(lambda x: not x.parent_id and x.id not in parent_departments.ids)
        parent_departments += other_deps
        rows = 6
        for parent in parent_departments:
            payslips = self.slip_ids.filtered(lambda x: x.employee_id.department_id.id == parent.id)
            parent_row = rows
            sheet.write(rows, 0, parent.name, parent_format)
            rows += 1
            basic_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'BASIC').mapped('total'))
            bonus_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'BONUS').mapped('total'))
            hra_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'HRA').mapped('total'))
            conv_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'CONV').mapped('total'))
            other_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'OTHER').mapped('total'))
            travel_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'Travel').mapped('total'))
            medical_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'Medical').mapped('total'))
            earn_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'EA').mapped('total'))
            data_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'CARD').mapped('total'))
            overtime_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'NOT').mapped('total'))
            arrears_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'ARREARS').mapped('total'))
            arrear_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'ARREAR').mapped('total'))
            cons_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'CON').mapped('total'))
            gross_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'GROSS').mapped('total'))
            emppf_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'EEPF').mapped('total'))
            emplpf_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'EPF').mapped('total'))
            empesi_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'ESI').mapped('total'))
            emplesi_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'ESI2').mapped('total'))
            gratuity_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'GR').mapped('total'))
            ncc_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'NCC').mapped('total'))
            mob_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'MD').mapped('total'))
            adv_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'AS').mapped('total'))
            tds_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'TDS').mapped('total'))
            othded_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'OD').mapped('total'))
            pt_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'PT').mapped('total'))
            totded_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.category_id.code == 'DED').mapped('total'))
            net_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code == 'NET').mapped('total'))
            ctc_over_total = sum(payslips.mapped('line_ids').filtered(lambda x: x.code in ['GROSS', 'EPF', 'ESI2', 'GR', 'NCC']).mapped('total'))
            for slip in payslips:
                sheet.write(rows, 0, slip.employee_id.name, bold_1)
                sheet.write(rows, 1, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'BASIC').mapped('total')), bold_1)
                sheet.write(rows, 2, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'BONUS').mapped('total')),bold_1)
                sheet.write(rows, 3, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'HRA').mapped('total')),bold_1)
                sheet.write(rows, 4, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'CONV').mapped('total')),bold_1)
                sheet.write(rows, 5, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'OTHER').mapped('total')),bold_1)
                sheet.write(rows, 6, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'Travel').mapped('total')),bold_1)
                sheet.write(rows, 7, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'Medical').mapped('total')),bold_1)
                sheet.write(rows, 8, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'EA').mapped('total')),bold_1)
                sheet.write(rows, 9, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'CARD').mapped('total')),bold_1)
                sheet.write(rows, 10, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'NOT').mapped('total')),bold_1)
                sheet.write(rows, 11, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'ARREARS').mapped('total')),bold_1)
                sheet.write(rows, 12, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'ARREAR').mapped('total')),bold_1)
                sheet.write(rows, 13, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'CON').mapped('total')),bold_1)
                sheet.write(rows, 14, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'GROSS').mapped('total')),bold_1)
                sheet.write(rows, 15, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'EEPF').mapped('total')),bold_1)
                sheet.write(rows, 16, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'EPF').mapped('total')),bold_1)
                sheet.write(rows, 17, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'ESI').mapped('total')),bold_1)
                sheet.write(rows, 18, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'ESI2').mapped('total')),bold_1)
                sheet.write(rows, 19, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'GR').mapped('total')),bold_1)
                sheet.write(rows, 20, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'NCC').mapped('total')),bold_1)
                sheet.write(rows, 21, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'MD').mapped('total')),bold_1)
                sheet.write(rows, 22, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'AS').mapped('total')),bold_1)
                sheet.write(rows, 23, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'TDS').mapped('total')),bold_1)
                sheet.write(rows, 24, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'OD').mapped('total')),bold_1)
                sheet.write(rows, 25, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'PT').mapped('total')),bold_1)
                sheet.write(rows, 26, sum(slip.mapped('line_ids').filtered(lambda x: x.category_id.code == 'DED').mapped('total')),bold_1)
                sheet.write(rows, 27, sum(slip.mapped('line_ids').filtered(lambda x: x.code == 'NET').mapped('total')),bold_1)
                sheet.write(rows, 28, sum(slip.mapped('line_ids').filtered(lambda x: x.code in ['GROSS', 'EPF', 'ESI2', 'GR', 'NCC']).mapped('total')),bold_1)
                rows += 1
            childs = self.slip_ids.mapped('employee_id').mapped('department_id').filtered(lambda x: x.parent_id.id == parent.id)
            child_row = rows
            for child in childs:
                child_payslips = self.slip_ids.filtered(lambda x: x.employee_id.department_id.id == child.id)
                if child_payslips:
                    sheet.write(rows, 0, child.name, child_format)
                    child_row = rows
                    rows += 1
                for child_slip in child_payslips:
                    sheet.write(rows, 0, child_slip.employee_id.name, bold_1)
                    sheet.write(rows, 1, sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'BASIC').mapped('total')),bold_1)
                    sheet.write(rows, 2,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'BONUS').mapped('total')),bold_1)
                    sheet.write(rows, 3,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'HRA').mapped('total')),bold_1)
                    sheet.write(rows, 4,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'CONV').mapped('total')),bold_1)
                    sheet.write(rows, 5,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'OTHER').mapped('total')),bold_1)
                    sheet.write(rows, 6,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'Travel').mapped('total')),bold_1)
                    sheet.write(rows, 7,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'Medical').mapped('total')),bold_1)
                    sheet.write(rows, 8,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'EA').mapped('total')),bold_1)
                    sheet.write(rows, 9,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'CARD').mapped('total')),bold_1)
                    sheet.write(rows, 10,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'NOT').mapped('total')),bold_1)
                    sheet.write(rows, 11,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'ARREARS').mapped('total')),bold_1)
                    sheet.write(rows, 12,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'ARREAR').mapped('total')),bold_1)
                    sheet.write(rows, 13,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'CON').mapped('total')),bold_1)
                    sheet.write(rows, 14,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'GROSS').mapped('total')),bold_1)
                    sheet.write(rows, 15,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'EEPF').mapped('total')),bold_1)
                    sheet.write(rows, 16,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'EPF').mapped('total')),bold_1)
                    sheet.write(rows, 17,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'ESI').mapped('total')),bold_1)
                    sheet.write(rows, 18,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'ESI2').mapped('total')),bold_1)
                    sheet.write(rows, 19,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'GR').mapped('total')),bold_1)
                    sheet.write(rows, 20,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'NCC').mapped('total')),bold_1)
                    sheet.write(rows, 21,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'MD').mapped('total')),bold_1)
                    sheet.write(rows, 22,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'AS').mapped('total')),bold_1)
                    sheet.write(rows, 23,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'TDS').mapped('total')),bold_1)
                    sheet.write(rows, 24,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'OD').mapped('total')),bold_1)
                    sheet.write(rows, 25,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'PT').mapped('total')),bold_1)
                    sheet.write(rows, 26,sum(child_slip.mapped('line_ids').filtered(lambda x: x.category_id.code == 'DED').mapped('total')),bold_1)
                    sheet.write(rows, 27,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code == 'NET').mapped('total')),bold_1)
                    sheet.write(rows, 28,sum(child_slip.mapped('line_ids').filtered(lambda x: x.code in ['GROSS', 'EPF', 'ESI2', 'GR', 'NCC']).mapped('total')),bold_1)
                    rows += 1
                sheet.write(child_row, 1,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'BASIC').mapped('total')),child_format)
                sheet.write(child_row, 2,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'BONUS').mapped('total')),child_format)
                sheet.write(child_row, 3,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'HRA').mapped('total')),child_format)
                sheet.write(child_row, 4,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'CONV').mapped('total')),child_format)
                sheet.write(child_row, 5,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'OTHER').mapped('total')),child_format)
                sheet.write(child_row, 6,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'Travel').mapped('total')),child_format)
                sheet.write(child_row, 7,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'Medical').mapped('total')),child_format)
                sheet.write(child_row, 8,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'EA').mapped('total')),child_format)
                sheet.write(child_row, 9,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'CARD').mapped('total')),child_format)
                sheet.write(child_row, 10,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'NOT').mapped('total')),child_format)
                sheet.write(child_row, 11,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'ARREARS').mapped('total')),child_format)
                sheet.write(child_row, 12,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'ARREAR').mapped('total')),child_format)
                sheet.write(child_row, 13,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'CON').mapped('total')),child_format)
                sheet.write(child_row, 14,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'GROSS').mapped('total')),child_format)
                sheet.write(child_row, 15,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'EEPF').mapped('total')),child_format)
                sheet.write(child_row, 16,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'EPF').mapped('total')),child_format)
                sheet.write(child_row, 17,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'ESI').mapped('total')),child_format)
                sheet.write(child_row, 18,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'ESI2').mapped('total')),child_format)
                sheet.write(child_row, 19,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'GR').mapped('total')), child_format)
                sheet.write(child_row, 20,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'NCC').mapped('total')), child_format)
                sheet.write(child_row, 21,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'MD').mapped('total')),child_format)
                sheet.write(child_row, 22,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'AS').mapped('total')),child_format)
                sheet.write(child_row, 23,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'TDS').mapped('total')),child_format)
                sheet.write(child_row, 24,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'OD').mapped('total')),child_format)
                sheet.write(child_row, 25,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'PT').mapped('total')),child_format)
                sheet.write(child_row, 26,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.category_id.code == 'DED').mapped('total')), child_format)
                sheet.write(child_row, 27,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'NET').mapped('total')),child_format)
                sheet.write(child_row, 28,sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code in ['GROSS', 'EPF', 'ESI2', 'GR', 'NCC']).mapped('total')),child_format)
                basic_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'BASIC').mapped('total'))
                bonus_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'BONUS').mapped('total'))
                hra_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'HRA').mapped('total'))
                conv_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'CONV').mapped('total'))
                other_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'OTHER').mapped('total'))
                travel_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'Travel').mapped('total'))
                medical_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'Medical').mapped('total'))
                earn_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'EA').mapped('total'))
                data_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'CARD').mapped('total'))
                overtime_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'NOT').mapped('total'))
                arrears_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'ARREARS').mapped('total'))
                arrear_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'ARREAR').mapped('total'))
                cons_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'CON').mapped('total'))
                gross_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'GROSS').mapped('total'))
                emppf_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'EEPF').mapped('total'))
                emplpf_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'EPF').mapped('total'))
                empesi_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'ESI').mapped('total'))
                emplesi_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'ESI2').mapped('total'))
                gratuity_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'GR').mapped('total'))
                ncc_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'NCC').mapped('total'))
                mob_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'MD').mapped('total'))
                adv_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'AS').mapped('total'))
                tds_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'TDS').mapped('total'))
                othded_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'OD').mapped('total'))
                pt_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'PT').mapped('total'))
                totded_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.category_id.code == 'DED').mapped('total'))
                net_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code == 'NET').mapped('total'))
                ctc_over_total += sum(child_payslips.mapped('line_ids').filtered(lambda x: x.code in ['GROSS', 'EPF', 'ESI2', 'GR']).mapped('total'))

            sheet.write(parent_row, 1, basic_over_total, parent_format)
            sheet.write(parent_row, 2, bonus_over_total, parent_format)
            sheet.write(parent_row, 3, hra_over_total, parent_format)
            sheet.write(parent_row, 4, conv_over_total, parent_format)
            sheet.write(parent_row, 5, other_over_total, parent_format)
            sheet.write(parent_row, 6, travel_over_total, parent_format)
            sheet.write(parent_row, 7, medical_over_total, parent_format)
            sheet.write(parent_row, 8, earn_over_total, parent_format)
            sheet.write(parent_row, 9, data_over_total, parent_format)
            sheet.write(parent_row, 10, overtime_over_total, parent_format)
            sheet.write(parent_row, 11, arrears_over_total, parent_format)
            sheet.write(parent_row, 12, arrear_over_total, parent_format)
            sheet.write(parent_row, 13, cons_over_total, parent_format)
            sheet.write(parent_row, 14, gross_over_total, parent_format)
            sheet.write(parent_row, 15, emppf_over_total, parent_format)
            sheet.write(parent_row, 16, emplpf_over_total, parent_format)
            sheet.write(parent_row, 17, empesi_over_total, parent_format)
            sheet.write(parent_row, 18, emplesi_over_total, parent_format)
            sheet.write(parent_row, 19, gratuity_over_total, parent_format)
            sheet.write(parent_row, 20, ncc_over_total, parent_format)
            sheet.write(parent_row, 21, mob_over_total, parent_format)
            sheet.write(parent_row, 22, adv_over_total, parent_format)
            sheet.write(parent_row, 23, tds_over_total, parent_format)
            sheet.write(parent_row, 24, othded_over_total, parent_format)
            sheet.write(parent_row, 25, pt_over_total, parent_format)
            sheet.write(parent_row, 26, totded_over_total, parent_format)
            sheet.write(parent_row, 27, net_over_total, parent_format)
            sheet.write(parent_row, 28, ctc_over_total, parent_format)
        rows += 1
        sheet.write(rows, 0, 'SUB TOTAL', total_format)
        sheet.write(rows, 1,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'BASIC').mapped('total')),total_format)
        sheet.write(rows, 2,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'BONUS').mapped('total')),total_format)
        sheet.write(rows, 3,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'HRA').mapped('total')),total_format)
        sheet.write(rows, 4,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'CONV').mapped('total')),total_format)
        sheet.write(rows, 5,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'OTHER').mapped('total')),total_format)
        sheet.write(rows, 6,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'Travel').mapped('total')),total_format)
        sheet.write(rows, 7,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'Medical').mapped('total')),total_format)
        sheet.write(rows, 8,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'EA').mapped('total')),total_format)
        sheet.write(rows, 9,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'CARD').mapped('total')),total_format)
        sheet.write(rows, 10,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'NOT').mapped('total')),total_format)
        sheet.write(rows, 11,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'ARREARS').mapped('total')),total_format)
        sheet.write(rows, 12,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'ARREAR').mapped('total')),total_format)
        sheet.write(rows, 13,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'CON').mapped('total')),total_format)
        sheet.write(rows, 14,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'GROSS').mapped('total')),total_format)
        sheet.write(rows, 15,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'EEPF').mapped('total')),total_format)
        sheet.write(rows, 16,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'EPF').mapped('total')),total_format)
        sheet.write(rows, 17,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'ESI').mapped('total')),total_format)
        sheet.write(rows, 18,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'ESI2').mapped('total')),total_format)
        sheet.write(rows, 19,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'GR').mapped('total')),total_format)
        sheet.write(rows, 20,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'NCC').mapped('total')),total_format)
        sheet.write(rows, 21,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'MD').mapped('total')),total_format)
        sheet.write(rows, 22,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'AS').mapped('total')),total_format)
        sheet.write(rows, 23,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'TDS').mapped('total')),total_format)
        sheet.write(rows, 24,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'OD').mapped('total')),total_format)
        sheet.write(rows, 25,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'PT').mapped('total')),total_format)
        sheet.write(rows, 26,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.category_id.code == 'DED').mapped('total')), total_format)
        sheet.write(rows, 27,sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'NET').mapped('total')),total_format)
        sheet.write(rows, 28, sum(self.slip_ids.mapped('line_ids').filtered(lambda x: x.code in ['GROSS', 'EPF', 'ESI2', 'GR', 'NCC']).mapped('total')),total_format)
        workbook.close()
        fo = open(url + 'Department Total Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'get_department_total': out, 'get_department_total_name': 'Department Total Report.xlsx'})

    def generate_xls_report(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Payslip Batches Report.xlsx')
        sheet = workbook.add_worksheet()
        payslips = self.env['hr.payslip'].search([('id', 'in', self.slip_ids.ids)])
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'valign': 'center', 'bold': True})
        format1.set_text_wrap()
        format2 = workbook.add_format({'font_size': 12, 'align': 'center'})
        format3 = workbook.add_format({'font_size': 12, 'align': 'left', 'num_format': 'dd-mm-yyyy'})
        currency_format2 = workbook.add_format({'num_format': '##0.000','bold': True,})
        bold = workbook.add_format({'bold': True})
        bold_1 = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
        })
        sheet.set_row(5, 50)
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 28)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
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

        month = datetime.strptime(str(self.date_start), '%Y-%m-%d').strftime("%B")
        company = self.env.user.company_id

        sheet.merge_range('B3:E3', 'PAYSLIP BATCHES REPORT -' + month, format1)
        sheet.merge_range('B1:E1', company.name, format1)
        sheet.merge_range('B2:E2', (company.street or '') + ' ' + (company.street2 or '') + ' ' + (
                company.city or '') + ' ' + (company.state_id.name if company.state_id else '') + ' ' + (
                              company.country_id.name if company.country_id else '') + ' ' + (company.zip or ''),
                          bold_1)

        row = 0
        col = 0
        sheet.write(row + 5, col, 'S.No', format1)
        sheet.write(row + 5, col + 1, 'Employee ID', format1)
        sheet.write(row + 5, col + 2, 'Name', format1)
        sheet.write(row + 5, col + 3, 'Date of Joining', format1)
        sheet.write(row + 5, col + 4, 'Pay Days', format1)
        sheet.write(row + 5, col + 5, 'Number of Days Present', format1)
        sheet.write(row + 5, col + 6, 'BASIC', format1)
        sheet.write(row + 5, col + 7, 'Bonus', format1)
        sheet.write(row + 5, col + 8, 'HRA', format1)
        sheet.write(row + 5, col + 9, 'Conveyance Allowance', format1)
        sheet.write(row + 5, col + 10, 'Other Allowance', format1)
        sheet.write(row + 5, col + 11, 'Travel Allowance', format1)
        sheet.write(row + 5, col + 12, 'Medical Allowance', format1)
        sheet.write(row + 5, col + 13, 'Earnings Allowance', format1)
        sheet.write(row + 5, col + 14, 'Data Card Allowance', format1)
        sheet.write(row + 5, col + 15, 'Overtime Allowance', format1)
        sheet.write(row + 5, col + 16, 'Arrears', format1)
        sheet.write(row + 5, col + 17, 'Arrear', format1)
        sheet.write(row + 5, col + 18, 'Consolidate Pay', format1)
        sheet.write(row + 5, col + 19, 'Gross', format1)
        sheet.write(row + 5, col + 20, 'Employee PF', format1)
        sheet.write(row + 5, col + 21, 'Employer PF', format1)
        sheet.write(row + 5, col + 22, 'Employee ESI', format1)
        sheet.write(row + 5, col + 23, 'Employer ESI', format1)
        sheet.write(row + 5, col + 24, 'Gratuity', format1)
        sheet.write(row + 5, col + 25, 'Mobile Deduction', format1)
        sheet.write(row + 5, col + 26, 'Advance Salary', format1)
        sheet.write(row + 5, col + 27, 'TDS', format1)
        sheet.write(row + 5, col + 28, 'Other Deduction', format1)
        sheet.write(row + 5, col + 29, 'PT', format1)
        sheet.write(row + 5, col + 30, 'Total Deduction', format1)
        sheet.write(row + 5, col + 31, 'Net', format1)
        sheet.write(row + 5, col + 32, 'ESI Number', format1)
        sheet.write(row + 5, col + 33, 'PF Number', format1)
        sheet.write(row + 5, col + 34, 'PF/UAN Number', format1)
        s_no = 1    
        basic_tot = 0
        bonus_tot = 0
        hra_tot = 0
        conveyance_tot = 0
        other_tot = 0
        travel_tot = 0
        medical_tot = 0
        ea_tot = 0
        card_tot = 0
        ot_tot = 0
        arrears_tot = 0
        arrear_tot = 0
        consolidate_tot = 0
        gross_tot = 0
        employeepf_tot = 0
        employerpf_tot = 0
        employeeesi_tot = 0
        employeresi_tot = 0
        gratuity_tot = 0
        mobile_tot = 0
        advsalary_tot = 0
        tds_tot = 0
        otherded_tot = 0
        pt_tot = 0
        totalded_tot = 0
        net_tot = 0
        for payslip in payslips:
            row += 1
            sheet.write(row + 5, col, s_no, format2)
            sheet.write(row + 5, col + 1, payslip.employee_id.employeeid, format2)
            sheet.write(row + 5, col + 2, payslip.employee_id.name, format3)
            sheet.write(row + 5, col + 3, payslip.employee_id.date_join, format3)
            sheet.write(row + 5, col + 4, payslip.tot_month_days, format2)
            sheet.write(row + 5, col + 5, payslip.tot_month_days - payslip.lop_days, format2)
            sheet.write(row + 5, col + 6, payslip.line_ids.filtered(lambda x: x.code == 'BASIC').total, format2)
            sheet.write(row + 5, col + 7, payslip.line_ids.filtered(lambda x: x.code == 'BONUS').total, format2)
            sheet.write(row + 5, col + 8, payslip.line_ids.filtered(lambda x: x.code == 'HRA').total, format2)
            sheet.write(row + 5, col + 9, payslip.line_ids.filtered(lambda x: x.code == 'CONV').total, format2)
            sheet.write(row + 5, col + 10, payslip.line_ids.filtered(lambda x: x.code == 'OTHER').total, format2)
            sheet.write(row + 5, col + 11, payslip.line_ids.filtered(lambda x: x.code == 'Travel').total, format2)
            sheet.write(row + 5, col + 12, payslip.line_ids.filtered(lambda x: x.code == 'Medical').total, format2)
            sheet.write(row + 5, col + 13, payslip.line_ids.filtered(lambda x: x.code == 'EA').total, format2)
            sheet.write(row + 5, col + 14, payslip.line_ids.filtered(lambda x: x.code == 'CARD').total, format2)
            sheet.write(row + 5, col + 15, payslip.line_ids.filtered(lambda x: x.code == 'NOT').total, format2)
            sheet.write(row + 5, col + 16, payslip.line_ids.filtered(lambda x: x.code == 'ARR').total, format2)
            sheet.write(row + 5, col + 17, payslip.line_ids.filtered(lambda x: x.code == 'AR').total, format2)
            sheet.write(row + 5, col + 18, payslip.line_ids.filtered(lambda x: x.code == 'CON').total, format2)
            sheet.write(row + 5, col + 19, payslip.line_ids.filtered(lambda x: x.code == 'GROSS').total, format2)
            sheet.write(row + 5, col + 20, payslip.line_ids.filtered(lambda x: x.code == 'EEPF').total, format2)
            sheet.write(row + 5, col + 21, payslip.line_ids.filtered(lambda x: x.code == 'EPF').total, format2)
            sheet.write(row + 5, col + 22, payslip.line_ids.filtered(lambda x: x.code == 'ESI').total, format2)
            sheet.write(row + 5, col + 23, payslip.line_ids.filtered(lambda x: x.code == 'ESI2').total, format2)
            sheet.write(row + 5, col + 24, payslip.line_ids.filtered(lambda x: x.code == 'GR').total, format2)
            sheet.write(row + 5, col + 25, payslip.line_ids.filtered(lambda x: x.code == 'MD').total, format2)
            sheet.write(row + 5, col + 26, payslip.line_ids.filtered(lambda x: x.code == 'AS').total, format2)
            sheet.write(row + 5, col + 27, payslip.line_ids.filtered(lambda x: x.code == 'TDS').total, format2)
            sheet.write(row + 5, col + 28, payslip.line_ids.filtered(lambda x: x.code == 'OD').total, format2)
            sheet.write(row + 5, col + 29, payslip.line_ids.filtered(lambda x: x.code == 'PT').total, format2)
            sheet.write(row + 5, col + 30,
                        sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'DED').mapped('total')), format2)
            sheet.write(row + 5, col + 31, payslip.line_ids.filtered(lambda x: x.code == 'NET').total, format2)
            sheet.write(row + 5, col + 32, payslip.employee_id.esi_number, format2)
            sheet.write(row + 5, col + 33, payslip.employee_id.pf_number, format2)
            sheet.write(row + 5, col + 34, payslip.employee_id.uan_number, format2)
            s_no += 1
            basic_tot += payslip.line_ids.filtered(lambda x: x.code == 'BASIC').total
            bonus_tot += payslip.line_ids.filtered(lambda x: x.code == 'BONUS').total
            hra_tot += payslip.line_ids.filtered(lambda x: x.code == 'HRA').total
            conveyance_tot += payslip.line_ids.filtered(lambda x: x.code == 'CONV').total
            other_tot += payslip.line_ids.filtered(lambda x: x.code == 'OTHER').total
            travel_tot += payslip.line_ids.filtered(lambda x: x.code == 'Travel').total
            medical_tot += payslip.line_ids.filtered(lambda x: x.code == 'Medical').total
            ea_tot += payslip.line_ids.filtered(lambda x: x.code == 'EA').total
            card_tot += payslip.line_ids.filtered(lambda x: x.code == 'CARD').total
            ot_tot += payslip.line_ids.filtered(lambda x: x.code == 'NOT').total
            arrears_tot += payslip.line_ids.filtered(lambda x: x.code == 'ARR').total
            arrear_tot += payslip.line_ids.filtered(lambda x: x.code == 'AR').total
            consolidate_tot += payslip.line_ids.filtered(lambda x: x.code == 'CON').total
            gross_tot += payslip.line_ids.filtered(lambda x: x.code == 'GROSS').total
            employeepf_tot += payslip.line_ids.filtered(lambda x: x.code == 'EEPF').total
            employerpf_tot += payslip.line_ids.filtered(lambda x: x.code == 'EPF').total
            employeeesi_tot += payslip.line_ids.filtered(lambda x: x.code == 'ESI').total
            employeresi_tot += payslip.line_ids.filtered(lambda x: x.code == 'ESI2').total
            gratuity_tot += payslip.line_ids.filtered(lambda x: x.code == 'GR').total
            mobile_tot += payslip.line_ids.filtered(lambda x: x.code == 'MD').total
            advsalary_tot += payslip.line_ids.filtered(lambda x: x.code == 'AS').total
            tds_tot += payslip.line_ids.filtered(lambda x: x.code == 'TDS').total
            otherded_tot += payslip.line_ids.filtered(lambda x: x.code == 'OD').total
            pt_tot += payslip.line_ids.filtered(lambda x: x.code == 'PT').total
            totalded_tot += sum(payslip.line_ids.filtered(lambda x: x.category_id.code == 'DED').mapped('total'))
            net_tot += payslip.line_ids.filtered(lambda x: x.code == 'NET').total
        sheet.write(row + 6, col + 5, "Totals", bold_1)
        sheet.write(row + 6, col + 6, basic_tot, bold_1)
        sheet.write(row + 6, col + 7, bonus_tot, bold_1)
        sheet.write(row + 6, col + 8, hra_tot, bold_1)
        sheet.write(row + 6, col + 9, conveyance_tot, bold_1)
        sheet.write(row + 6, col + 10, other_tot, bold_1)
        sheet.write(row + 6, col + 11, travel_tot, bold_1)
        sheet.write(row + 6, col + 12, medical_tot, bold_1)
        sheet.write(row + 6, col + 13, ea_tot, bold_1)
        sheet.write(row + 6, col + 14, card_tot, bold_1)
        sheet.write(row + 6, col + 15, ot_tot, bold_1)
        sheet.write(row + 6, col + 16, arrears_tot, bold_1)
        sheet.write(row + 6, col + 17, arrear_tot, bold_1)
        sheet.write(row + 6, col + 18, consolidate_tot, bold_1)
        sheet.write(row + 6, col + 19, gross_tot, bold_1)
        sheet.write(row + 6, col + 20, employeepf_tot, bold_1)
        sheet.write(row + 6, col + 21, employerpf_tot, bold_1)
        sheet.write(row + 6, col + 22, employeeesi_tot, bold_1)
        sheet.write(row + 6, col + 23, employeresi_tot, bold_1)
        sheet.write(row + 6, col + 24, gratuity_tot, bold_1)
        sheet.write(row + 6, col + 25, mobile_tot, bold_1)
        sheet.write(row + 6, col + 26, advsalary_tot, bold_1)
        sheet.write(row + 6, col + 27, tds_tot, bold_1)
        sheet.write(row + 6, col + 28, otherded_tot, bold_1)
        sheet.write(row + 6, col + 29, pt_tot, bold_1)
        sheet.write(row + 6, col + 30, totalded_tot, bold_1)
        sheet.write(row + 6, col + 31, net_tot, bold_1)

        workbook.close()
        fo = open(url + 'Payslip Batches Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'filedata': out, 'filename': 'Payslip Batches Report.xlsx'})

    def salary_excel_eport_esi(self):
        url = "/tmp/"
        workbook = xlsxwriter.Workbook(url + 'esi_report_new.xlsx')
        worksheet = workbook.add_worksheet()
        # creation of header
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'white'})
        merge_format2 = workbook.add_format({
            'bold': 1, 'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'underline': 'underline', })
        merge_format1 = workbook.add_format({
            'align': 'center',
            'font_size': 11,
            'valign': 'vcenter', })
        merge_format3 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'font_size': 11,
            'valign': 'vcenter',
            'fg_color': 'gray'})
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 20)
        worksheet.set_column('M:M', 20)

        month = datetime.strptime(str(self.date_start), '%Y-%m-%d').strftime("%B")
        worksheet.merge_range('A1:C1', self.env['res.company']._company_default_get('fnet_hrms').name, merge_format)
        worksheet.merge_range('A2:C2', 'ESI REPORT ' + month, merge_format)
        worksheet.write('A4', "S.No", merge_format3)
        worksheet.write('B4', "Employee ID", merge_format3)
        worksheet.write('C4', "Employee Name", merge_format3)
        worksheet.write('D4', "No of Working Days", merge_format3)
        worksheet.write('E4', "Total Wages", merge_format3)
        worksheet.write('F4', "ESI Amount", merge_format3)
        worksheet.write('G4', "ESI Number", merge_format3)
        worksheet.write('H4', "Basic", merge_format3)
        worksheet.write('I4', "HRA", merge_format3)
        worksheet.write('J4', "Bonus", merge_format3)
        worksheet.write('K4', "Travel Allowance", merge_format3)

        n = 5
        c = 1
        payslips = self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'ESI' and x.total > 0).mapped('slip_id')
        for slip in payslips:
            aa = self.env['hr.contract'].search([('employee_id', '=', slip.employee_id.id), ('state', '=', 'open')])
            if aa:
                worksheet.write('A' + str(n), str(c), merge_format1)
                worksheet.write('B' + str(n), slip.employee_id.employeeid, merge_format1)
                worksheet.write('C' + str(n), slip.employee_id.name, merge_format1)
                worksheet.write('D' + str(n), slip.contract_id.new_employee - slip.lop_days if slip.contract_id.is_new_emp else 30 - slip.lop_days, merge_format1)
                worksheet.write('E' + str(n),sum(slip.line_ids.filtered(lambda x: x.code == 'GROSS').mapped('total')), merge_format1)
                worksheet.write('F' + str(n), sum(slip.line_ids.filtered(lambda x: x.code == 'ESI').mapped('total')), merge_format1)
                worksheet.write('G' + str(n), slip.employee_id.esi_number if slip.employee_id.esi_number else ' ', merge_format1)
                worksheet.write('H' + str(n), sum(slip.line_ids.filtered(lambda x: x.code == 'BASIC').mapped('total')), merge_format1)
                worksheet.write('I' + str(n), sum(slip.line_ids.filtered(lambda x: x.code == 'HRA').mapped('total')), merge_format1)
                worksheet.write('J' + str(n), sum(slip.line_ids.filtered(lambda x: x.code == 'BONUS').mapped('total')), merge_format1)
                worksheet.write('K' + str(n), sum(slip.line_ids.filtered(lambda x: x.code == 'Travel').mapped('total')),merge_format1)

                n += 1
                c += 1

        workbook.close()
        fo = open(url + 'esi_report_new.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'data_esi': out, 'esi_name': 'esi_report_' + month + '.xls'})

    def pf_excel_report(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'pf_report_new.xlsx')
        worksheet = workbook.add_worksheet()
        # creation of header
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'white'})
        merge_format2 = workbook.add_format({
            'bold': 1, 'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'underline': 'underline', })
        merge_format1 = workbook.add_format({
            'align': 'center',
            'font_size': 11,
            'valign': 'vcenter', })
        merge_format3 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'font_size': 11,
            'valign': 'vcenter',
            'fg_color': 'gray'})
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 20)
        worksheet.set_column('M:M', 20)

        month = datetime.strptime(str(self.date_start), '%Y-%m-%d').strftime("%B")
        worksheet.merge_range('A1:C1', self.env['res.company']._company_default_get('fnet_hrms').name, merge_format)
        worksheet.merge_range('A2:C2', 'PF REPORT - ' + month, merge_format)
        worksheet.write('A4', "S.No", merge_format3)
        worksheet.write('B4', "UAN NUMBER", merge_format3)
        worksheet.write('C4', "EMPLOYEE NAME", merge_format3)
        worksheet.write('D4', "GROSS WAGES", merge_format3)
        worksheet.write('E4', "EPF WAGES", merge_format3)
        worksheet.write('F4', "EPS WAGES", merge_format3)
        worksheet.write('G4', "EDLI WAGES", merge_format3)
        worksheet.write('H4', "EPF CONTRI REMITTED", merge_format3)
        worksheet.write('I4', "EPS CONTRI REMITTED", merge_format3)
        worksheet.write('J4', "EPF EPS DIFF REMITTED", merge_format3)
        worksheet.write('K4', "NCP DAYS", merge_format3)
        worksheet.write('L4', "REFUND OF ADVANCES", merge_format3)

        n = 5
        c = 1
        payslips = self.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'EEPF' and x.total > 0).mapped('slip_id')
        for slip in payslips:
            pf_calculation = sum(slip.line_ids.filtered(lambda x: x.code in ['BASIC', 'BONUS', 'Travel']).mapped('total'))
            hra = sum(slip.line_ids.filtered(lambda x: x.code == 'HRA').mapped('total'))
            aa = self.env['hr.contract'].search([('employee_id', '=', slip.employee_id.id), ('state', '=', 'open')])
            if aa:
                val = vals = val2 = 0.0
                if pf_calculation:
                    val = pf_calculation
                if hra:
                    vals = hra
                    val2 = (val - vals) * 0.12
                    val3 = (val - vals) * 0.0833
                    val4 = round(float(val2)) if val2 <= 1800 else 1800
                    val5 = round(float(val3)) if val2 <= 1250 else 1250
                    val6 = val4 - val5
                    # val4 = val2 - val3
                worksheet.write('A' + str(n), str(c), merge_format1)
                worksheet.write('B' + str(n), slip.employee_id.uan_number if slip.employee_id.uan_number else ' ', merge_format1)
                worksheet.write('C' + str(n), slip.employee_id.name, merge_format1)
                worksheet.write('D' + str(n), pf_calculation if pf_calculation <= 15000 else 15000, merge_format1)
                worksheet.write('E' + str(n), pf_calculation if pf_calculation <= 15000 else 15000, merge_format1)
                worksheet.write('F' + str(n), pf_calculation if pf_calculation <= 15000 else 15000, merge_format1)
                worksheet.write('G' + str(n), pf_calculation if pf_calculation <= 15000 else 15000, merge_format1)
                worksheet.write('H' + str(n), val4, merge_format1)
                worksheet.write('I' + str(n), val5, merge_format1)
                worksheet.write('J' + str(n), round(val6), merge_format1)

                n += 1
                c += 1

        workbook.close()
        fo = open(url + 'pf_report_new.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'data_live_pf': out, 'data_pf': 'pf_report_' + month + '.xls'})


