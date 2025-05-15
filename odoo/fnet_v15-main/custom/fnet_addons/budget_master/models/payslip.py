# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from calendar import monthrange
from datetime import datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
import tempfile
import decimal
import base64
import string
import logging
import operator
from num2words import num2words


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    budget_id = fields.Many2one('department.budget', string="Budget")
    budget_line_id = fields.Many2one('department.budget.line', string="Budget Line")
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id", store=True)

    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()
        for payslip in self:
            if not payslip.budget_id:
                raise UserError(_("Select the Budget"))
        return res

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        if not self.budget_id:
            raise UserError(_("Select the Budget"))
        budget_line = self.budget_id.budget_lines.filtered(lambda x: x.department_id == self.employee_id.department_id)
        if budget_line:
            self.write({'budget_line_id': budget_line.id})
        return res


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    budget_id = fields.Many2one('department.budget', string="Budget", required=True)
    budget_lines = fields.One2many('payslip.budget', 'run_id', string="Payslip Budget")
    payslip_total = fields.Monetary(string='Total', compute="compute_amount", readonly=True)
    budget_total = fields.Monetary(string='Budget Total', compute="compute_amount", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id")
    state = fields.Selection(selection_add=[('submit', 'Waiting for Approval'), ('approve1', 'Finance Approved'),
                                            ('approve2', 'MD Approved'), ('close',), ('cancel', 'Rejected')])
    get_budget_report = fields.Binary('Budget Report', readonly=True)
    budget_report_name = fields.Char('Filename', size=64, readonly=True)

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_finance_approve(self):
        mail_content = "  Dear Ashok,<br/> the Budget for the month of " + self.date_start.strftime(
            "%B") + " is waiting for your approval.<br/> Click on the below link:<br/><a href='https://erp.futurenet.in/web#menu_id=415&action=923&model=payslip.budget&view_type=list'>View Budget</a>"

        main_content = {
            'subject': _('Budget Approval for %s 2022') % self.date_start.strftime("%B"),
            'email_from': 'accounts@futurenet.in',
            'body_html': mail_content,
            'email_to': 'lashok@futurenet.in'
        }
        self.env['mail.mail'].sudo().create(main_content).send()
        self.write({'state': 'approve1'})

    def action_md_approve(self):
        self.write({'state': 'approve2'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_reset(self):
        self.write({'state': 'draft'})

    @api.onchange('budget_id')
    def onchange_budget_id(self):
        if self.budget_id:
            if not self.budget_id.date_from <= self.date_start or not self.budget_id.date_to >= self.date_end:
                raise ValidationError("The Payslip Batch is not within the period of the budget selected")
            self.budget_lines = False
            for line in self.budget_id.budget_lines:
                self.budget_lines.create({
                    'run_id': self.id,
                    'department_id': line.department_id.id,
                    'expected_value': line.expected_value / 12,
                })

    @api.depends('slip_ids.line_ids.total')
    def compute_amount(self):
        payslip_run = self.env['hr.payslip.run'].search([])
        last_batch = payslip_run.filtered(lambda x: x.date_start.strftime('%m') == (self.date_start - relativedelta(months=1)).strftime('%m'))
        for rec in self:
            rec.payslip_total = sum(rec.slip_ids.mapped('line_ids').filtered(lambda x: x.code == 'NET').mapped('total'))
            for l in rec.budget_lines:
                actual_value = 0
                payslips = rec.slip_ids.filtered(lambda x: l.department_id.id in x.employee_id.budget_lines.mapped('department_id').ids)
                for slip in payslips:
                    budget_percentage = self.env['employee.budget.line'].search([('employee_id', '=', slip.employee_id.id), ('department_id', '=', l.department_id.id), ('date_from', '<=', slip.date_from) , ('date_to', '>=', slip.date_to)], limit=1)
                    actual_value += sum(slip.mapped('line_ids').filtered(lambda x: x.code in ['GROSS', 'EPF', 'ESI2', 'GR', 'NCC']).mapped('total')) * \
                                    (budget_percentage.percentage/1)
                l.actual_value = actual_value
                l.head_count = len(rec.slip_ids.filtered(lambda x: x.employee_id.department_id.id == l.department_id.id))
                l.difference_value = l.expected_value - l.actual_value
                l.last_actual_value = sum(last_batch.mapped('budget_lines').filtered(lambda x: x.department_id.id == l.department_id.id).mapped('actual_value'))

            rec.budget_total = sum(rec.budget_lines.mapped('actual_value'))

    def unlink(self):
        self.budget_lines.unlink()
        return super(HrPayslipRun, self).unlink()

    def generate_budget_report(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Budget Report.xlsx')
        sheet = workbook.add_worksheet()
        # departments =  self.slip_ids.read_group(domain=[], fields=['employee_id.department_id.parent_id.name'], groupby =[])
        # departments =  self.env['hr.department'].read_group(domain=[], fields=['parent_id'], groupby =['parent_id'])
        # print("dddddddddddddddddddddddddddddddddddddd", departments)
        format1 = workbook.add_format({'font_size': 11, 'align': 'vcenter', 'valign': 'center'})
        parent_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left'})
        child_format = workbook.add_format({'font_size': 11, 'align': 'left'})
        total_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#FFCCCB'})
        format1.set_text_wrap()
        format2 = workbook.add_format({'font_size': 12, 'align': 'center'})
        format3 = workbook.add_format({'font_size': 12, 'align': 'left', 'num_format': 'dd-mm-yyyy'})

        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        bold_1 = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        sheet.set_column('A:A', 30)
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
        sheet.merge_range('B3:E3', 'BUDGET REPORT', bold)
        sheet.write(5, 0, 'Employee', bold)
        sheet.write(5, 1, 'Gross', bold)
        sheet.write(5, 2, 'Employee PF', bold)
        sheet.write(5, 3, 'Employer ESI', bold)
        sheet.write(5, 4, 'Gratuity', bold)
        sheet.write(5, 5, 'Non-Cash Component', bold)
        sheet.write(5, 6, 'Total', bold)
        departments = self.budget_lines.mapped('department_id')
        parent_departments = departments.mapped('parent_id')
        other_deps = departments.filtered(lambda x: not x.parent_id and x.id not in parent_departments.ids)
        parent_departments += other_deps
        budget = self.env['employee.budget'].search([('date_from', '<=', self.date_start), ('date_to', '>=', self.date_end)], limit=1)
        if not budget:
            raise ValidationError('No Employee Budget found for this batch period')
        rows = 5
        for parent in departments:
            rows += 1
            sheet.merge_range(rows, 0, rows, 6, parent.name, bold)
            employees = self.slip_ids.mapped('employee_id').filtered(lambda x: parent.id in x.budget_lines.mapped('department_id').ids)
            for emp in employees:
                payslip = self.slip_ids.filtered(lambda x: x.employee_id.id == emp.id)
                budget_percentage = self.env['employee.budget.line'].search([('employee_id', '=', emp.id), ('department_id', '=', parent.id),('date_from', '<=', payslip.date_from), ('date_to', '>=', payslip.date_to)], limit=1)
                rows += 1
                sheet.write(rows, 0, emp.name, parent_format)
                sheet.write(rows, 1, sum(payslip.line_ids.filtered(lambda x: x.code == 'GROSS').mapped('total')), child_format)
                sheet.write(rows, 2, sum(payslip.line_ids.filtered(lambda x: x.code == 'EPF').mapped('total')), child_format)
                sheet.write(rows, 3, sum(payslip.line_ids.filtered(lambda x: x.code == 'ESI2').mapped('total')), child_format)
                sheet.write(rows, 4, sum(payslip.line_ids.filtered(lambda x: x.code == 'GR').mapped('total')), child_format)
                sheet.write(rows, 5, sum(payslip.line_ids.filtered(lambda x: x.code == 'NCC').mapped('total')), child_format)
                sheet.write(rows, 6, sum(payslip.line_ids.filtered(lambda x: x.code in ['GROSS','EPF','ESI2','GR','NCC']).mapped('total')) * budget_percentage.percentage/1, child_format)
        workbook.close()
        fo = open(url + 'Budget Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'get_budget_report': out, 'budget_report_name': 'Budget Report.xlsx'})

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note', 'budget_id'])
        rec_from_date = run_data.get('date_start')
        rec_to_date = run_data.get('date_end')
        budget_id = self.env['department.budget'].search([('id', '=', run_data.get('budget_id')[0])])
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        departments = budget_id.budget_lines.mapped('department_id')
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            if employee.department_id not in departments:
                raise UserError(_("The selected budget has no budget for the department %s") % employee.department_id.name)
            from_date = rec_from_date
            to_date = rec_to_date
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            if not employee.contract_id:
                raise UserError(_("No Contracts are current active for %s" % employee.name))
            if employee.contract_id.date_start > from_date:
                from_date = employee.contract_id.date_start
            if employee.contract_id.date_end and employee.contract_id.date_end < to_date:
                to_date = employee.contract_id.date_end
            if to_date < from_date:
                raise UserError(
                    _("Payslip can not generate for employee %s. Kindly check Contract Date's." % (employee.name)))
            start_month = fields.Date.from_string(from_date)
            end_month = fields.Date.from_string(to_date)
            start = start_month.replace(day=1)
            end = start_month.replace(day=monthrange(start_month.year, start_month.month)[1])
            lop_days = 0
            if start_month > start:
                lop_days += (start_month - start).days
            if end_month < end:
                lop_days += (end - end_month).days

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'budget_id': budget_id.id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'lop_days': lop_days,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}




class BudgetLines(models.Model):
    _name = 'payslip.budget'
    _description = 'Payslip Budget'
    _rec_name = 'department_id'

    run_id = fields.Many2one('hr.payslip.run', string='Payslip Batch')
    date_start = fields.Date('Start Date', related="run_id.date_start", store=True)
    date_end = fields.Date('End Date', related="run_id.date_end")
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Waiting for Approval'),
                              ('approve1', 'Finance Approved'), ('approve2', 'MD Approved'), ('cancel', 'Rejected')], related="run_id.state")
    department_id = fields.Many2one('hr.department', string='Department')
    parent_department_id = fields.Many2one('hr.department', string='Parent Department', related='department_id.parent_id', store=True)
    head_count = fields.Integer(string="Head Count")
    expected_value = fields.Float('Budget')
    difference_value = fields.Float('Difference')
    actual_value = fields.Float('Actual Expense')
    remarks = fields.Text(string="Remarks")
    last_actual_value = fields.Float('Last Month Expense')

    def action_finance_approve(self):
        if self.run_id:
            self.run_id.action_finance_approve()

    def action_md_approve(self):
        if self.run_id:
            self.run_id.action_md_approve()

    def action_cancel(self):
        if self.run_id:
            self.run_id.action_cancel()

    def view_employee(self):
        employee = self.run_id.slip_ids.mapped('employee_id').filtered(lambda x: x.department_id.id == self.department_id.id)
        return {
            'name': _('Employee(s)'),
            'res_model': 'hr.employee',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', employee.ids)],
            'view_id': False,
            'view_mode': 'tree,form',
        }

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # if 'pin' in groupby or 'pin' in self.env.context.get('group_by', '') or self.env.context.get('no_group_by'):
        #     raise exceptions.UserError(_('Such grouping is not allowed.'))
        if 'run_id' in groupby:
            # domain = [('run_id', '!=', False)]
            orderby = 'date_start desc,run_id desc'
        return super(BudgetLines, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,lazy=lazy)
