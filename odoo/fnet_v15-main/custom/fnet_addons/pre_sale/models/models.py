# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64
import io  # Required for handling BytesIO streams
import xlsxwriter  # Required for generating Excel files
from odoo import models, fields
from odoo.http import request


class SaleType(models.Model):
    _inherit = 'sale.type'

    pre_sale_users = fields.Many2many('res.users', string="Pre Sale Person")
    email_to= fields.Char(string='Email To')
    email_cc= fields.Char(string='Email Cc')


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    pre_sale_alert = fields.Boolean(string="Send Pre Sale Intimation")
    is_pre_sale = fields.Boolean(string="Is Pre Sale")


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    pre_sale = fields.Boolean(string="Pre Sales")
    pre_sale_users = fields.Many2many('res.users', string="Pre Sale Person", related="sale_type_id.pre_sale_users")
    opportunity_type = fields.Selection([('normal', 'Normal Sales'), ('pre_sale', 'Pre Sales')], default='normal',
                                        string='Opportunity Type', compute='compute_opportunity_type', store=True)
    technical_file = fields.Many2many('ir.attachment', 'techincal_other_rel', string="Technical Document",
                                      store=True,)

    scope_file = fields.Binary("Requirement Document", attachment=False)
    scope_file_name = fields.Char("Requirement Document")
    reason_for_reject=fields.Text('Reason For Reject')
    attachment_tracking_ids=fields.One2many('attachment.tracking','crm_document_tracking_id')

    tech_file = fields.Binary("Technical Document",)
    technical_file_name = fields.Char("Technical Document")
    pre_sale_request_date = fields.Date(string="Pre Sale Request Date")
    pre_sale_submit_date = fields.Date(string="Pre Sale Submit Date")

    def action_update_technical_file(self):
        return {
            'name': 'Technical Document',
            'type': 'ir.actions.act_window',
            'res_model': 'tech.document.wizard',
            'view_mode': 'form',
            'context': {
                'default_opportunity_id': self.id,
            },
            'target': 'new',
        }

    @api.depends('pre_sale')
    def compute_opportunity_type(self):
        for rec in self:
            if rec.pre_sale:
                rec.opportunity_type = 'pre_sale'
            else:
                rec.opportunity_type = 'normal'

    @api.onchange('stage_id')
    def _onchange_stage(self):
        if self.pre_sale and self.stage_id.pre_sale_alert and self.sale_type_id.pre_sale_users:
            temp_id = self.env.ref('pre_sale.email_template_crm_pre_sales')
            if self.stage_id.probability > self._origin.stage_id.probability:
                ctx = {'email_to': self.pre_sale_users_list(), 'email_cc': self.env.user.company_id.pre_sales_mail and self.sale_type_id.email_cc, 'pre_sale_mail_details': self.pre_sale_mail_details()}
                temp_id.with_context(ctx).send_mail(self.ids[0], force_send=True)
            elif self.stage_id.probability < self._origin.stage_id.probability:
                ctx = {'email_to': self.pre_sale_users_list(), 'email_cc': self.sale_type_id.email_cc}
                temp_id.with_context(ctx).send_mail(self.ids[0], force_send=True)
        if self._origin.stage_id and self.pre_sale and self.stage_id.is_pre_sale and self.stage_id.probability > self._origin.stage_id.probability:
            if self.env.user.id not in self.sale_type_id.pre_sale_users.ids:
                raise UserError(_("You are not allowed to move to the further stage"))
            else:
                pass
        if self.stage_id.reponsible_user and self.env.user.id not in self.stage_id.reponsible_user.ids:
            raise UserError(_("You are not allowed to move to the further stage"))
        if self.stage_id.is_pre_sale:
            if not self.technical_file:
                raise ValidationError(_('Please Attach Technical Document'))
            if not self.scope_file_id:
                raise ValidationError(_('Please Attach Scope Document'))
        if self.stage_id and not self.pre_sale and (self.stage_id.is_pre_sale or self.stage_id.pre_sale_alert):
            raise UserError(_("You are not allowed to move to this stage as this opportunity is not under pre sale"))

    def pre_sale_users_list(self):
        if self.sale_type_id and self.sale_type_id.pre_sale_users:
            users_mail = ''
            for user in self.sale_type_id.pre_sale_users:
                if users_mail == '' and user.partner_id.email:
                    users_mail += user.partner_id.email
                    if self.sale_type_id.email_to:
                        users_mail += ','
                        users_mail += self.sale_type_id.email_to

                else:
                    users_mail += ','
                    users_mail += user.partner_id.email
            return users_mail

    def pre_sale_mail_details(self):
        details = []
        no = 1
        if self.partner_id:
            customer = {'no': no, 'name': 'Customer:', 'value': self.partner_id.name}
            details.append(customer)
            no += 1
        if self.contact_name:
            contact = {'no': no, 'name': 'Customer Contact Name:', 'value': self.contact_name}
            details.append(contact)
            no += 1
        if self.phone:
            phone = {'no': no, 'name': 'Contact Details:', 'value': self.phone}
            details.append(phone)
            no += 1
        address_parts = []
        if self.street:
            address_parts.append(self.street)
        if self.street2:
            address_parts.append(self.street2)
        if self.city:
            address_parts.append(self.city)
        if self.state_id:
            address_parts.append(self.state_id.name)
        if self.zip:
            address_parts.append(self.zip)
        if self.country_id:
            address_parts.append(self.country_id.name)

        if address_parts:
            address = {'no': no, 'name': 'Customer Address:', 'value': ', '.join(address_parts)}
            details.append(address)
            no += 1

        if self.name:
            opporunity = {'no': no, 'name': 'Need or Exact Requirement:', 'value': self.name}
            details.append(opporunity)
            no += 1
        if self.date_deadline:
            timeline = {'no': no, 'name': 'Customer provided Timeline if any:', 'value': self.date_deadline.strftime('%d-%m-%Y')}
            details.append(timeline)
            no += 1
        if self.budget:
            timeline = {'no': no, 'name': 'Budget:', 'value': self.budget_text}
            details.append(timeline)
            no += 1
        if self.need:
            timeline = {'no': no, 'name': 'Need:', 'value': self.need_text}
            details.append(timeline)
            no += 1
        if self.time_lead:
            timeline = {'no': no, 'name': 'Time Lead', 'value': self.time_lead}
            details.append(timeline)
            no += 1
        if self.authority:
            timeline = {'no': no, 'name': 'Authority', 'value': self.authority_text}
            details.append(timeline)
            no += 1
        print("--------", details,"----details---\n")
        return details

    def action_generate_daily_report(self):
        """Generate and download the Excel report directly."""
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
        leads = self.env['crm.lead'].search([('create_date', '>=', fields.Date.today())])

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

        # Convert to base64
        file_data = base64.b64encode(output.getvalue())

        # Create an attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'CRM_Daily_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'CRM_Daily_Report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_generate_monthly_report(self):
        """Generate and download the Excel report for the monthly CRM report."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Monthly CRM Report')

        # Define styles
        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        normal = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'border': 1})

        # Define headers
        headers = [
            "Sl No", "Opportunity Created Date", "BDM", "Customer Name", "Opportunity",
            "Pre Sale Request Date", "Pre Sale Submit Date", "Stage", "PO Date", "PO Value"
        ]

        # Write headers
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        # Fetch CRM leads for the current month
        start_date = fields.Date.today().replace(day=1)  # First day of the month
        leads = self.env['crm.lead'].search([('create_date', '>=', start_date)])

        row = 1
        for index, lead in enumerate(leads, start=1):
            po_date = ''
            po_value = ''

            # If the lead is won, fetch purchase order details
            if lead.stage_id.name == 'Won':
                purchase_order = self.env['purchase.order'].search([('origin', '=', lead.name)], limit=1)
                if purchase_order:
                    po_date = purchase_order.date_order.strftime('%Y-%m-%d') if purchase_order.date_order else ''
                    po_value = purchase_order.name  # PO Name

            # Write data to the sheet
            sheet.write(row, 0, index, normal)  # Sl No
            sheet.write(row, 1, str(lead.create_date) if lead.create_date else '', normal)  # Created Date
            sheet.write(row, 2, lead.user_id.name or '', normal)  # BDM
            sheet.write(row, 3, lead.partner_id.name or '', normal)  # Customer Name
            sheet.write(row, 4, lead.name, normal)  # Opportunity
            sheet.write(row, 5, str(lead.pre_sale_request_date) if lead.pre_sale_request_date else '', normal)  # Request Date
            sheet.write(row, 6, str(lead.pre_sale_submit_date) if lead.pre_sale_submit_date else '', normal)  # Submit Date
            sheet.write(row, 7, lead.stage_id.name or '', normal)  # Stage
            sheet.write(row, 8, po_date, normal)  # PO Date
            sheet.write(row, 9, po_value, normal)  # PO Value (PO Name)
            row += 1

        workbook.close()
        output.seek(0)

        # Convert to base64
        file_data = base64.b64encode(output.getvalue())

        # Create an attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'CRM_Monthly_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'CRM_Monthly_Report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pre_sales_mail = fields.Char(string="Pre Sales Mail",readonly=False, related='company_id.pre_sales_mail', store=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    pre_sales_mail = fields.Char(string="Pre Sales Mail")


class AttachmentTracking(models.Model):
    _name = 'attachment.tracking'

    crm_document_tracking_id = fields.Many2one('crm.lead')
    name = fields.Char('Name')
    date = fields.Datetime('Date', default=fields.Datetime.now)
    document_attachment = fields.Many2many('ir.attachment', string='Document Attachment')








