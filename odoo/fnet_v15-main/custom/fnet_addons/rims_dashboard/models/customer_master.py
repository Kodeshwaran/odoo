# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import re
from dateutil.relativedelta import relativedelta


class CustomerMaster(models.Model):
    _name = 'rims.customer.master'
    _inherit = 'mail.thread'
    _description = 'Rims Customer Master'
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True)
    contract_start_date = fields.Date(string="Contract Start Date")
    contract_end_date = fields.Date(string="Contract End Date")
    street = fields.Char(string='Address(H.O)')
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    service_code = fields.Char(string="Service Code")
    rims_scope = fields.Char(string="RIMS Scope")
    contract_type = fields.Many2one('rims.contract.type', string="Contract Type")

    epo_count = fields.Integer(string="Current EPO's Count", compute="compute_epo_count")
    first_epo_count = fields.Integer(string="EPO's Count as per the Contract")

    contract_document = fields.Many2many('ir.attachment', string="Contract Document")
    # contract_document_filename = fields.Char(string='Contract Filename', size=64, readonly=True)
    customer_matrix = fields.One2many('customer.matrix.line', 'customer_id')
    escalation_matrix = fields.One2many('escalation.matrix.line', 'customer_id')
    monitoring_details = fields.One2many('monitoring.details', 'customer_id')
    tool_name = fields.Char(string="Monitor Tool")
    tool_version = fields.Char(string="Monitor Tool Version")
    monitoring_ip_address = fields.Char(string="Monitoring IP")
    environment_access = fields.Char(string="Customer Environment Access")
    monitoring_alert_members = fields.One2many('monitoring.alert.members', 'customer_id')
    report_members = fields.One2many('report.members', 'customer_id', string='Report Members', copy=False)
    vendor_details = fields.One2many('vendor.details', 'customer_id', string="Vendor Details", copy=False)
    # report_member_daily = fields.One2many('report.members', 'customer_id', string='Report Members Daily',
    #                                       domain=[('report_type', '=', 'daily')], copy=True)
    technology_supported = fields.One2many('technology.landscape.line', 'customer_id')
    epo_details = fields.One2many('epo.details', 'customer_id', string="EPO Details")
    support_details = fields.One2many('support.details', 'customer_id', string="Support Subscription")
    epo_supported = fields.One2many('epo.supported', 'customer_id', string="EPO Supported",
                                    compute="compute_epo_supported")
    monitoring_thresholds_ids = fields.One2many('monitoring.thresholds', 'customer_id', string="Monitoring Thresholds",
                                                tracking=True)
    subscription_id = fields.Many2one('sale.subscription', string="Subscription ID")
    date_start = fields.Date(related='subscription_id.date_start', string="Subscription Start Date")
    date_end = fields.Date(related='subscription_id.date', string="Subscription End Date")
    template_id = fields.Many2one('sale.subscription.template', string='Subscription Template',
                                  related='subscription_id.template_id')
    warning = fields.Boolean("Warning", compute='_compute_red', store=True)
    warning_name = fields.Char(string="Warning", compute='_compute_name',
        help=( "Warning Details:\n"
            "CD - contract document is not updated,\n"
            "Lv1 - in Escalation Matrix lv1 is not mapped,\n"
            "Lv2 - in Escalation Matrix lv2 is not mapped,\n"
            "MT - monitoring thresholds are not updated,\n"
            "SS - Support Subscription is not updated." ))

    invoice_count = fields.Char("Invoice Status", compute='_compute_invoice_count')
    doc_false_cron_date = fields.Date("doc_false_cron_date")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    def _compute_invoice_count(self):
        for customer in self:
            subscription = customer.subscription_id
            if subscription and subscription.date_start and subscription.date:
                date_start = fields.Date.from_string(subscription.date_start)
                date_end = fields.Date.from_string(subscription.date)
                recurring_rule_type = subscription.template_id.recurring_rule_type
                recurring_interval = subscription.template_id.recurring_interval

                interval_count = self._calculate_intervals(date_start, date_end, recurring_rule_type,
                                                           recurring_interval)

                invoice_domain = [
                    ('subscription_id', '=', subscription.id),
                    ('move_id.invoice_date', '>=', subscription.date_start),
                    ('move_id.invoice_date', '<=', subscription.date)
                ]


                invoice_count = self.env['account.move.line'].search(invoice_domain).mapped('move_id')

                customer.invoice_count = f"{len(invoice_count)}/{interval_count}"
            else:
                customer.invoice_count = '0/0'

    def _calculate_intervals(self, start_date, end_date, rule_type, interval):
        if rule_type == 'daily':
            delta = timedelta(days=interval)
        elif rule_type == 'weekly':
            delta = timedelta(weeks=interval)
        elif rule_type == 'monthly':
            delta = relativedelta(months=interval)
        elif rule_type == 'yearly':
            delta = relativedelta(years=interval)
        else:
            delta = timedelta(days=0)

        count = 0
        current_date = start_date
        while current_date <= end_date:
            count += 1
            current_date += delta
        return count

    @api.onchange('monitoring_thresholds_ids')
    def onchange_monitoring_thresholds(self):
        for rec in self:
            if rec.monitoring_thresholds_ids:
                for record in rec.monitoring_thresholds_ids:
                    record.ip_address = record.host_id.ip_address

    @api.depends('escalation_matrix', 'support_details')
    def _compute_red(self):
        for record in self:
            if record.escalation_matrix:
                levels = record.escalation_matrix.mapped('level')
                if 'lv1' not in levels or 'lv2' not in levels:
                    record.warning = True
                else:
                    record.warning = False

            if not record.support_details:
                record.warning = True

            else:
                record.warning = False


    @api.depends('escalation_matrix', 'support_details', 'monitoring_thresholds_ids', 'contract_document')
    def _compute_name(self):
        for record in self:
            warning_parts = []
            if not record.contract_document:
                warning_parts.append("CD")
            if record.escalation_matrix:
                levels = record.escalation_matrix.mapped('level')
                if 'lv1' not in levels:
                    warning_parts.append("Lv1")
                if 'lv2' not in levels:
                    warning_parts.append("Lv2")
            if not record.monitoring_thresholds_ids:
                warning_parts.append("MT")
            if not record.support_details:
                warning_parts.append("SS")


            record.warning_name = "/ ".join(warning_parts) if warning_parts else False


    def action_open_customer(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'EPO Change Request',
            'view_mode': 'tree,form',
            'res_model': 'epo.change.request',
            'domain': [('customer_id', '=', self.id)],
            'target': 'current'
        }

    def action_open_mt(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Monitoring Thresholds Change Request',
            'view_mode': 'tree,form',
            'res_model': 'mt.change.request',
            'domain': [('customer_id', '=', self.id)],
            'target': 'current'
        }

    # @api.model
    # def create(self, vals):
    #     if 'name' in vals:
    #         vals['name'] = ' '.join(word.capitalize() for word in vals['name'].split())
    #     return super(CustomerMaster, self).create(vals)

    @api.depends('epo_details')
    def compute_epo_count(self):
        for rec in self:
            if rec.epo_details:
                rec.epo_count = len(rec.epo_details)
            else:
                rec.epo_count = 0

    @api.depends('epo_details')
    def compute_epo_supported(self):
        for rec in self:
            if rec.epo_supported:
                for line in rec.epo_supported:
                    line.unlink()
            if rec.epo_details:
                epo_types = rec.epo_details.mapped('epo_type_id')
                for type in epo_types:
                    type_lines = rec.epo_details.filtered(lambda x: x.epo_type_id.id == type.id)
                    device_categories = type_lines.mapped('device_category_id').ids
                    vals = {
                        'customer_id': rec.id,
                        'epo_type_id': type.id,
                        'device_category_id': device_categories,
                        'device_qty': len(type_lines)
                    }
                    epo_id = self.env['epo.supported'].create(vals)
            else:
                rec.epo_supported = False

    @api.constrains('monitoring_ip_address')
    def _check_monitoring_ip_address(self):
        ipv4_pattern = r'^\d{1,3}(\.\d{1,3}){3}$'

        for record in self:
            if record.monitoring_ip_address:
                if not re.match(ipv4_pattern, record.monitoring_ip_address):
                    raise ValidationError("Invalid Monitoring IP address format. Please enter a valid IPv4 address.")

    def action_contract_expiry_alert(self):
        master = self.search([])
        if master:
            for rec in master:
                if rec.date_end:
                    today = fields.Date.today()
                    end_date = rec.date_end
                    duration = (today - end_date).days


                days = self.env['contract.expiry.company.line'].search([('period_type', '=', 'before')])
                for record in days:
                    if record.period == duration:
                        customer_name = rec.name
                        days_before_expiry = record.period
                        print("\n---", duration, "--duration--\n")
                        print(today)
                        print(end_date, "\n")

                        mail_body = """
                                        <table border="0" cellpadding="0" cellspacing="0" width="1000"
                                            style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                                            <tr>
                                                <td valign="top" style="padding: 0px 10px;">
                                                    <div style="font-size: 13px; margin: 0px; padding: 0px;">
                                                        Dear Team,
                                                        <br/>
                                                        <br/>
                                                         This is regard to inform you that the <b>{customer_name} {contract_type}</b> contract is going to expire within <b>{days_before_expiry} days</b>.
                                                          Please refer to the details below and take the necessary action immediately.
                                                        <br/>
                                                        <br/>
                                                        <br/>
                                                        Customer Name                 : {customer_name}<br/>
                                                        Contract Type                 : {contract_type}<br/>
                                                        Service Code                  : {service_code}<br/>
                                                        Contract Start Date           : {date_start}<br/>
                                                        Contract End Date             : {date_end}<br/>
                                                        EPO count as per the contract : {first_epo_count}<br/>
                                                        Current EPO count             : {epo_count}<br/>
                                                        <br/>
                                                        <br/>
                                                        Note: This is an auto generated email.
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    """.format(customer_name=customer_name, days_before_expiry=days_before_expiry, contract_type=rec.contract_type.name,
                                                service_code=rec.service_code, date_start= rec.date_start, date_end=rec.date_end,
                                                first_epo_count=rec.first_epo_count, epo_count=rec.epo_count)

                        mail_subject = f"{customer_name}'s Contract Expiry Alert"
                        to_email = record.to_emails
                        cc_email = record.cc_emails

                        self.env['mail.mail'].create({
                            'subject': mail_subject,
                            'email_to': to_email,
                            'email_cc': cc_email,
                            'body_html': mail_body,
                        }).send()

    def action_subscription_expiry_alert(self):
        master = self.search([])
        days = self.env['support.details.alert.line'].search([])
        if master:
            for record in master:
                if record.support_details:
                    for line in record.support_details:
                        start_date = fields.Date.today()
                        if line.end_date:
                            end_date = line.end_date
                            duration = (start_date - end_date).days
                            if days:
                                for rec in days:
                                    if rec.period == duration:
                                        customer_name = record.name
                                        days_before_expiry = rec.period
                                        mail_body = """
                                                        <table border="0" cellpadding="0" cellspacing="0" width="1000"
                                                            style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                                                            <tr>
                                                                <td valign="top" style="padding: 0px 10px;">
                                                                    <div style="font-size: 13px; margin: 0px; padding: 0px;">
                                                                        Dear Team,
                                                                        <br/>
                                                                        <br/>
                                                                          This is regard to inform you that the <b>{customer_name} {category}</b> Subscription is going to expire within {days_before_expiry} days.
                                                                           Please refer to the details below and take the necessary actions immediately.
                                                                        <br/>
                                                                        <br/>
                                                                        <br/>
                                                                        Category                   : {category}<br/>
                                                                        IP Address                 : {ip_address}<br/>
                                                                        Serial No                  : {serial_no}<br/>
                                                                        Type                       : {type}<br/>
                                                                        Sub Start Date             : {start_date}<br/>
                                                                        Sub End Date               : {end_date}<br/>
                                                                        Description                : {description}<br/>
                                                                        <br/>
                                                                        <br/>
                                                                        Note: This is an auto generated email.
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        </table>
                                                    """.format(customer_name=customer_name,
                                                               days_before_expiry=days_before_expiry, ip_address=line.ip_address, category=line.category,
                                                    serial_no=line.serial_no, type= line.type, start_date=line.start_date,
                                                    end_date=line.end_date, description=line.description)

                                        mail_subject = "Subscription End date Alert"
                                        to_email = rec.to_emails
                                        cc_email = rec.cc_emails

                                        self.env['mail.mail'].create({
                                            'subject': mail_subject,
                                            'email_to': to_email,
                                            'email_cc': cc_email,
                                            'body_html': mail_body,
                                        }).send()

    def action_attachment_false_alert(self):
        master_records = self.search([('contract_document', '=', False),('doc_false_cron_date', '=', False)])
        days = self.env['document.alert.line'].search([('repeated_mail', '=', False)])
        for rec in master_records:
            today = fields.Date.today()
            for line in days:
                if rec.date_start and line.period:
                    after_start_date = rec.date_start + timedelta(days=line.period)
                    if today == after_start_date:
                        rec.doc_false_cron_date = today
                        self.action_attachment_false_alert_mail(rec.name, rec.contract_type.name, rec.service_code,
                                                               rec.date_start, rec.date_end, rec.subscription_id.name, line.to_emails, line.cc_emails)
        master_records = self.search([('contract_document', '=', False), ('doc_false_cron_date', '!=', False)])
        days = self.env['document.alert.line'].search([('repeated_mail', '=', True)])
        for rec in master_records:
            for line in days:
                if line.period:
                    after_start_date = rec.doc_false_cron_date + timedelta(days=line.period)
                    if fields.Date.today() == after_start_date:
                        rec.doc_false_cron_date = fields.Date.today()
                        self.action_attachment_false_alert_mail(rec.name, rec.contract_type.name, rec.service_code,
                                                           rec.date_start, rec.date_end,
                                                           rec.subscription_id.name, line.to_emails, line.cc_emails)

    def action_attachment_false_alert_mail(self, customer_name, contract_type, service_code, date_start, date_end, subscription_id, to_emails, cc_emails):
        mail_body = """
                    <table border="0" cellpadding="0" cellspacing="0" width="1000"
                        style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                        <tr>
                            <td valign="top" style="padding: 0px 10px;">
                                <div style="font-size: 13px; margin: 0px; padding: 0px;">
                                    Dear Team,
                                    <br/>
                                    <br/>
                                    This is regard to reminder you to update the <b>{customer_name} {contract_type}</b> Contract Document in the {subscription_id}.
                                     Please refer to the details below and do the needful immediately.
                                    <br/>
                                    <br/>
                                    <br/>
                                    Customer Name                 : {customer_name}<br/>
                                    Contract Type                 : {contract_type}<br/>
                                    Service Code                  : {service_code}<br/>
                                    Contract Start Date           : {date_start}<br/>
                                    Contract End Date             : {date_end}<br/>
                                    <br/>
                                    <br/>
                                    Note: This is an auto generated email.   
                                </div>
                            </td>
                        </tr>
                    </table>
                """.format(customer_name=customer_name, contract_type=contract_type,
                           service_code=service_code, date_start=date_start, date_end=date_end,
                           subscription_id=subscription_id)

        mail_subject = "Contract Document Alert"
        to_email = to_emails
        cc_email = cc_emails

        self.env['mail.mail'].create({
            'subject': mail_subject,
            'email_to': to_email,
            'email_cc': cc_email,
            'body_html': mail_body,
        }).send()

    def action_monitoring_threshold_false_alert(self):
        if self.company_id.is_mt:
            ticket_no = " "
            master_records = self.search([])
            for rec in master_records:
                for epo_line in rec.epo_details.filtered(lambda x: x.epo_type_id.mt_alert):
                    monitoring_id = rec.monitoring_thresholds_ids.search([('host_id', '=', epo_line.id)])
                    if not monitoring_id and fields.Date.today() > epo_line.create_date.date() + timedelta(days=self.company_id.mt_days):
                        request_line_id = self.env['epo.detail.change'].search([('epo_detail_id.customer_id', '=', rec.id), ('device_name_change', '=', epo_line.device_name),('ip_address_epo', '=', epo_line.ip_address)], limit=1)
                        if request_line_id:
                            ticket_no = f"and EPO change request ticket no is {request_line_id.epo_detail_id.ticket_no}"
                        self.action_monitoring_threshold_mail(rec.name, ticket_no, epo_line.device_name,epo_line.ip_address)

    def action_monitoring_threshold_mail(self, customer_name, ticket_no, host_name, ip_address):
        mail_body = f"""
            <table border="0" cellpadding="0" cellspacing="0" width="1000" style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                <tr>
                    <td valign="top" style="padding: 0px 10px;">
                        <div style="font-size: 13px; margin: 0px; padding: 0px;">
                            Dear Team,
                            <br/><br/>
                            This is regard to reminder you to update the <b>{customer_name}</b> {ticket_no} recent onboarded EPO’s monitoring threshold is not updated. Please refer to the details below and do the needful immediately.
                            <br/><br/>
                            <table style="width:100%;">
                                <tr>
                                    <td style="width: 200px; border: 1px solid #000;">S.no</td>
                                    <td style="width: 200px; border: 1px solid #000;">Host Name</td>
                                    <td style="width: 200px; border: 1px solid #000;">IP Address</td>
                                </tr>
                                <tr>
                                    <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">1</td>
                                    <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{host_name}</td>
                                    <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{ip_address}</td>
                                </tr>
                            </table>
                            <br/>
                            <br/>
                            Note: This is an auto generated email.
                        </div>
                    </td>
                </tr>
            </table>
        """

        mail_subject = "Monitoring Threshold Alert"
        to_email = self.company_id.mt_to_mail
        cc_email = self.company_id.mt_cc_mail

        self.env['mail.mail'].create({
            'subject': mail_subject,
            'email_to': to_email,
            'email_cc': cc_email,
            'body_html': mail_body,
        }).send()


    def action_after_contract_expiry_alert(self):
        master = self.search([])
        if master:
            for rec in master:
                if rec.date_end:
                    today = fields.Date.today()
                    end_date = rec.date_end
                    total = (end_date - today).days

                days = self.env['contract.expiry.company.line'].search([('period_type', '=', 'after')])
                for record in days:
                    if record.period == total:
                        customer_name = rec.name
                        print("\n---", total, "--total--")
                        print(today)
                        print(end_date, "\n")

                        mail_body = """
                                        <table border="0" cellpadding="0" cellspacing="0" width="1000"
                                            style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                                            <tr>
                                                <td valign="top" style="padding: 0px 10px;">
                                                    <div style="font-size: 13px; margin: 0px; padding: 0px;">
                                                        Dear Team,
                                                        <br/>
                                                        <br/>
                                                         This is to remind you that the <b>{customer_name} {contract_type}</b> contract was expired on {date_end}. 
                                                         Please refer to the details below and take the necessary action immediately.
                                                        <br/>
                                                        <br/>
                                                        <br/>
                                                        Customer Name                 : {customer_name}<br/>
                                                        Contract Type                 : {contract_type}<br/>
                                                        Service Code                  : {service_code}<br/>
                                                        Contract Start Date           : {date_start}<br/>
                                                        Contract End Date             : {date_end}<br/>
                                                        EPO count as per the contract : {first_epo_count}<br/>
                                                        Current EPO count             : {epo_count}<br/>
                                                        <br/>
                                                        <br/>
                                                        Note: This is an auto generated email.
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    """.format(customer_name=customer_name, contract_type=rec.contract_type.name,
                                                service_code=rec.service_code, date_start= rec.date_start, date_end=rec.date_end,
                                                first_epo_count=rec.first_epo_count, epo_count=rec.epo_count)

                        mail_subject = f"{customer_name}'s Contract Expiry Alert"
                        to_email = f"{record.to_emails},{rec.subscription_id.user_id.login}"
                        cc_email = record.cc_emails

                        self.env['mail.mail'].create({
                            'subject': mail_subject,
                            'email_to': to_email,
                            'email_cc': cc_email,
                            'body_html': mail_body,
                        }).send()


