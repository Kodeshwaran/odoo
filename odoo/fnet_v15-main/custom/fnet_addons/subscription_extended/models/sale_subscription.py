# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    work_location_id = fields.Many2one('hr.work.location', string="Work Location", readonly=False)
    contract_document = fields.Many2many('ir.attachment', string="Contract Document")

    def _prepare_renewal_order_values(self, discard_product_ids=False, new_line_ids=False):
        res = super(SaleSubscription, self)._prepare_renewal_order_values()
        for subscription in self:
            payment_term = self.env['account.payment.term'].search([('is_default_invoice', '=', True)], limit=1)
            res[subscription.id].update({'sale_type_id':subscription.sale_type_id.id, 'sale_sub_type_id': subscription.sales_sub_types.id,
                                         'subscription_id': subscription.id, 'payment_term_id': payment_term.id if payment_term else False,
                                         'subscription_product': True, 'subscription_template': subscription.template_id.id})
        return res

    def _recurring_create_invoice(self, automatic=False, batch_size=20):
        res = super(SaleSubscription, self)._recurring_create_invoice(automatic, batch_size)
        if res:
            for rec in res:
                subscription = rec.invoice_line_ids.mapped('subscription_id')
                current_date = datetime.today().date()
                sale_order = self.env['sale.order.line'].search([('order_id.state', '=', 'sale'), ('subscription_id', '=', subscription.id),
                                                                 ('order_id.contract_start_date', '<=', current_date), ('order_id.contract_end_date', '>=', current_date)], limit=1).mapped('order_id')
                if sale_order:
                    for line in sale_order.order_line:
                        invoice_line = rec.invoice_line_ids.filtered(lambda x: x.product_id.id == line.product_id.id)
                        line.invoice_lines = invoice_line.ids
        return res

    def _prepare_invoice_data(self):
        res = super(SaleSubscription, self)._prepare_invoice_data()
        res['sale_type_id'] = self.sale_type_id.id
        res['sales_sub_types'] = self.sales_sub_types.id
        return res

    def prepare_renewal_order(self):
        self.write({'renewal_done': True})
        if self.contract_document:
            for doc in self.contract_document:
                copy_doc = doc.copy({'name': 'Old - ' + doc.name})
            self.contract_document = False
            self.write({'contract_status': 'waiting'})
        return super(SaleSubscription, self).prepare_renewal_order()

    date_start = fields.Date(string="Start Date")
    date = fields.Date(string="End Date")
    template_id = fields.Many2one('sale.subscription.template', string="Subscription Template")
    renewal_done = fields.Boolean(string="Renewed", default=False)
    renewal_days_type = fields.Many2one('renewal.days', string="Type", required=True)
    number_of_days = fields.Integer(string="Days")
    invoice_ids = fields.Many2many('account.move',string="Invoice ID")
    invoice_sub_count = fields.Integer(string="invoice count")
    sale_type_id = fields.Many2one('sale.type', string="Sale Type", required=True)
    sales_sub_types = fields.Many2one('sale.type.line', string="Sale Sub Type")
    rims_sub_types = fields.Many2one('sale.type.line', string="Rims Sub Type")
    rims_type_id = fields.Many2one('sale.type', string="RIMS Type", required=True)
    contract_status = fields.Selection([('waiting', 'Waiting for Document'), ('received', 'Document Received')])

    @api.onchange('contract_document')
    def onchange_contract_document(self):
        if self.contract_document:
            self.write({'contract_status': 'received'})
        else:
            self.write({'contract_status': 'waiting'})

    @api.model
    def _check_subscription_expiry(self):
        current_date = datetime.now().date()
        recs = self.env['sale.subscription'].sudo().search([('stage_id', '=', 'In Progress')])
        alert_date_head = current_date + timedelta(days=25)
        alert_date_md = current_date + timedelta(days=23)
        for rec in recs:
            if rec.number_of_days > 0:
                tot_days = rec.number_of_days
            else:
                tot_days = rec.renewal_days_type.number_of_days
            alert_date = current_date + timedelta(days=tot_days)
            if not rec.renewal_done and rec.date == alert_date and rec.renewal_days_type.alert_person:
                temp_id = self.env.ref('subscription_extended.email_template_subscription_expiry_alert_mail').id
                ctx = {'email_to': [user.login for user in rec.renewal_days_type.alert_person]}
                self.env['mail.template'].browse(temp_id).with_context(ctx).send_mail(rec.id, force_send=True)
            if not rec.renewal_done and rec.date == alert_date:
                temp_id = self.env.ref('subscription_extended.email_template_subscription_expiry_alert_sales_person').id
                self.env['mail.template'].browse(temp_id).send_mail(rec.id, force_send=True)
                if rec.number_of_days == 0:
                    rec.number_of_days = rec.renewal_days_type.number_of_days - 30
                else:
                    rec.number_of_days = rec.number_of_days - 30

            elif rec.date == alert_date_head and rec.renewal_done == True:
                rec.renewal_done = False

            elif rec.date == alert_date_head and not rec.renewal_done and rec.renewal_days_type.alert_person:
                temp_id = self.env.ref('subscription_extended.email_template_subscription_expiry_alert_mail').id
                ctx = {'email_to': [user.login for user in rec.renewal_days_type.alert_person]}
                self.env['mail.template'].browse(temp_id).with_context(ctx).send_mail(rec.id, force_send=True)

            elif rec.date == alert_date_head and not rec.renewal_done:
                temp_id = self.env.ref('subscription_extended.email_template_subscription_expiry_alert_sales_head').id
                self.env['mail.template'].browse(temp_id).send_mail(rec.id, force_send=True)

            elif rec.date == alert_date_md and rec.renewal_done == True:
                rec.renewal_done = False

            elif rec.date == alert_date_md and not rec.renewal_done and rec.renewal_days_type.alert_person:
                temp_id = self.env.ref('subscription_extended.email_template_subscription_expiry_alert_mail').id
                ctx = {'email_to': [user.login for user in rec.renewal_days_type.alert_person]}
                self.env['mail.template'].browse(temp_id).with_context(ctx).send_mail(rec.id, force_send=True)

            elif rec.date == alert_date_md and not rec.renewal_done:
                temp_id = self.env.ref('subscription_extended.email_template_subscription_expiry_alert_md_accounts').id
                self.env['mail.template'].browse(temp_id).send_mail(rec.id, force_send=True)

            else:
                continue


