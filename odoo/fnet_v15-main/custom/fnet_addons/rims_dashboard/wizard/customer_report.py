# -*- coding: utf-8 -*-

from odoo import models, fields, api
from werkzeug.urls import url_encode
from odoo.exceptions import UserError, ValidationError
import xlsxwriter
import base64
from io import StringIO


FIELDS_TEMPLATE = ['service_code', 'rims_scope','contract_type', 'epo_count','first_epo_count',
                   'street', 'street2', 'city', 'state_id', 'zip', 'country_id',
                   'contract_document', 'tool_name', 'tool_version', 'monitoring_ip_address', 'environment_access']


class CustomerReportWizard(models.TransientModel):
    _name = 'rims.customer.report'
    _description = 'RIMS Customer Report'

    customer_id = fields.Many2one('rims.customer.master', string="Customer Name")
    contract_start_date = fields.Char(string="Contract Start Date")
    contract_end_date = fields.Char(string="Contract End Date")
    service_code = fields.Char(string="Service Code")
    rims_scope = fields.Char(string="RIMS Scope")
    contract_type = fields.Many2one('rims.contract.type', string="Contract Type")
    epo_count = fields.Integer(string="EPO's count")
    first_epo_count = fields.Integer(string="EPO's Count as per the Contract")
    street = fields.Char(string='Address(H.O)')
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    contract_document = fields.Many2many('ir.attachment', string="Contract Document")
    # contract_document_filename = fields.Char(string='Contract Filename', size=64, readonly=True)
    customer_matrix = fields.Many2many('customer.matrix.line', readonly=True)
    escalation_matrix = fields.Many2many('escalation.matrix.line', readonly=True)
    monitoring_details = fields.Many2many('monitoring.details', readonly=True)
    tool_name = fields.Char(string="Monitor Tool")
    tool_version = fields.Char(string="Monitor Tool Version")
    monitoring_ip_address = fields.Char(string="Monitoring IP")
    environment_access = fields.Char(string="Customer Environment Access")
    monitoring_alert_members = fields.Many2many('monitoring.alert.members', readonly=True)
    report_members = fields.Many2many('report.members', string='Report Members', readonly=True)
    vendor_details = fields.Many2many('vendor.details', string="Vendor Details", readonly=True)
    # report_member_daily = fields.Many2many('report.members', relation='report_members_daily_rel', string='Report Members Daily', readonly=True)
    technology_supported = fields.Many2many('technology.landscape.line', readonly=True)
    epo_details = fields.Many2many('epo.details', string="EPO Details", readonly=True)
    support_details = fields.Many2many('support.details', string="Support Subscription", readonly=True)
    epo_supported = fields.Many2many('epo.supported', string="EPO Supported", readonly=True)
    monitoring_thresholds_ids = fields.Many2many('monitoring.thresholds', string="EPO Supported", readonly=True)

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        self.ensure_one()
        if self.customer_id:
            for field in FIELDS_TEMPLATE:
                value = self.customer_id[field]
                if value:
                    self[field] = value
            self.contract_start_date = self.customer_id.date_start.strftime('%d-%b-%Y').upper() if self.customer_id.date_start else False
            self.contract_end_date = self.customer_id.date_end.strftime('%d-%b-%Y').upper() if self.customer_id.date_end else False
            self.customer_matrix = [(6, 0, self.customer_id.customer_matrix.ids)] if self.customer_id.customer_matrix else False
            self.escalation_matrix = [(6, 0, self.customer_id.escalation_matrix.ids)] if self.customer_id.escalation_matrix else False
            self.monitoring_details = [(6, 0, self.customer_id.monitoring_details.ids)] if self.customer_id.monitoring_details else False
            self.monitoring_alert_members = [(6, 0, self.customer_id.monitoring_alert_members.ids)] if self.customer_id.monitoring_alert_members else False
            self.report_members = [(6, 0, self.customer_id.report_members.ids)] if self.customer_id.report_members else False
            self.vendor_details = [(6, 0, self.customer_id.vendor_details.ids)] if self.customer_id.vendor_details else False
            # self.report_member_daily = [(6, 0, self.customer_id.report_member_daily.ids)] if self.customer_id.report_member_daily else False
            self.technology_supported = [(6, 0, self.customer_id.technology_supported.ids)] if self.customer_id.technology_supported else False
            self.epo_details = [(6, 0, self.customer_id.epo_details.ids)] if self.customer_id.epo_details else False
            self.epo_supported = [(6, 0, self.customer_id.epo_supported.ids)] if self.customer_id.epo_supported else False
            self.monitoring_thresholds_ids = [(6, 0, self.customer_id.monitoring_thresholds_ids.ids)] if self.customer_id.monitoring_thresholds_ids else False
            self.support_details = [(6, 0, self.customer_id.support_details.ids)] if self.customer_id.support_details else False
            for support, customer in zip(self.support_details, self.customer_id.support_details):
                support.s_no = customer.s_no
            for support, customer in zip(self.epo_details, self.customer_id.epo_details):
                support.s_no = customer.s_no


    def get_contract_document(self):
        # if self.customer_id.contract_document:
        #     for record in self.customer_id.contract_document:
        #         return {
        #             'type': 'ir.actions.act_url',
        #             'name': 'Download',
        #             'target': 'new',
        #             'url': '/web/content/' + str(record.id) + '?filename=' + record.name + '&amp;field=datas&amp;model=ir.attachment&amp;download=false',
        #         }
        if self.customer_id.contract_document:
            record = self.customer_id.contract_document[0]
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            download_url = '/web/content/' + str(record.id) + '?download=True'
            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "self",
            }
        else:
            return False



    def action_epo_report(self):
        output = StringIO()
        url = '/tmp/'
        report_name = "EPO_Details"
        workbook = xlsxwriter.Workbook(url + report_name + '.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_name': 'Arial'})
        format = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})

        sheet.set_column('B:B', 35)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:F', 15)
        sheet.set_column('G:G', 35)

        sheet.write('A1', 'S.No', format)
        sheet.write('B1', 'Device Name', format)
        sheet.write('C1', 'IP Address', format)
        sheet.write('D1', 'EPO Type', format)
        sheet.write('E1', 'Device Category', format)
        sheet.write('F1', 'Technology', format)
        sheet.write('G1', 'Folder', format)

        n = 2
        s_no = 1
        employees = self.customer_id.epo_details

        for employee in employees:
            sheet.write('A' + str(n), s_no, format1)
            sheet.write('B' + str(n), employee.device_name, format1)
            sheet.write('C' + str(n), employee.ip_address, format1)
            sheet.write('D' + str(n), employee.epo_type_id.name, format1)
            sheet.write('E' + str(n), employee.device_category_id.name, format1)
            sheet.write('F' + str(n), employee.technology_id.name, format1)
            sheet.write('G' + str(n), employee.folder, format1)

            n += 1
            s_no += 1
        workbook.close()

        fo = open(url + 'EPO_Details' + '.xlsx', "rb+")
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
            "target": "self",
        }

    def action_mt_report(self):
        output = StringIO()
        url = '/tmp/'
        report_name = "Monitoring_Thresholds"
        workbook = xlsxwriter.Workbook(url + report_name + '.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_name': 'Arial'})
        format = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})

        sheet.set_column('B:N', 20)
        # sheet.set_column('C:C', 20)
        # sheet.set_column('D:F', 15)
        # sheet.set_column('G:G', 35)

        sheet.write('A1', 'S.No', format)
        sheet.write('B1', 'Host Name', format)
        sheet.write('C1', 'Service', format)
        sheet.write('D1', 'EPO Type', format)
        sheet.write('E1', 'Criticality', format)
        sheet.write('F1', 'CPU Capacity', format)
        sheet.write('G1', 'CPU Warn (%)', format)
        sheet.write('H1', 'CPU Crit (%)', format)
        sheet.write('I1', 'Memory Capacity', format)
        sheet.write('J1', 'Memory Warn (%)', format)
        sheet.write('K1', 'Memory Warn (%)', format)
        sheet.write('L1', 'Disk Capacity', format)
        sheet.write('M1', 'Disk Warn (%)', format)
        sheet.write('N1', 'Disk Warn (%)', format)

        n = 2
        s_no = 1
        employees = self.customer_id.monitoring_thresholds_ids

        for employee in employees:
            sheet.write('A' + str(n), s_no, format1)
            sheet.write('B' + str(n), employee.host_id.device_name, format1)
            sheet.write('C' + str(n), employee.ip_address, format1)
            sheet.write('D' + str(n), employee.service, format1)
            sheet.write('E' + str(n), employee.criticality, format1)
            sheet.write('F' + str(n), employee.cpu_capacity, format1)
            sheet.write('G' + str(n), employee.cpu_warn_percentage, format1)
            sheet.write('H' + str(n), employee.cpu_crit_percentage, format1)
            sheet.write('I' + str(n), employee.memory_capacity, format1)
            sheet.write('J' + str(n), employee.memory_warn_percentage, format1)
            sheet.write('K' + str(n), employee.memory_crit_percentage, format1)
            sheet.write('L' + str(n), employee.disk_capacity, format1)
            sheet.write('M' + str(n), employee.disk_warn_percentage, format1)
            sheet.write('N' + str(n), employee.disk_crit_percentage, format1)

            n += 1
            s_no += 1
        workbook.close()

        fo = open(url + 'Monitoring_Thresholds' + '.xlsx', "rb+")
        values = {
            'name': 'Monitoring_Thresholds.xlsx',
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