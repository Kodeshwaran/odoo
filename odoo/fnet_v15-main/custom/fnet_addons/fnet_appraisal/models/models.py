# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64
import xlsxwriter
from io import StringIO
from odoo.exceptions import UserError


class BulkAppraisal(models.Model):
    _name = "bulk.appraisal"
    _description = 'Bulk Appraisal'
    _rec_name = 'number'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')], string="Status", default='draft', tracking=True,)
    number = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    name = fields.Char("Name", required=1)
    date = fields.Date("Effective From", required=1)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    line_ids = fields.One2many('bulk.appraisal.line', 'appraisal_id', string="Salary Details")

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('number', _('New')) == _('New'):
            seq_date = None
            if 'date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
            vals['number'] = self.env['ir.sequence'].next_by_code('bulk.appraisal', sequence_date=seq_date) or _('New')
        result = super(BulkAppraisal, self).create(vals)
        return result

    def action_validate(self):
        for line in self.line_ids:
            line.contract_id.write({
                'struct_id': line.revised_structure_id.id,
                'wage': line.revised_ctc,
                'travel_allowance': line.revised_ta,
                'earning_alw': line.revised_ea,
            })
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError(_("Completed records cannot be deleted."))
        return super(BulkAppraisal, self).unlink()

    def action_print(self):
        output = StringIO()
        url = '/tmp/'
        report_name = "Appraisal Report - %s" % self.date.year
        workbook = xlsxwriter.Workbook(url + report_name + '.xlsx')
        worksheet = workbook.add_worksheet()
        col_header = workbook.add_format(
            {'bold': 1, 'font_size': 15, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Liberation Serif',
             'border': 1, 'fg_color': 'gray'})
        col_value = workbook.add_format(
            {'font_size': 12, 'align': 'right', 'valign': 'vcenter', 'font_name': 'Liberation Serif',
             'border': 1, 'num_format': '#,##0.00'})
        total_format = workbook.add_format(
            {'num_format': '#,##0.00', 'bold': 1, 'border': 1, 'font_size': 13, 'align': 'right', 'valign': 'vcenter',
             'font_name': 'Liberation Serif', 'fg_color': 'yellow'})
        worksheet.set_column('A:B', 25)
        worksheet.set_column('C:I', 15)
        worksheet.write('A1', 'Employee', col_header)
        worksheet.write('B1', 'Current Structure', col_header)
        worksheet.write('C1', 'Current CTC', col_header)
        worksheet.write('D1', 'Travel Allowance', col_header)
        worksheet.write('E1', 'Earned Allowance', col_header)
        worksheet.write('F1', 'Revised CTC', col_header)
        worksheet.write('G1', 'Revised Structure', col_header)
        worksheet.write('H1', 'Revised Travel Allowance', col_header)
        worksheet.write('I1', 'Revised Earned Allowance', col_header)
        n = 2
        for line in self.line_ids:
            worksheet.write('A' + str(n), line.employee_id.name, col_value)
            worksheet.write('B' + str(n), line.current_structure_id.name, col_value)
            worksheet.write('C' + str(n), line.current_ctc, col_value)
            worksheet.write('D' + str(n), line.current_ta, col_value)
            worksheet.write('E' + str(n), line.current_ea, col_value)

            worksheet.write('F' + str(n), line.revised_ctc, col_value)
            worksheet.write('G' + str(n), line.revised_structure_id.name, col_value)
            worksheet.write('H' + str(n), line.revised_ta, col_value)
            worksheet.write('I' + str(n), line.revised_ea, col_value)
            n += 1
        worksheet.write('A' + str(n), "Total", total_format)
        worksheet.write('B' + str(n), '', total_format)
        worksheet.write('C' + str(n), sum(self.line_ids.mapped('current_ctc')), total_format)
        worksheet.write('D' + str(n), sum(self.line_ids.mapped('current_ta')), total_format)
        worksheet.write('E' + str(n), sum(self.line_ids.mapped('current_ea')), total_format)

        worksheet.write('F' + str(n), sum(self.line_ids.mapped('revised_ctc')), total_format)
        worksheet.write('G' + str(n), '', total_format)
        worksheet.write('H' + str(n), sum(self.line_ids.mapped('revised_ta')), total_format)
        worksheet.write('I' + str(n), sum(self.line_ids.mapped('revised_ea')), total_format)
        workbook.close()
        fo = open(url + report_name + '.xlsx', "rb+")
        values = {
            'name': report_name + '.xlsx',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'datas': base64.encodestring(fo.read()),
        }
        attachment_id = self.env['ir.attachment'].sudo().create(values)
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }


class BulkAppraisalLine(models.Model):
    _name = 'bulk.appraisal.line'
    _description = 'Bulk Appraisal Line'

    appraisal_id = fields.Many2one('bulk.appraisal', string="Appraisal")
    state = fields.Selection(related='appraisal_id.state', string="Status")
    date = fields.Date(related='appraisal_id.date', string="Effective From")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    contract_id = fields.Many2one('hr.contract', string="Contract")
    current_ctc = fields.Float("Current CTC")
    current_structure_id = fields.Many2one('hr.payroll.structure', string="Current Structure")
    current_ta = fields.Float("Travel Allowance")
    current_ea = fields.Float("Earned Allowance")

    revised_ctc = fields.Float("Revised CTC")
    revised_structure_id = fields.Many2one('hr.payroll.structure', string="Revised Structure")
    revised_ta = fields.Float("Revised Travel Allowance")
    revised_ea = fields.Float("Revised Earned Allowance")

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1)
            if contract:
                self.contract_id = contract.id
                self.current_ctc = contract.wage
                self.current_structure_id = contract.struct_id.id
                self.current_ta = contract.travel_allowance
                self.current_ea = contract.earning_alw

                self.revised_ctc = contract.wage
                self.revised_structure_id = contract.struct_id.id
                self.revised_ta = contract.travel_allowance
                self.revised_ea = contract.earning_alw


class HrContract(models.Model):
    _inherit = 'hr.contract'

    appraisal_line_ids = fields.One2many('bulk.appraisal.line', 'contract_id', string="Appraisals")