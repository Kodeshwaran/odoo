from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import xlrd
import base64

class EpoDetailsWizard(models.TransientModel):
    _name = "epo.details.wizard"

    epo_upload_file = fields.Binary(string="Upload file", tracking=True)
    file_name = fields.Char('File Name', tracking=True)
    customer_id = fields.Many2one('rims.customer.master')

    @api.depends('epo_upload_file')
    def action_generate_last_epo_details(self):
        if not self.epo_upload_file:
            raise ValidationError('The uploaded file is empty. Please upload a valid file.')
        self.customer_id.epo_details.unlink()
        self.customer_id.monitoring_details.unlink()
        self.customer_id.report_members.unlink()
        self.customer_id.escalation_matrix.unlink()
        self.customer_id.customer_matrix.unlink()
        if self.epo_upload_file:
            epo_upload_file = base64.b64decode(self.epo_upload_file)
            try:
                wb = xlrd.open_workbook(file_contents=epo_upload_file)

            except xlrd.biffh.XLRDError:
                raise ValidationError(
                    _('The uploaded file is not a valid Excel file. Please upload a valid .xls or .xlsx file.'))
            sheet = wb.sheet_by_index(0)
            for row in range(1, sheet.nrows):
                row_values = sheet.row_values(row)
                rims_epo_type= self.env['epo.type'].search([('name', '=', str(row_values[3]))], limit=1)
                if not rims_epo_type:
                    raise ValidationError(_('"%s" is not in Application type list' % (row_values[3])))
                rims_device_category = self.env['device.category'].search([('name', '=', str(row_values[4]))], limit=1)
                if not rims_device_category:
                    raise ValidationError(_('"%s" is not in Application type list' % (row_values[4])))
                rims_platform = self.env['service.type'].search([('name', '=', str(row_values[5]))], limit=1)
                if not rims_platform:
                    raise ValidationError(_('"%s" is not in Application type list' % (row_values[5])))
                rims_technology = self.env['service.type'].search([('name', '=', str(row_values[5]))], limit=1)
                if not rims_technology:
                    raise ValidationError(_('"%s" is not in Application type list' % (row_values[5])))
                self.env['epo.details'].create({
                    'customer_id': self.customer_id.id,
                    'device_name': row_values[1] if row_values[1] else ' ',
                    'ip_address': row_values[2] if row_values[2] else ' ',
                    'epo_type_id': rims_epo_type.id if rims_epo_type.id else '',
                    'device_category_id': rims_device_category.id if rims_device_category.id else '',
                    'platform_id': rims_platform.id if rims_platform.id else '',
                    'technology_id': rims_technology.id if rims_technology.id else '',
                    'folder': row_values[7] if row_values[7] else ' ',
                    'create_date': row_values[8] if row_values[8] else ' ',
                })

            sheet = wb.sheet_by_index(1)
            for row in range(0, sheet.nrows):
                row_values = sheet.row_values(row)
            self.env['customer.matrix.line'].create({
                'customer_id': self.customer_id.id,
                'person': row_values[0] if row_values[0] else ' ',
                'name': row_values[1] if row_values[1] else ' ',
                'email': row_values[2] if row_values[2] else ' ',
                'contact_number': row_values[3] if row_values[3] else ' ',

            })

            sheet = wb.sheet_by_index(2)
            for row in range(0, sheet.nrows):
                row_values = sheet.row_values(row)
            self.env['escalation.matrix.line'].create({
                'customer_id': self.customer_id.id,
                'level': row_values[0] if row_values[0] else ' ',
                'name': row_values[1] if row_values[1] else ' ',
                'designation': row_values[2] if row_values[2] else ' ',
                'email': row_values[3] if row_values[3] else ' ',
                'contact_number': row_values[4] if row_values[4] else ' ',
                'escalation_time': row_values[5] if row_values[5] else ' ',
            })

            sheet = wb.sheet_by_index(3)
            tool_name = ''
            tool_version = ''
            environment_access = ''
            monitoring_ip_address = ''
            for row in range(0, sheet.nrows):
                row_values = sheet.row_values(row)
                if len(row_values) == 2:
                    if row == 0:
                        tool_name = row_values[1] if row_values[1] else ''

                    if row == 1:
                        tool_version = row_values[1] if row_values[1] else ''

                    if row == 2:
                        monitoring_ip_address = row_values[1] if row_values[1] else ''

                    if row == 3:
                        environment_access = row_values[1] if row_values[1] else ''

            self.customer_id.write({
                'tool_name': tool_name,
                'tool_version': tool_version,
                'monitoring_ip_address': monitoring_ip_address,
                'environment_access': environment_access,
            })
            for row in range(6, sheet.nrows):
                row_values = sheet.row_values(row)
                self.env['monitoring.details'].create({
                    'customer_id': self.customer_id.id,
                    'monitoring_url': row_values[0] if row_values[0] else ' ',
                })

            sheet = wb.sheet_by_index(4)
            for row in range(0, sheet.nrows):
                row_values = sheet.row_values(row)
            if len(row_values) == 2:
                self.env['report.members'].create({
                    'customer_id': self.customer_id.id,
                    'report_type': row_values[0] if row_values[0] else '',
                    'name': row_values[1] if row_values[1] else '',
                    'mail_type': row_values[2] if row_values[2] else '',
                    'email': row_values[3] if row_values[3] else '',
                })