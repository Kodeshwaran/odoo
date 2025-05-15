# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class ContractConfiguration(models.Model):
    _name = 'contract.configuration'
    _rec_name = 'contract_name'
    _description = "Contract Details"

    contract_name = fields.Char(string="Contract Name", required=True)
    type = fields.Selection([('tos', "TOS"), ('tor', "TOR"),('domain', 'Domain'), ('others', "Others")],
                            string="Type",default='others')
    contract_document = fields.Binary(string='Attachment', store=True, help="Attach the Contract Document")
    file_name = fields.Char(string="File Name")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_subscription_data(self, template):
        res = super(SaleOrder, self)._prepare_subscription_data(template)
        if not self.renewal_type:
            raise ValidationError(_('Select the renewal Type'))
        if not self.contract_start_date or not self.contract_end_date:
            raise ValidationError('Select the Contract Period for the Subscription')
        res.update({'sale_type_id': self.sale_type_id.id if self.sale_type_id else False,
                           'sales_sub_types': self.sale_sub_type_id.id if self.sale_sub_type_id else False,
                           'renewal_days_type': self.renewal_type.id if self.renewal_type else False,
                           'date_start': self.contract_start_date,
                           'recurring_next_date': self.contract_start_date + relativedelta(
                               months=self.subscription_template.recurring_interval) if self.subscription_template.recurring_rule_type == 'monthly' else self.contract_start_date + relativedelta(
                               years=self.subscription_template.recurring_interval),
                           })
        return res

    def create_subscriptions(self):
        res = super(SaleOrder, self).create_subscriptions()
        subscription = self.env['sale.subscription'].sudo().search([('id', 'in', res)])
        if subscription:
            subscription.sudo().write({'date': self.contract_end_date})
        return res

    @api.model
    def _check_sale_quotation(self):
        current_date = datetime.now().date()
        subscriptions = self.env['sale.subscription'].sudo().search([('stage_id', '=', 'In Progress')])
        recs = self.env['sale.order'].search(
            [('order_line.subscription_id', 'in', subscriptions.ids), ('state', 'in', ['draft','sent'])])
        alert_date_head = current_date + timedelta(days=10)
        alert_date_md = current_date + timedelta(days=8)
        for rec in recs:
            if rec.number_of_days > 0:
                tot_days = rec.number_of_days
            else:
                tot_days = rec.order_line.subscription_id.renewal_days_type.quotation_days
            alert_date = current_date + timedelta(days=tot_days)
            if rec.order_line.subscription_id.date == alert_date:
                temp_id = self.env.ref('subscription_extended.email_template_sale_quotation_alert_sales_person').id
                self.env['mail.template'].browse(temp_id).send_mail(rec.id, force_send=True)

            elif rec.order_line.subscription_id.date == alert_date_head:
                temp_id = self.env.ref('subscription_extended.email_template_sale_quotation_alert_sales_head').id
                self.env['mail.template'].browse(temp_id).send_mail(rec.id, force_send=True)

            elif rec.order_line.subscription_id.date == alert_date_md:
                temp_id = self.env.ref('subscription_extended.email_template_sale_quotation_alert_sales_md_accounts').id
                self.env['mail.template'].browse(temp_id).send_mail(rec.id, force_send=True)

            elif rec.order_line.subscription_id.date == current_date:
                temp_id = self.env.ref('subscription_extended.email_template_sale_quotation_alert_sales_md_accounts').id
                self.env['mail.template'].browse(temp_id).send_mail(rec.id, force_send=True)

            else:
                continue

    contract_configuration_type = fields.Many2one('contract.configuration', string="Type")
    subscription_id = fields.Many2one('sale.subscription',string="Subscription ID", store=True)
    type = fields.Selection(related="contract_configuration_type.type")
    subscription_template = fields.Many2one('sale.subscription.template', string="Subscription Template")
    number_of_days = fields.Integer(string="Days")
    body_contract = fields.Text(string="Body of TOS Contract", store=True)
    commercial_content_before = fields.Text(string="Line before Amount", store=True,
                                            help="Text written in this line comes before the total amount under the Commercials Section")
    commercial_content_after = fields.Text(string="Line after Amount", store = True,
                                           help="Text written in this line comes after the total amount under the Commercials Section")
    renewal_type = fields.Many2one('renewal.days', string="Renewal Type")
    is_contract_uploaded = fields.Boolean(string="Is Contract Uploaded")
    contract_reference = fields.Char(string='Contract Reference')
    contact_name = fields.Char(string='Contact Name')
    contract_name = fields.Char(string="Contract Name")
    contract_start_date = fields.Date(string="Contract Start Date")
    month_count = fields.Integer('Month Duration')
    contract_end_date = fields.Date(string="Contract End Date", compute='_compute_month_count', store=True)
    contract_type = fields.Selection([('rims', 'RIMS'), ('onsite', 'On Site')])
    subscription_product = fields.Boolean(string="Subscription", compute='compute_subscription_product', store=True)
    subscription_count = fields.Integer("Subscription Count", compute='_subscription_count')
    partner_type = fields.Selection(related='opportunity_id.partner_type', string="Partner Type")

    @api.depends('month_count', 'contract_end_date', 'contract_start_date')
    def _compute_month_count(self):
        for rec in self:
            if rec.contract_start_date and rec.month_count:
                rec.contract_end_date = rec.contract_start_date + relativedelta(months=rec.month_count)
                rec.contract_end_date -= timedelta(days=1)

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_id.subscription_product')
    def compute_subscription_product(self):
        for rec in self:
            rec.subscription_product = False
            if any(line.product_id.subscription_product for line in rec.order_line):
                rec.subscription_product = True
            else:
                rec.subscription_product = False



    def _subscription_count(self):
        for rec in self:
            count = 0
            count += len(rec.order_line.mapped('subscription_id'))
            rec.subscription_count = count

    def open_subscription(self):
        subscriptions = self.order_line.mapped('subscription_id')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Subscription',
            'view_mode': 'tree,form',
            'res_model': 'sale.subscription',
            'domain': [('id', '=', subscriptions.ids)],
        }

    def _compute_subscription_id(self):
        for rec in self:
            for line in rec.order_line:
                if line.subscription_id:
                    rec.subscription_id = line.subscription_id.id
                else:
                    rec.subscription_id = False

    # @api.onchange('order_line')
    # def _onchange_order_line(self):
    #     subscription_product = []
    #     for line in self.order_line:
    #         if line.subscription_product:
    #             self.subscription_template = line.product_id.subscription_template_id.id if line.product_id.subscription_template_id else False
    #             subscription_product.append(line.product_id.id)
    #         else:
    #             continue
    #     if subscription_product:
    #         self.subscription_product = True
    #     else:
    #         self.subscription_product = False

    def action_create_subscription(self):
        subscription_obj = self.env['sale.subscription']

        subscription = subscription_obj.sudo().create({
            'partner_id': self.partner_id.id or False,
            'date_start': self.date_order or False,
            'date': self.date_order + relativedelta(months=self.subscription_template.recurring_interval) if self.subscription_template.recurring_rule_type == 'monthly' else self.date_order + relativedelta(years=self.subscription_template.recurring_interval),
            'template_id': self.subscription_template.id if self.subscription_template else False,
            'renewal_days_type': self.renewal_type.id if self.renewal_type else False,
            'sale_type_id': self.sale_type_id.id if self.sale_type_id else False,
            'sales_sub_types': self.sale_sub_type_id.id if self.sale_sub_type_id else False,
        })
        # subscription.start_subscription()
        # new_date = subscription._get_recurring_next_date(subscription.recurring_rule_type,
        #                                                  subscription.recurring_interval, subscription.date_start,
        #                                                  subscription.recurring_invoice_day)
        # subscription.update({'date': new_date, 'recurring_next_date': new_date})
        for line in self.order_line.filtered(lambda x: x.subscription_product):
            values = {
                'product_id': line.product_id.id,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'uom_id': line.product_uom.id,
                'analytic_account_id':subscription.id,
            }
            lines = subscription.env['sale.subscription.line']
            lines.create(values)
            line.subscription_id = subscription.id

        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.subscription",
            "views": [[False, "form"]],
            "res_id": subscription.id,
        }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.subscription_id:
            if not self.contract_start_date or not self.contract_end_date:
                raise ValidationError('Kindly provide contract start date and end date')
            if self.contract_start_date and self.contract_end_date:
                recurring_next_date = self.contract_start_date + relativedelta(months=self.subscription_template.recurring_interval) if self.subscription_template.recurring_rule_type == 'monthly' else self.contract_start_date + relativedelta(years=self.subscription_template.recurring_interval)
                self.subscription_id.update({'date_start': self.contract_start_date, 'date': self.contract_end_date,
                                             'recurring_next_date': recurring_next_date})
            for line in self.order_line:
                subscription_line = self.subscription_id.recurring_invoice_line_ids.filtered(lambda x: x.product_id.id == line.product_id.id and x.quantity == line.product_uom_qty)
                for l in subscription_line:
                    l.sudo().update({'price_unit': line.price_unit})
        return res




    # def action_quotation_send(self):
    #     res = super(SaleOrder, self).action_quotation_send()
    #
    #     template = self.env.ref('sale.email_template_edi_sale', False)
    #     pdf1 = self.env.ref('subscription_extended.contract_tos_sale_order_report')._render_qweb_pdf(self.ids)
    #     if self.contract_type.type == 'tos':
    #         b64_pdf = base64.b64encode(pdf1[0])
    #         name = "TOS Contract"
    #     elif self.contract_type.type == 'domain':
    #         pdf2 = base64.b64encode(self.contract_type.contract_document)
    #         b64_pdf = base64.b64decode(pdf2)
    #         name = "Domain Contract"
    #     elif self.contract_type.type == 'tor':
    #         pdf3 = base64.b64encode(self.contract_type.contract_document)
    #         b64_pdf = base64.b64decode(pdf3)
    #         name = "TOR Contract"
    #     else:
    #         template.write({'attachment_ids': False})
    #         return res
    #
    #     attachment_ids=[]
    #
    #     if b64_pdf:
    #         attach_data = {
    #             'name': name,
    #             'type': 'binary',
    #             'res_name': "Sale Order",
    #             'datas':  b64_pdf,
    #             'res_model': 'sale.order',
    #             'res_id': self.id,
    #         }
    #         attach_id = self.env['ir.attachment'].create(attach_data)
    #         attachment_ids.append(attach_id.id)
    #
    #         if attachment_ids:
    #             template.write({'attachment_ids': [(6, 0, attachment_ids)]})
    #     return res

    @api.model
    def check_undelivered_sale_orders(self):
        mail_date = datetime.now().date() - timedelta(days=10)
        close_date = datetime.now().date() - timedelta(days=15)
        sale_lines_all = self.env['sale.order.line'].search([])
        sale_lines = sale_lines_all.filtered(lambda x: x.product_uom_qty > x.qty_delivered)
        sale_orders = self.env['sale.order'].search(
            [('id', 'in', sale_lines.order_id.ids), ('state', '=', 'sale'), ('amount_residual', '>', 0)])
        sale_orders_mail_filtered = sale_orders.filtered(
            lambda x: x.commitment_date.date() == mail_date if x.commitment_date else '')
        sale_orders_close_filtered = sale_orders.filtered(
            lambda x: x.commitment_date.date() == close_date if x.commitment_date else '')
        if sale_orders_mail_filtered:
            for sale in sale_orders_mail_filtered:
                mail_content = "  Dear Team, <br>The Sale Order" + sale.name + \
                               " is 10 days ahead of its expected delivery date."
                main_content = {
                    'subject': _('Exceeding Expected Delivery Date'),
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': sale.user_id.partner_id.email or '' + ',%s' % sale.team_id.user_id.partner_id.email or '' + ',%s' % self.company_id.sale_delivery_alert_mail or '',
                }
                self.env['mail.mail'].create(main_content).send()
        if sale_orders_close_filtered:
            dic_so = []
            for sale in sale_orders_close_filtered:
                dic_so.append({'url': '/mail/view?model=%s&res_id=%s' % ('sale.order', sale.id), 'sale': sale.name})
            ctx = {'records': dic_so}
            template = self.env.ref('subscription_extended.email_template_sale_order_close_alert').id
            self.env['mail.template'].browse(template).with_context(ctx).send_mail(self.id, force_send=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    subscription_product = fields.Boolean(string="Subscription", related="product_id.subscription_product")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_delivery_alert_mail = fields.Char(string="Delivery alert for 10 Days",
                                           readonly=False, related='company_id.sale_delivery_alert_mail', store=True)
    sale_closure_alert_mail = fields.Char(string="Delivery alert for 15 Days",
                                          readonly=False, related='company_id.sale_closure_alert_mail', store=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_delivery_alert_mail = fields.Char(string="Delivery alert for 10 Days")
    sale_closure_alert_mail = fields.Char(string="Delivery alert for 15 Days")