class CustomerMatrixLine(models.Model):
    _name = 'customer.matrix.line'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    person = fields.Char(string="Designation", required=True)
    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Mail ID", required=True)
    contact_number = fields.Char(string="Contact Number")

    @api.constrains('email')
    def _check_email_format(self):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(pattern, record.email):
                raise ValidationError('Please provide a valid email address.')

    @api.constrains('contact_number')
    def _check_contact_number(self):
        pattern = re.compile(r'^(?:\d{10}|\+\d{2}\s\d{10})$')
        for record in self:
            if record.contact_number:
                if not pattern.match(record.contact_number):
                    raise ValidationError(
                        "Contact Number must be either a 10-digit number or in the format '+XX XXXXXXXXXX'.")


class EscalationMatrixLine(models.Model):
    _name = 'escalation.matrix.line'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    level = fields.Selection([('lv1', 'Level 1'), ('lv2', 'Level 2'), ('lv3', 'Level 3'),
                              ('lv4', 'Level 4'), ('lv5', 'Level 5')], required=True)
    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Mail ID", required=True)
    designation = fields.Char(string="Designation", required=True)
    category_id = fields.Many2one('rims.service.category', string="Category")
    service_id = fields.Many2many('rims.service.category.line', string="Service")
    contact_number = fields.Char(string="Contact Number")
    escalation_time = fields.Char(string="Escalation Time")

    @api.constrains('email')
    def _check_email_format(self):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(pattern, record.email):
                raise ValidationError('Please provide a valid email address.')

    @api.constrains('contact_number')
    def _check_contact_number(self):
        pattern = re.compile(r'^(?:\d{10}|\+\d{2}\s\d{10})$')
        for record in self:
            if record.contact_number:
                if not pattern.match(record.contact_number):
                    raise ValidationError(
                        "Contact Number must be either a 10-digit number or in the format '+XX XXXXXXXXXX'.")


