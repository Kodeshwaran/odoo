# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime



class PartnerRequest(models.Model):
    _name = 'partner.request'
    _rec_name = 'name'
    _description = 'Partner Creation Request'

    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    partner_id = fields.Many2one('res.partner', string="Partner")
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Waiting for Approval'), ('head_approve', 'BU Head Approved'),
                              ('finance_approve', 'Finance Approved'), ('md_approve', 'MD Approved'), ('cancel', 'Rejected')], string="Status", default='draft', readonly=True)
    name = fields.Char(string="Name of the Customer", required=True)
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state', string="State")
    zip = fields.Char(string="Zip")
    country = fields.Many2one('res.country', string="Country")
    tel_no = fields.Integer(string="Tel No.")
    business_types_lines = fields.One2many('business.types.line', 'request_id', string="Types of Business")
    shareholders_lines = fields.One2many('shareholders.line', 'req_id', string="Major Shareholders")
    sales_turnover = fields.Char(string="Sales Turnover RO")
    employee_count = fields.Integer(string="No of Employees")
    equity_capital = fields.Char(string="Equity Capital RO")
    annual_profit = fields.Char(string="Annual Profit(If Possible) RO")
    debt_cover = fields.Char(string="Debt Cover Ratio")
    bankers = fields.One2many('banker.line', 're_id', string="Bankers")
    head_name = fields.Char(string="Name of GMD/MD/CEO")
    financial_controller = fields.Char(string="Name of Financial Controller")
    payment_contact = fields.Char(string="Name of Person/Designation")
    vendor_list = fields.One2many('vendor.line', 'reqt_id', string="Vendors List")
    hardware_ro = fields.Char(string="Hardware RO")
    software_ro = fields.Char(string="Software RO")
    other_ro = fields.Char(string="Others RO")
    rating_a = fields.Boolean(string="A")
    rating_b = fields.Boolean(string="B")
    rating_c = fields.Text(string="C")
    finance_approved_by = fields.Many2one('res.users', string="Approved By")
    finance_approved_on = fields.Datetime(string="Approved On")
    bu_head_approved_by = fields.Many2one('res.users', string="Approved By")
    bu_head_approved_on = fields.Datetime(string="Approved On")
    partner_count = fields.Integer(string="Customer Count", compute="_compute_partner_count")

    @api.depends('partner_id')
    def _compute_partner_count(self):
        for rec in self:
            if rec.partner_id:
                rec.partner_count = self.env['res.partner'].search_count([('id', '=', rec.partner_id.id)])
            else:
                rec.partner_count = 0

    def view_partner(self):
        return {
            'name': _('Customers'),
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            'res_id': self.partner_id.id,
        }

    def get_request_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url

    def submit(self):
        bu_head_approvers = [user for user in self.env['res.users'].search([]) if user.has_group('partner_creation.group_partner_creation_bu_head')]
        print("--------", bu_head_approvers,"----bu_head_approvers---\n")
        for approver in bu_head_approvers:
            mail_content = "  Dear  " + (
                    approver.name or '') + ",<br>Kindly approve the Customer Creation Request for %s<br/><br/><a href=%s><button>View Customer Request</button></a>" % (self.name, self.get_request_url())
            main_content = {
                'subject': _('Customer Creation Approval'),
                'body_html': mail_content,
                'email_to': approver.login,
            }
            self.env['mail.mail'].sudo().create(main_content).send()
        self.write({'state': 'submit'})

    def first_approve(self):
        self.write({'state': 'head_approve',
                    'bu_head_approved_by': self.env.user.id,
                    'bu_head_approved_on': datetime.now()})
        self.create_customer()

    def second_approve(self):
        self.write({'state': 'finance_approve',
                   'finance_approved_by': self.env.user.id,
                    'finance_approved_on': datetime.now()})

    def third_approve(self):
        self.write({'state': 'md_approve'})

    def cancel(self):
        self.write({'state': 'cancel'})

    def create_customer(self):
        vals = {
            'name': self.name or '',
            'street': self.street or '',
            'street2': self.street2 or '',
            'city': self.city or '',
            'state_id': self.state_id.id or False,
            'zip': self.zip or '',
            'country_id': self.country.id or False,
        }
        partner_creation = self.env['res.partner'].sudo().create(vals)
        self.sudo().write({'partner_id': partner_creation.id})
        self.opportunity_id.write({'partner_id': partner_creation.id})
        return {
            'name': _('Customers'),
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            'res_id': partner_creation.id,
        }

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError('You can only delete the requests in draft state')
        super(PartnerRequest, self).unlink()


class BusinessTypesLine(models.Model):
    _name = 'business.types.line'

    request_id = fields.Many2one('partner.request', string="Request ID")
    business_description = fields.Text()


class ShareholdersLine(models.Model):
    _name = 'shareholders.line'

    req_id = fields.Many2one('partner.request', string="Request ID")
    shareholder_description = fields.Text()


class BankerLine(models.Model):
    _name = 'banker.line'

    re_id = fields.Many2one('partner.request', string="Request ID")
    banker_name = fields.Char(string="Name")


class VendorLine(models.Model):
    _name = 'vendor.line'

    reqt_id = fields.Many2one('partner.request', string="Request ID")
    vendor_name = fields.Char(string="Name")
    tel_no = fields.Integer(string="Tel No")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if not self.env.user.has_group('base.group_partner_manager'):
            raise AccessError(_('You are not allowed to create a partner.You can edit an existing partner'))
        return res

