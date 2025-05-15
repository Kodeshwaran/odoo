# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class Lead(models.Model):
    _inherit = 'crm.lead'

    opportunity_order_line = fields.One2many('opportunity.order.line', 'lead_id', string='Product Line', copy=True)
    quotation_stage_line = fields.One2many('quotation.stage.line', 'lead_id', string='Quotation Stage Line', copy=True)
    regrets = fields.Text("Reason for Regrets")
    is_mark_bid = fields.Boolean(copy=False)
    predicted_closing_in = fields.Integer('Predicted Closing In', readonly=False, store=True)
    # predicted_closing_in = fields.Integer('Predicted Closing In', compute='_compute_predicted_type_calc', readonly=False, store=True)
    predicted_closing_date = fields.Date('Predicted Closing Date', readonly=False, store=True)
    closing_type = fields.Selection([('week', 'Weeks'), ('month', 'Months'), ('year', 'Years')], default='week')
    potential_amount = fields.Float('Potential Amount', compute='_compute_potential', readonly=False, store=True)
    gross_profit_perc = fields.Float('Gross Margin')
    weighted_amount = fields.Float('Weighted Amount', compute="_compute_weighted", store=True)
    gross_profit_total = fields.Float('Gross Profit Total', compute='_compute_calc_gross', readonly=False, store=True)
    quotation_count_custom = fields.Integer(compute='_compute_quotation_data', string="Number of Quotations")
    customer_po_attachment = fields.Binary('Customer PO')
    bp_code = fields.Char('Business Partner Code', related='partner_id.customer_code')
    contact_person = fields.Many2one('res.partner', 'Contact Person')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.id)
    total_amount_invoiced = fields.Monetary('Total Amount Invoiced', related='partner_id.total_invoiced')
    bp_territory = fields.Many2one('res.country.state', related='partner_id.state_id',
                                   string='Business Partner Territory')
    opportunity_no = fields.Char('Opportunity No.', readonly=True, copy=False)
    quotation_status = fields.Selection(selection=[
        ('draft', "Draft"),
        ('sent', "Quotation Sent"),
        ('sale', "Sales Order"),
        ('done', "Locked"),
        ('cancel', "Cancelled"),
    ], compute='_compute_quotation_data', string='Status')
    enable_quotation = fields.Boolean(copy=False)
    state_revised = fields.Selection([
        ('enquiry_received', 'Enquiry Received'),
        ('awaiting_customer_details', 'Awaiting Detail From Customer'),
        ('sales_quote_prep', 'Sales Quote Preparation'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('quotation_sent', 'Quotation Sent'),
        ('sales_order', 'Sales Order'),
        # ('regret', 'Regret'),
        ('cancelled', 'Cancelled')
    ], compute='compute_set_state', string='CRM Status')
    is_regret = fields.Boolean(copy=False)
    mark_crm_as_sent = fields.Boolean(copy=False)
    manager_comments = fields.Html(copy=False)

    @api.depends('gross_profit_perc')
    def _compute_calc_gross(self):
        for rec in self:
            rec.gross_profit_total = False
            if rec.gross_profit_perc:
                calc_gross_profit = rec.potential_amount * float(rec.gross_profit_perc)
                rec.write({'gross_profit_total': calc_gross_profit})

    @api.onchange('predicted_closing_in', 'closing_type')
    def _onchange_predicted_type_calc(self):
        current_date = fields.Date.today()

        # If predicted_closing_in is set to a non-zero value, calculate the predicted_closing_date
        if self.predicted_closing_in and self.predicted_closing_in != 0:
            if self.closing_type == 'week':
                self.predicted_closing_date = current_date + relativedelta(weeks=self.predicted_closing_in)
            elif self.closing_type == 'month':
                self.predicted_closing_date = current_date + relativedelta(months=self.predicted_closing_in)
            elif self.closing_type == 'year':
                self.predicted_closing_date = current_date + relativedelta(years=self.predicted_closing_in)

        # If predicted_closing_in is 0, allow manual input of predicted_closing_date without auto-calculation
        elif self.predicted_closing_in == 0:
            pass  # User can manually enter the predicted_closing_date

        # If both predicted_closing_in and predicted_closing_date are empty, reset predicted_closing_date
        elif not self.predicted_closing_in and not self.predicted_closing_date:
            self.predicted_closing_date = False

    # @api.onchange('predicted_closing_date')
    # def _onchange_predicted_date_calc(self):
    #     current_date = fields.Date.today()
    #     if self.predicted_closing_date:
    #         delta = relativedelta(self.predicted_closing_date, current_date)
    #         days_difference = (self.predicted_closing_date - current_date).days
    #         if days_difference <= 7:
    #             self.closing_type = 'week'
    #             self.predicted_closing_in = days_difference / 7
    #         elif delta.years == 0:
    #             self.closing_type = 'month'
    #             self.predicted_closing_in = delta.years * 12 + delta.months
    #         else:
    #             self.closing_type = 'year'
    #             self.predicted_closing_in = delta.years
    #     else:
    #         self.predicted_closing_in = 0
    #         self.closing_type = False

    def compute_set_state(self):
        for rec in self:
            created_quote = rec.env['sale.order'].search(
                [('opportunity_id', '=', rec.id), ('state', 'not in', ['cancel'])], limit=1)
            rec.state_revised = 'enquiry_received'

            if rec.mark_crm_as_sent:
                rec.write({'state_revised': 'awaiting_customer_details', 'probability': 10})
            if rec.is_mark_bid:
                rec.write({'state_revised': 'sales_quote_prep', 'probability': 10})
            if rec.enable_quotation or (rec.state_revised not in ['enquiry_received', 'awaiting_customer_details',
                                                                  'sales_quote_prep'] and rec.quotation_count_custom == 0):
                rec.write({'state_revised': 'sales_quote_prep', 'probability': 50})
            if created_quote and created_quote.send_approval_pricing:
                rec.write({'state_revised': 'waiting_for_approval', 'probability': 65})
            if created_quote and created_quote.approval_state == 'approved' and created_quote.state == 'sent':
                rec.write({'state_revised': 'approved', 'probability': 85})
            if created_quote and created_quote.show_quote_sent_stage:
                rec.write({'state_revised': 'quotation_sent', 'probability': 95})
            if created_quote and created_quote.state == 'sale':
                rec.write({'state_revised': 'sales_order', 'probability': 95})
            if rec.is_regret:
                rec.write({'state_revised': 'cancelled', 'probability': 0})

    @api.model
    def create(self, vals):
        if vals.get('opportunity_no', _('New')) == _('New'):
            vals['opportunity_no'] = self.env['ir.sequence'].next_by_code('crm.lead') or _('New')
        return super(Lead, self).create(vals)

    @api.onchange('partner_id')
    def onchange_partner_contact(self):
        self.contact_person = False
        if self.partner_id:
            contacts = self.partner_id.child_ids.filtered(lambda x: x.type == 'contact')
            if contacts:
                self.contact_person = contacts[0].id
            return {'domain': {'contact_person': [('id', 'in', contacts.ids)]}}

    def action_opportunity_send(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        # self.order_line._validate_analytic_distribution()
        lang = self.env.context.get('lang')
        mail_template = self._find_mail_template()
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'crm.lead',
            'default_res_id': self.id,
            'default_use_template': bool(mail_template),
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang),
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _find_mail_template(self):
        """ Get the mail template sent on SO confirmation (or for confirmed SO's).

        :return: `mail.template` record or None if default template wasn't found
        """
        return self.env.ref('crm_extended.mail_template_get_customer_details', raise_if_not_found=False)

    def _compute_quotation_data(self):
        for lead in self:
            lead.quotation_status = 'draft'
            current_quote = self.env['sale.order'].search([('opportunity_id', '=', self.id)], limit=1)
            if current_quote:
                lead.write({'quotation_status': current_quote.state})
            lead.quotation_count_custom = self.env['sale.order'].search_count([('opportunity_id', '=', self.id)])

    def action_view_sale_quotation_custom(self):
        action = self.env.ref('sale.action_quotations_with_onboarding').sudo().read()[0]
        order_ids = self.env['sale.order'].search([('opportunity_id', '=', self.id)])
        if len(order_ids) > 1:
            action['domain'] = [('opportunity_id', '=', self.id)]
        else:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = order_ids.id
        return action

    def action_create_quotation(self):
        self.write({'enable_quotation': True})

        # Check if a previous sale order exists for this lead and delete it
        existing_sale_order = self.env['sale.order'].search([('opportunity_id', '=', self.id)], limit=1)
        if existing_sale_order:
            existing_sale_order.sudo().unlink()

        # Create a new sale order (which is a quotation, not a confirmed sale order)
        # Use context to suppress the default "Sales Order Created" message
        quotation_creation = {
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.company_id.currency_id.id,
            'origin': self.name,
            'opportunity_id': self.id,  # Link to crm.lead
            'opportunity_no1': self.opportunity_no,
            'manager_comments': self.manager_comments,
            'description': self.description,
            'website': self.website,
            'user_id': self.user_id.id,

        }

        # Create the quotation (sale order with quotation state) without triggering the default message
        quotation = self.env['sale.order'].with_context(no_auto_message=True).create(quotation_creation)
        messages = self.env['mail.message'].search([('model', '=', 'sale.order'), ('res_id', '=', quotation.id)])
        for message in messages:
            message.sudo().unlink()
        # Manually post a custom message without triggering the system message
        quotation.message_post(
            body="Sales Quotation Created: %s" % quotation.quotation_name,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',  # Ensure it's a comment message, not a system message
            send=False  # This prevents the automatic system message from being sent
        )

        # Copy the opportunity order lines to the sale order
        if self.opportunity_order_line:
            for line in self.opportunity_order_line:
                order_lines = {
                    'name': line.product_id.description or line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.unit_price,
                    'order_id': quotation.id,
                }
                self.env['sale.order.line'].create(order_lines)

        # Copy attachments from the CRM lead to the sale order
        attachments = self.env['ir.attachment'].search([('res_model', '=', 'crm.lead'), ('res_id', '=', self.id)])
        for attachment in attachments:
            attachment.copy({'res_model': 'sale.order', 'res_id': quotation.id})

        # Create the quotation stage line
        sale_crm_ids = self.env['sale.order'].search([('id', '=', quotation.id)])
        for crm in sale_crm_ids:
            quote_lines = {
                'lead_id': crm.opportunity_id.id,
                'document_id': crm.id,
                'user_id': crm.user_id.id,
                'stage': crm.state,
            }
            self.env['quotation.stage.line'].create(quote_lines)

    @api.depends('expected_revenue')
    def _compute_potential(self):
        for rec in self:
            rec.potential_amount = False
            if rec.expected_revenue:
                rec.potential_amount = float(rec.expected_revenue)

    @api.depends('potential_amount')
    def _compute_weighted(self):
        for rec in self:
            rec.weighted_amount = False
            weighted_percentage = self.env['ir.config_parameter'].sudo().get_param('crm_extended.weighted_amount_perc',
                                                                                   False)
            if rec.potential_amount:
                rec.weighted_amount = rec.potential_amount * (float(weighted_percentage) / 100)

    def action_set_won_rainbowman(self):
        self.ensure_one()
        self.write({'is_mark_bid': True})
        message = self._get_rainbowman_message()
        for rec in self:
            subject = 'Opportunity Created'
            body = """
                        <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                            <div style="height:auto; font-size: 18px; color: #29408c;">
                                <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                    %s Created
                                </strong>
                            </div>
                            <br/>
                            <div style="text-align: left; font-size: 16px; margin-top: 10px; ">
                               As the assigned salesperson for this opportunity, I kindly request you to begin processing it at your earliest convenience.
                               <br/>
                               <br/>
                               <br/>
                            <center>
                            <a href="%s" style="background-color: #29408c; padding: 18px; text-decoration: none; color: #fff; border-radius: 4px; font-size: 13px;" class="o_default_snippet_text">View Opportunity</a>
                            <br/><br/><br/>
                            </center>
                            <center>
                              <p style="font-size: 10px;">
                                <i>THIS IS AN AUTOMATICALLY GENERATED NOTIFICATION EMAIL</i>
                              </p>
                            </center>
                        </div>""" % (
                self.name, self.get_mail_url())
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.env.user.email,
                'email_to': (self.user_id.login, self.partner_id.email),
            }
            self.message_post(body=message_body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()

        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'img_url': '/web/image/%s/%s/image_1024' % (self.team_id.user_id._name,
                                                                self.team_id.user_id.id) if self.team_id.user_id.image_1024 else '/web/static/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        return True

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url


class OpportunityOrderLine(models.Model):
    _name = 'opportunity.order.line'
    _description = 'Opportunity Order Line'

    lead_id = fields.Many2one('crm.lead', string='Product')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Expected Quantity')
    unit_measure = fields.Many2one('uom.uom', 'Unit of Measure')
    unit_price = fields.Float(string='Expected Price')
    parameter_1 = fields.Text(
        string='Parameter 1',
        related='product_id.parameter_1',
        readonly=True,
        store=True
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.quantity = 1
            rec.unit_measure = rec.product_id.uom_id.id


class QuotationStageLine(models.Model):
    _name = 'quotation.stage.line'
    _description = 'Quotation Stage Line'

    lead_id = fields.Many2one('crm.lead', string='Opportunity')
    closing_date = fields.Date('Closing Date')
    user_id = fields.Many2one('res.users', string='Sale Employee')
    stage = fields.Selection(selection=[
        ('draft', "Quotation"),
        ('sent', "Quotation Sent"),
        ('sale', "Sales Order"),
        ('done', "Locked"),
        ('cancel', "Cancelled"),
    ], string='Stage')
    show_bps_docs = fields.Boolean('Show BPs Docs', copy=False)
    document_type = fields.Selection([('quotation', 'Quotation')], default='quotation', string='Document Type')
    document_id = fields.Many2one('sale.order', string='Document No')
    revision = fields.Char('Revision')
    remarks = fields.Text('Remarks')


class CrmStage(models.Model):
    _inherit = "crm.stage"

    enable_quote = fields.Boolean('Will Create a Quotation', copy=False)

    @api.constrains('enable_quote')
    def _check_boolean_field(self):
        for rec in self:
            if not self.search([('enable_quote', '=', True)], limit=1):
                raise ValidationError(
                    'At least one stage must have "Will Create a Quotation" set to True to create a quotation.')


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    opportunity_id = fields.Many2one('crm.lead', 'Opportunity')

    @api.model
    def default_get(self, fields):
        res = super(CrmLeadLost, self).default_get(fields)
        lead = self.env['crm.lead'].browse(self.env.context.get('active_id'))
        res['opportunity_id'] = lead.id
        return res

    def action_lost_reason_apply(self):
        res = super(CrmLeadLost, self).action_lost_reason_apply()
        for rec in self:
            rec.opportunity_id.write({'is_regret': True, 'is_mark_bid': True})
            subject = 'Opportunity Lost'
            body = """
                        <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                            <div style="height:auto; font-size: 18px; color:red;">
                                <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                    %s - Lost/Regret
                                </strong>
                            </div>
                            <br/>
                            <div style="text-align: left; font-size: 16px; margin-top: 10px; ">
                            Dear %s,<br/>
                                <br/>
                                We regret to inform you that the opportunity - %s has been cancelled.<br/>
                                <br/>
                                Please find the reason for this decision below:<br/>
                                <b>Lost Reason:</b> %s.
                               <br/>
                               <br/>
                               <br/>
                            <center>
                            <a href="%s" style="background-color: #ff2c2c;; padding: 18px; text-decoration: none; color: #fff; border-radius: 4px; font-size: 13px;" class="o_default_snippet_text">View Opportunity</a>
                            <br/><br/><br/>
                            </center>
                            <center>
                              <p style="font-size: 10px;">
                                <i>THIS IS AN AUTOMATICALLY GENERATED NOTIFICATION EMAIL</i>
                              </p>
                            </center>
                        </div>""" % (
                self.opportunity_id.name, self.opportunity_id.partner_id.name, self.opportunity_id.name,
                self.lost_reason_id.name, self.opportunity_id.get_mail_url())
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.env.user.email,
                'email_to': self.opportunity_id.partner_id.email,
            }
            # self.message_post(body=message_body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
        return res


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        res = super(MailComposeMessage, self).action_send_mail()
        get_crm = self.env['crm.lead'].search([('id', '=', self.res_id)])
        get_crm.write({'mark_crm_as_sent': True})
        return res