class MonitoringDetails(models.Model):
    _name = 'monitoring.details'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    name = fields.Char(string="Name")
    monitoring_url = fields.Char(string="Monitor URL")


class MonitoringAlertMembers(models.Model):
    _name = 'monitoring.alert.members'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    name = fields.Char(string="Name", required=True)
    mail_type = fields.Selection([('to', 'TO'), ('cc', 'CC')], required=True)
    level = fields.Selection([('lv1', 'Level 1'), ('lv2', 'Level 2'), ('lv3', 'Level 3'),
                              ('lv4', 'Level 4'), ('lv5', 'Level 5')], required=True)
    email = fields.Char(string="Mail", required=True)
    category_id = fields.Many2one('rims.service.category', string="Category", required=True)
    service_id = fields.Many2one('rims.service.category.line', string="Service", required=True)

    @api.constrains('email')
    def _check_email_format(self):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(pattern, record.email):
                raise ValidationError('Please provide a valid email address.')


class ReportMembers(models.Model):
    _name = 'report.members'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    report_type = fields.Selection([('daily', 'Daily'), ('monthly', 'Monthly')], required=True)
    name = fields.Char(string="Name", required=True)
    mail_type = fields.Selection([('to', 'TO'), ('cc', 'CC')], required=True)
    email = fields.Char(string="Mail", required=True)

    @api.constrains('email')
    def _check_email_format(self):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(pattern, record.email):
                raise ValidationError('Please provide a valid email address.')


