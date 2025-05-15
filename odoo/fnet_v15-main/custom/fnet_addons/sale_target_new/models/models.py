from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import base64
import xlsxwriter


class SaleTypeLines(models.Model):
    _inherit = 'sale.type.line'

    new_customer_target = fields.Float(string='New Customer Target')
    existing_customer_target = fields.Float('Existing Customer Target')
    new_vendor_target_percent = fields.Float('New Vendor Percentage')
    existing_vendor_target_percent = fields.Float('Existing Vendor Percentage')
    new_vendor_target = fields.Float('New Vendor Target', compute='_compute_percentange_calc')
    existing_vendor_target = fields.Float('Existing Vendor Target')
    new_expense_target = fields.Float('New Expense Target')
    existing_expense_target = fields.Float('Existing Expense Target')
    is_no_bill = fields.Boolean("No Bills", help="If selected, the target and margin amount only based on the percentage and not from the vendor bill.")

    @api.onchange('is_no_bill', 'existing_customer_target', 'existing_vendor_target_percent')
    def onchange_vendor_target(self):
        if self.is_no_bill and self.existing_customer_target > 0 and self.existing_vendor_target_percent > 0:
            self.existing_vendor_target = self.existing_customer_target * self.existing_vendor_target_percent
        else:
            self.existing_vendor_target = 0

    @api.depends('new_customer_target', 'existing_customer_target', 'new_vendor_target_percent', 'existing_vendor_target_percent')
    def _compute_percentange_calc(self):
        for rec in self:
            rec.new_vendor_target = rec.new_customer_target - (rec.new_customer_target * rec.new_vendor_target_percent)
            # rec.existing_vendor_target = (rec.existing_customer_target * rec.existing_vendor_target_percent)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    # amount_residual_company = fields.Monetary("Total in Company Currency", compute='_compute_company_amount_residual', store=True, currency_field='company_currency_id')
    amount_residual_company = fields.Monetary("Total in Company Currency")
    amount_total_company = fields.Monetary("Total in Company Currency", compute='_compute_company_amount', store=True, currency_field='company_currency_id')

    def action_send_daily_report(self):
        current_date = fields.Date.today()
        if 1 <= current_date.month < 4:
            date_from = current_date.replace(day=1, month=4) - relativedelta(year=1)
            date_to = current_date
        elif current_date.month == 4 and current_date.day == 1:
            date_from = current_date - relativedelta(year=1)
            date_to = current_date.replace(day=31, month=3)
        else:
            date_from = current_date.replace(day=1, month=4)
            date_to = current_date
        report = self.env['daily.report'].create({
                'date_from': date_from,
                'date_to': date_to,
        })
        report.action_daily_report()
        attachment = report.report_attachment
        # attachment_id = self.env['ir.attachment'].browse(attachment)
        mail_content = "Kindly find the attached Daily Sales report"
        main_content = {
            'subject': _('Daily Sales Report - %s to %s' % (date_from, date_to)),
            'body_html': mail_content,
            'email_to': self.env.company.sales_mail_to,
            'email_cc': self.env.company.sales_mail_cc,
            'attachment_ids': [(6, 0, attachment.ids)]
        }
        self.env['mail.mail'].sudo().create(main_content).send()

    @api.depends('amount_total')
    def _compute_company_amount(self):
        for rec in self:
            if rec.currency_id.id != rec.company_id.currency_id.id:
                rec.amount_total_company = rec.currency_id._convert(rec.amount_total, rec.company_id.currency_id,
                                                                    rec.company_id, rec.date_order or rec.create_date)
            else:
                rec.amount_total_company = rec.amount_total

    @api.depends('amount_residual')
    def _compute_company_amount_residual(self):
        for rec in self:
            if rec.currency_id.id != rec.company_id.currency_id.id:
                rec.amount_residual_company = rec.currency_id._convert(rec.amount_residual, rec.company_id.currency_id,
                                                                    rec.company_id, rec.date_order or rec.create_date)
            else:
                rec.amount_residual_company = rec.amount_residual


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    recurring_total_company = fields.Monetary("Total in Company Currency", compute='_compute_company_recurring_total', store=True,currency_field='company_currency_id')

    @api.depends('recurring_total')
    def _compute_company_recurring_total(self):
        for rec in self:
            if rec.currency_id.id != rec.company_id.currency_id.id:
                rec.recurring_total_company = rec.currency_id._convert(rec.recurring_total, rec.company_id.currency_id,
                                                                    rec.company_id, rec.date_start or rec.create_date)
            else:
                rec.recurring_total_company = rec.recurring_total


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_type_id = fields.Many2one('sale.type', 'Sale Type')
    sales_sub_types = fields.Many2one('sale.type.line', string="Sale Sub Types")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    amount_total_company = fields.Monetary("Total in Company Currency", compute='_compute_company_amount', store=True, currency_field='company_currency_id')

    @api.depends('amount_total')
    def _compute_company_amount(self):
        for rec in self:
            if rec.currency_id.id != rec.company_id.currency_id.id:
                rec.amount_total_company = rec.currency_id._convert(rec.amount_untaxed, rec.company_id.currency_id,
                                                                    rec.company_id, rec.date_order or rec.create_date)
            else:
                rec.amount_total_company = rec.amount_untaxed


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sale_type_id = fields.Many2one('sale.type', 'Sale Type')
    sales_sub_types = fields.Many2one('sale.type.line', string="Sale Sub Types", domain="[('type_id', '=', sale_type_id)]")


class AccountMove(models.Model):
    _inherit = 'account.move'

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    amount_total_company = fields.Monetary("Untaxed Total in Company Currency", compute='_compute_company_amount', store=True, currency_field='company_currency_id')
    amount_subtotal_company = fields.Monetary("Untaxed Total in Company Currency", compute='_compute_company_amount', store=True, currency_field='company_currency_id')
    amount_residual_company = fields.Monetary("Due in Company Currency", compute='_compute_company_amount', store=True, currency_field='company_currency_id')
    collection_person = fields.Many2one('res.users', string="Collection Person", default=lambda self: self.env.user)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.collection_person:
                self.collection_person = self.partner_id.collection_person.id

    @api.depends('amount_total', 'amount_untaxed', 'amount_residual')
    def _compute_company_amount(self):
        for rec in self:
            if rec.currency_id.id != rec.company_id.currency_id.id:
                rec.amount_total_company = rec.currency_id._convert(rec.amount_untaxed, rec.company_id.currency_id, rec.company_id, rec.invoice_date or rec.date or rec.create_date)
                rec.amount_subtotal_company = rec.currency_id._convert(rec.amount_total, rec.company_id.currency_id, rec.company_id, rec.invoice_date or rec.date or rec.create_date)
                rec.amount_residual_company = rec.currency_id._convert(rec.amount_residual, rec.company_id.currency_id, rec.company_id, rec.invoice_date or rec.date or rec.create_date)
            else:
                rec.amount_total_company = rec.amount_untaxed
                rec.amount_subtotal_company = rec.amount_total
                rec.amount_residual_company = rec.amount_residual


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_new = fields.Boolean('Is New Customer')
    collection_person = fields.Many2one('res.users', string="Collection Person")


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    email_to = fields.Char('Email To:')
    email_cc = fields.Char('Email CC:')


class ResCompany(models.Model):
    _inherit = 'res.company'

    email_to = fields.Char('Email To:')
    email_cc = fields.Char('Email CC:')


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_hold = fields.Boolean(string="Is Hold")
    is_dropped = fields.Boolean(string="Is Dropped")