class RenewalDays(models.Model):
    _name = 'renewal.days'
    _rec_name = 'name'
    _description = "Renewal Days"

    name = fields.Char(string="Name", required=True)
    number_of_days = fields.Integer(string="Renewal Days",required=True,store=True)
    quotation_days = fields.Integer(string="Quotation Days", required=True,store=True)
    alert_person = fields.Many2many('res.users', string="Alert Person")


class SaleSubscriptionLog(models.Model):
    _inherit = 'sale.subscription.log'

    renewal_done = fields.Boolean(string="Renewed", related="subscription_id.renewal_done")
    renewal_days_type = fields.Many2one('renewal.days', string="Type", required=True, related="subscription_id.renewal_days_type")
    number_of_days = fields.Integer(string="Days", related="subscription_id.number_of_days")
    invoice_ids = fields.Many2many('account.move', string="Invoice ID", readonly=True , related="subscription_id.invoice_ids")


class SaleSubscriptionWizard(models.TransientModel):
    _inherit = 'sale.subscription.wizard'

    def create_sale_order(self):
        self = self.with_company(self.subscription_id.company_id)
        fpos = self.env['account.fiscal.position'].get_fiscal_position(
            self.subscription_id.partner_id.id)
        sale_order_obj = self.env['sale.order']
        team = self.env['crm.team']._get_default_team_id(user_id=self.subscription_id.user_id.id)
        new_order_vals = {
            'partner_id': self.subscription_id.partner_id.id,
            'analytic_account_id': self.subscription_id.analytic_account_id.id,
            'team_id': team and team.id,
            'pricelist_id': self.subscription_id.pricelist_id.id,
            'payment_term_id': self.subscription_id.payment_term_id.id,
            'fiscal_position_id': fpos.id,
            'subscription_management': 'upsell',
            'origin': self.subscription_id.code,
            'company_id': self.subscription_id.company_id.id,
            'sale_type_id': self.subscription_id.sale_type_id.id
        }
        # we don't override the default if no payment terms has been set on the customer
        if self.subscription_id.partner_id.property_payment_term_id:
            new_order_vals['payment_term_id'] = self.subscription_id.partner_id.property_payment_term_id.id
        order = sale_order_obj.create(new_order_vals)
        order.message_post(body=(_("This upsell order has been created from the subscription ") + " <a href=# data-oe-model=sale.subscription data-oe-id=%d>%s</a>" % (self.subscription_id.id, self.subscription_id.display_name)))
        for line in self.option_lines:
            self.subscription_id.partial_invoice_line(order, line, date_from=self.date_from)
        order.order_line._compute_tax_id()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": order.id,
        }