class VendorDetails(models.Model):
    _name = 'vendor.details'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    category_id = fields.Many2one('rims.service.category', string="Category", required=True)
    service_id = fields.Many2many('rims.service.category.line', string="Service", required=True)
    servers_name = fields.Char(string="Servers", required=True)
    vendor_escalation_matrix = fields.One2many('vendor.escalation.matrix', 'vendor_id', string='Escalation Matrix',
                                               copy=False)


class VendorEscalationMatrix(models.Model):
    _name = 'vendor.escalation.matrix'

    vendor_id = fields.Many2one('vendor.details', string="Vendor")
    escalation_name = fields.Char(string="Name")
    escalation_mail_to = fields.Char(string="TO")
    escalation_mail_cc = fields.Char(string="CC")


class TechnologyLandscapeLine(models.Model):
    _name = 'technology.landscape.line'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    technology_type = fields.Selection(
        [('virtual', 'Virtualization'), ('platform', 'Platform'), ('services', 'Services'),
         ('network', 'Network'), ('storage', 'Storage'), ('isp', 'ISP')])
    service_ids = fields.Many2many('service.type', string="Services")


class EpoDetails(models.Model):
    _name = 'epo.details'
    _rec_name = 'device_name'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    s_no = fields.Char(string="S.NO", compute="_compute_s_no", store=True, readonly=True)
    device_name = fields.Char(string="Device Name")
    # onboarding_date = fields.Datetime("Onboarding Date", index=True, default=fields.Datetime.now, readonly=True)
    ip_address = fields.Char(string="IP Address")
    epo_type_id = fields.Many2one('epo.type', string="EPO Type")
    device_category_id = fields.Many2one('device.category', string="Device Category")
    platform_id = fields.Many2one('service.type', string="Platform")
    technology_id = fields.Many2one('service.type', string="Technology")
    service_id = fields.Many2many('rims.service.category.line', string="Service")
    folder = fields.Char("Folder")
    # serial_no = fields.Char("Serial No", required=True)

    def name_get(self):
        result = []
        for rec in self:
            if rec.device_name and rec.ip_address:
                name = rec.device_name + ' - ' + rec.ip_address
            else:
                name = ''
            result.append((rec.id, name))
        return result

    @api.depends('customer_id.epo_details')
    def _compute_s_no(self):
        for record in self:
            if record.id and record.customer_id:
                record.s_no = str(record.customer_id.epo_details.ids.index(record.id) + 1)
            else:
                record.s_no = False

    @api.constrains('ip_address')
    def _check_ip_address(self):
        ipv4_pattern = r'^\d{1,3}(\.\d{1,3}){3}$'

        for record in self:
            if record.ip_address:
                if not re.match(ipv4_pattern, record.ip_address):
                    raise ValidationError("Invalid IP address format. Please enter a valid IPv4 address.")


