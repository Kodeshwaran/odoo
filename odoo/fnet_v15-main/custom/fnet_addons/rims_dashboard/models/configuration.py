# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import re
from odoo.exceptions import ValidationError


class RimsContractType(models.Model):
    _name = 'rims.contract.type'
    _description = 'Rims Contract Type'
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True)


class ServiceType(models.Model):
    _name = 'service.type'
    _description = 'Service Types'
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True)
    technology_type = fields.Selection([('technology', 'Technology'), ('virtual', 'Virtualization'), ('platform', 'Platform'), ('services', 'Services'),
        ('network', 'Network'), ('storage', 'Storage'), ('isp', 'ISP')], string="Technology")


class EpoType(models.Model):
    _name = 'epo.type'
    _description = 'EPO Types'
    _rec_name = 'name'

    name = fields.Char(string="Name")
    device_category = fields.One2many('device.category', 'epo_id', string="Device Category")
    mt_alert = fields.Boolean("Monitoring Thresholds False Alert")


class DeviceCategory(models.Model):
    _name = 'device.category'

    epo_id = fields.Many2one('epo.type', string="EPO")
    name = fields.Char(string="Name")


class RimsEmailTemplates(models.Model):
    _name = 'rims.email.templates'
    _description = 'Rims Email Templates'

    name = fields.Char(string="Name", required=True)
    content_lines = fields.One2many('template.content.line', 'rims_template_id', string="Mail Content")


class TemplateContentLine(models.Model):
    _name = 'template.content.line'

    rims_template_id = fields.Many2one('rims.email.templates', string='Rims Template')
    name = fields.Char(string="Name", required=True)
    mail_content = fields.Html(string="Mail Content")


class StandardOperatingProcedure(models.Model):
    _name = 'standard.operating.procedure'
    _description = 'Standard Operating Procedure'

    name = fields.Char('Name', required=True)
    sop_document = fields.Binary(string="SOP Document")
    sop_document_filename = fields.Char('SOP Filename', size=64, readonly=True)


class RimsServiceCategory(models.Model):
    _name = 'rims.service.category'
    _description = 'Service Category'

    name = fields.Char(string='Name', required=True)
    service_lines = fields.One2many('rims.service.category.line', 'category_id', string="Service Lines", copy=False)


class RimsServiceCategoryLines(models.Model):
    _name = 'rims.service.category.line'
    _description = 'Service Lines'

    category_id = fields.Many2one('rims.service.category', string="Category")
    name = fields.Char(string='Service Name')







class ContractExpiryCompany(models.Model):
    _name = 'contract.expiry.company.line'
    _description = 'Contract Expiry Alert Mail'

    period = fields.Integer('Alert Days For Contract Expiry')
    period_type = fields.Selection([('after', 'After'), ('before', 'Before')], required=True, default="after")
    to_emails = fields.Char(string="To Email Ids")
    cc_emails = fields.Char(string="CC Email Ids")

    @api.onchange('cc_emails')
    def _onchange_cc_emails(self):
        if self.cc_emails:
            self.cc_emails = re.sub(r'\s+', ',', self.cc_emails)
            self.cc_emails = re.sub(r',{2,}', ',', self.cc_emails)

    @api.constrains('cc_emails')
    def _check_cc_emails(self):
        for record in self:
            if record.cc_emails:
                emails = record.cc_emails.split(',')
                for email in emails:
                    if not self._validate_email(email.strip()):
                        raise exceptions.ValidationError("Invalid email format: %s" % email)

    @api.onchange('to_emails')
    def _onchange_to_emails(self):
        if self.to_emails:
            self.to_emails = re.sub(r'\s+', ',', self.to_emails)
            self.to_emails = re.sub(r',{2,}', ',', self.to_emails)

    @api.constrains('to_emails')
    def _check_to_emails(self):
        for record in self:
            if record.to_emails:
                emails = record.to_emails.split(',')
                for email in emails:
                    if not self._validate_email(email.strip()):
                        raise exceptions.ValidationError("Invalid email format: %s" % email)

    def _validate_email(self, email):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email)


class SupportDetailsAlertLine(models.Model):
    _name = 'support.details.alert.line'

    period = fields.Integer('Subscription End date Alert Days')
    to_emails = fields.Char(string="To Email Ids")
    cc_emails = fields.Char(string="CC Email Ids")

    @api.onchange('cc_emails')
    def _onchange_cc_emails(self):
        if self.cc_emails:
            self.cc_emails = re.sub(r'\s+', ',', self.cc_emails)
            self.cc_emails = re.sub(r',{2,}', ',', self.cc_emails)

    @api.constrains('cc_emails')
    def _check_cc_emails(self):
        for record in self:
            if record.cc_emails:
                emails = record.cc_emails.split(',')
                for email in emails:
                    if not self._validate_email(email.strip()):
                        raise exceptions.ValidationError("Invalid email format: %s" % email)

    @api.onchange('to_emails')
    def _onchange_to_emails(self):
        if self.to_emails:
            self.to_emails = re.sub(r'\s+', ',', self.to_emails)
            self.to_emails = re.sub(r',{2,}', ',', self.to_emails)

    @api.constrains('to_emails')
    def _check_to_emails(self):
        for record in self:
            if record.to_emails:
                emails = record.to_emails.split(',')
                for email in emails:
                    if not self._validate_email(email.strip()):
                        raise exceptions.ValidationError("Invalid email format: %s" % email)

    def _validate_email(self, email):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email)

class DocumentAlertLine(models.Model):
    _name = 'document.alert.line'

    period = fields.Integer('Contract Document Alert Days')
    repeated_mail = fields.Boolean("Repeated Mail")
    to_emails = fields.Char(string="To Email Ids")
    cc_emails = fields.Char(string="CC Email Ids")

    @api.constrains('repeated_mail')
    def _check_repeated_mail(self):
        records = self.search_count([('repeated_mail', '=', True)])
        if records > 1:
            raise ValidationError("You can only set one Repeated Mail field as true, and one has already been set")

    @api.onchange('cc_emails')
    def _onchange_cc_emails(self):
        if self.cc_emails:
            self.cc_emails = re.sub(r'\s+', ',', self.cc_emails)
            self.cc_emails = re.sub(r',{2,}', ',', self.cc_emails)

    @api.constrains('cc_emails')
    def _check_cc_emails(self):
        for record in self:
            if record.cc_emails:
                emails = record.cc_emails.split(',')
                for email in emails:
                    if not self._validate_email(email.strip()):
                        raise exceptions.ValidationError("Invalid email format: %s" % email)

    @api.onchange('to_emails')
    def _onchange_to_emails(self):
        if self.to_emails:
            self.to_emails = re.sub(r'\s+', ',', self.to_emails)
            self.to_emails = re.sub(r',{2,}', ',', self.to_emails)

    @api.constrains('to_emails')
    def _check_to_emails(self):
        for record in self:
            if record.to_emails:
                emails = record.to_emails.split(',')
                for email in emails:
                    if not self._validate_email(email.strip()):
                        raise exceptions.ValidationError("Invalid email format: %s" % email)

    def _validate_email(self, email):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email)