class EpoSupportedSummary(models.Model):
    _name = 'epo.supported'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    epo_type_id = fields.Many2one('epo.type', string="EPO Type")
    device_category_id = fields.Many2many('device.category', string="Device Category")
    device_qty = fields.Integer(string='Qty')


class MonitoringThresholds(models.Model):
    _name = 'monitoring.thresholds'

    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    cust_id = fields.Many2one('rims.customer.master', string="Customer")
    host_name = fields.Char(string="Host Name")
    host_id = fields.Many2one('epo.details', string="Host Name")
    ip_address = fields.Char(string="IP Address")
    service = fields.Char(string="Service")
    criticality = fields.Char(string="Criticality")
    memory_capacity = fields.Char()
    memory_warn_percentage = fields.Float()
    memory_crit_percentage = fields.Float()
    cpu_capacity = fields.Char()
    cpu_warn_percentage = fields.Float()
    cpu_crit_percentage = fields.Float()
    disk_capacity = fields.Char()
    disk_warn_percentage = fields.Float()
    disk_crit_percentage = fields.Float()

    def name_get(self):
        result = []
        for rec in self:
            if rec.ip_address and rec.host_id:
                name = rec.host_id.device_name + ' - ' + rec.ip_address
            else:
                name = ''
            result.append((rec.id, name))
        return result

    @api.constrains('ip_address')
    def _check_ip_address(self):
        ipv4_pattern = r'^\d{1,3}(\.\d{1,3}){3}$'

        for record in self:
            if record.ip_address:
                if not re.match(ipv4_pattern, record.ip_address):
                    raise ValidationError("Invalid IP address format. Please enter a valid IPv4 address.")


class SupportDetails(models.Model):
    _name = 'support.details'

    s_no = fields.Char(string="S.NO", compute="_compute_s_no", store=True, readonly=True)
    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    description = fields.Char("Description")
    serial_no = fields.Char("Serial No", required=True)
    start_date = fields.Date("Subs Start", help="Subscription Start Date")
    end_date = fields.Date("Subs End", help="Subscription End Date", required=True)
    account_id_name = fields.Char("Account ID")
    email = fields.Char("Email ID")
    l1_name = fields.Char("L1 Name")
    l1_no = fields.Char("L1 No")
    l2_name = fields.Char("L2 Name")
    l2_no = fields.Char("L2 No")
    l3_name = fields.Char("L3 Name")
    l3_no = fields.Char("L3 No")
    ip_address = fields.Char(string="IP Address", required=True)
    category = fields.Selection([
        ('server', 'Physical Server'), ('storage', 'Storage'), ('switch', 'Switch'),
        ('firewall', 'Firewall'), ('ssl', 'SSL Certificate'), ('dpmain', 'Domain Name'),
        ('licence', 'Software License'), ('isps', 'ISPs')
    ], string="Category", required=True)
    type = fields.Selection([
        ('warranty', 'Warranty'), ('amc', 'AMC'), ('subscription', 'Subscription')
    ], string="Category", required=True)

    @api.constrains('email')
    def _check_email_format(self):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(pattern, record.email):
                raise ValidationError('Please provide a valid email address.')

    @api.depends('customer_id.support_details')
    def _compute_s_no(self):
        for record in self:
            if record.id and record.customer_id:
                record.s_no = str(record.customer_id.support_details.ids.index(record.id) + 1)
            else:
                record.s_no = False

    @api.constrains('l1_no', 'l2_no', 'l3_no')
    def _check_l1_no(self):
        for record in self:
            pattern = re.compile(r'^(?:\d{10}|\+\d{2}\s\d{10})$')
            if record.l1_no:
                if not pattern.match(record.l1_no):
                    raise ValidationError(
                        "Contact Number must be either a 10-digit number or in the format '+XX XXXXXXXXXX'.")
            if record.l2_no:
                if not pattern.match(record.l2_no):
                    raise ValidationError(
                        "Contact Number must be either a 10-digit number or in the format '+XX XXXXXXXXXX'.")
            if record.l3_no:
                if not pattern.match(record.l3_no):
                    raise ValidationError(
                        "Contact Number must be either a 10-digit number or in the format '+XX XXXXXXXXXX'.")

    @api.constrains('ip_address')
    def _check_ip_address(self):
        ipv4_pattern = r'^\d{1,3}(\.\d{1,3}){3}$'

        for record in self:
            if record.ip_address:
                if not re.match(ipv4_pattern, record.ip_address):
                    raise ValidationError("Invalid IP address format. Please enter a valid IPv4 address.")
