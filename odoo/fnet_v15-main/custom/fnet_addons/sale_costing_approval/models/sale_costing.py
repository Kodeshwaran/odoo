# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from lxml import etree
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleCosting(models.Model):
    _inherit = 'sale.costing'

    sale_cost_approval_rule_ids = fields.One2many('sale.cost.approval.rules', 'sale_costing',
                                                  string='Sale Costing Approval Lines', readonly=True, copy=False)
    sale_cost_approval_history = fields.One2many('sale.cost.approval.history', 'sale_costing',
                                                 string='Sale Costing Approval History', readonly=True, copy=False)
    approve_button = fields.Boolean(compute='_compute_approve_button', string='Approve Button ?',
                                    search='_search_to_approve_costs', copy=False)
    ready_for_sc = fields.Boolean(compute='_compute_ready_for_sc', string='Ready to Quote ?', copy=False)
    send_for_approval = fields.Boolean(string="Send For Approval", copy=False)
    is_rejected = fields.Boolean(string='Rejected ?', copy=False)
    user_ids = fields.Many2many('res.users', 'sale_cost_user_rel', 'sale_cost_id', 'uid', 'Request Users',
                                compute='_compute_user')

    sale_cost_single_approval_rule_id = fields.Many2one('sale.cost.approval.rule',
                                                        string='Sale Costing Single Approval Rules')
    sale_cost_double_approval_rule_id = fields.Many2one('sale.cost.approval.rule',
                                                        string='Sale Costing double Approval Rules')
    sale_cost_approval = fields.Boolean(related='company_id.sale_cost_approval', string='Sale Costing Approval By Rule')
    approval_state = fields.Selection([('no', 'No Approvals'),
                                       ('not_sent', 'Not Sent'),
                                       ('to_approve', 'Waiting for Approval'),
                                       ('approved', 'Approved'),
                                       ], string="Approval Status", compute='_get_approval_status', copy=False)
    company_currency = fields.Many2one('res.currency', 'Company Currency', related="company_id.currency_id")
    amount_in_company_currency = fields.Monetary("Amount in Company Currency", compute="_currency_conversion", store=True)

    # @api.depends('line_ids')
    # def _currency_conversion(self):
    #     for rec in self:
    #         rec.amount_in_company_currency = rec.pricelist_id.currency_id.with_context(date=rec.date).compute(sum(self.line_ids.mapped('last_total_price')), rec.company_id.currency_id)

    def _get_users(self):
        upcoming_approvals = self.sale_cost_approval_rule_ids.filtered(lambda x: not x.is_approved).sorted(key=lambda x: x.sequence)
        next_approver_mails = ''
        next_approval = upcoming_approvals[0]
        if upcoming_approvals:
            can_sent_user_ids = self.env['res.users']
            if len(next_approval.users) == 1 or len(upcoming_approvals) == 1:
                can_sent_user_ids += next_approval.users
            else:
                for user in next_approval.users:
                    if len(upcoming_approvals) > 1:
                        if user.id not in upcoming_approvals[1].users.ids:
                            can_sent_user_ids += user
            if not can_sent_user_ids and len(upcoming_approvals) > 1:
                can_sent_user_ids += upcoming_approvals[1].users
            for user in can_sent_user_ids:
                next_approver_mails += user.login
                next_approver_mails += ', '
        return next_approver_mails

    @api.returns('self', lambda value: value.id)
    def copy(self, defaults=None):
        if not defaults:
            defaults = {}
        if self.env.context.get('sale_revision_history'):
            # defaults.update({
            #     'sale_cost_approval_rule_ids': [(4, rec.id) for rec in self.sale_cost_approval_rule_ids],
            #     'sale_cost_approval_history': [(4, rec.id) for rec in self.sale_cost_approval_history],
            # })
            values = self._get_data_sale_cost_approval_rule_ids()
            if values:
                self.write({'send_for_approval': False})
                for v in values:
                    v.update({'state': 'draft'})
                    self.env['sale.cost.approval.rules'].create(v)
        return super(SaleCosting, self).copy(defaults)

    @api.depends('sale_cost_approval_rule_ids')
    def _compute_user(self):
        for order in self:
            order.user_ids = []
            for approve_rule in order.sale_cost_approval_rule_ids:
                order.user_ids = [(4, user.id) for user in approve_rule.users]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleCosting, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type in ['tree', 'form'] and (self.user_has_groups('sales_team.group_sale_salesman') and not self.user_has_groups('sales_team.group_sale_manager')):
            if self._context.get('sale_approve'):
                for node in doc.xpath("//tree"):
                    node.set('create', 'false')
                    node.set('edit', 'false')
                for node_form in doc.xpath("//form"):
                    node_form.set('create', 'false')
                    node_form.set('edit', 'false')
        res['arch'] = etree.tostring(doc)
        return res

    def _search_to_approve_costs(self, operator, value):
        res = []
        for i in self.search([('sale_cost_approval_rule_ids', '!=', False)]):
            approval_lines = i.sale_cost_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(
                key=lambda r: r.sequence)
            if approval_lines:
                same_seq_lines = approval_lines.filtered(lambda b: b.sequence == approval_lines[0].sequence)
                if self.env.user in same_seq_lines.mapped('users') and i.send_for_approval:
                    res.append(i.id)
        return [('id', 'in', res)]

    @api.depends('sale_cost_approval_rule_ids.is_approved')
    def _compute_approve_button(self):
        for rec in self:
            if rec.company_id.sale_cost_approval and rec.company_id.sale_cost_single_approval_rule_id and rec.company_id.sale_cost_double_approval_rule_id:
                approval_lines = rec.sale_cost_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(
                    key=lambda r: r.sequence)
                if approval_lines:
                    same_seq_lines = approval_lines.filtered(lambda b: b.sequence == approval_lines[0].sequence)
                    if same_seq_lines:
                        if self.env.user in same_seq_lines.mapped('users') and rec.send_for_approval:
                            rec.approve_button = True
                        else:
                            rec.approve_button = False
                    else:
                        rec.approve_button = False
                else:
                    rec.approve_button = False
            else:
                rec.approve_button = False

    @api.depends('sale_cost_approval_rule_ids.is_approved')
    def _get_approval_status(self):
        for rec in self:
            if rec.company_id.sale_cost_approval and rec.company_id.sale_cost_single_approval_rule_id and rec.company_id.sale_cost_double_approval_rule_id:
                if all([i.is_approved for i in rec.sale_cost_approval_rule_ids]) and rec.sale_cost_approval_rule_ids:
                    rec.approval_state = 'approved'
                else:
                    if rec.send_for_approval:
                        rec.approval_state = 'to_approve'
                    else:
                        rec.approval_state = 'not_sent'
            else:
                rec.approval_state = 'no'

    @api.depends('sale_cost_approval_rule_ids.is_approved')
    def _compute_ready_for_sc(self):
        for rec in self:
            if rec.company_id.sale_cost_approval and rec.company_id.sale_cost_single_approval_rule_id and rec.company_id.sale_cost_double_approval_rule_id:
                if all([i.is_approved for i in rec.sale_cost_approval_rule_ids]) and rec.sale_cost_approval_rule_ids:
                    rec.ready_for_sc = True
                else:
                    rec.ready_for_sc = False
            else:
                rec.ready_for_sc = True

    def action_button_approve(self):
        self.action_confirm()
        for rec in self:
            if rec.sale_cost_approval_rule_ids:
                rules = rec.sale_cost_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': True, 'date': fields.Datetime.now(), 'state': 'approve',
                             'user_id': self.env.user.id})
                msg = _("Costing has been approved by %s.") % (self.env.user.name)
                self.message_post(body=msg)
                self.env['sale.cost.approval.history'].create({
                    'sale_costing': rec.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'approved'
                })
                if rec.approval_state == 'to_approve':
                    subject = 'Costing Approved'
                    body = """
                                <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                                    <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                        <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                            Costing Approved
                                        </strong>
                                    </div>
                                    <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                        <p>Hello,</p>
                                
                                        <p>Costing %s-%s has been approved by %s. You may proceed further to approve from your end. Please Ignore if already approved. </p>
                                    </div>
                                    <center>
                                    <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Costing</a>
                                    <br/><br/><br/>
                                    </center>
                                    <center>
                                      <p style="font-size: 30px;">
                                        <i>THIS IS AN AUTOMATICALLY GENERATED NOTIFICATION EMAIL</i>
                                      </p>
                                    </center>
                                </div>
                                         """ % (self.name,self.partner_id.name,self.env.user.name,self.get_mail_url())
                    message_body = body
                    template_data = {
                        'subject': subject,
                        'body_html': message_body,
                        'email_from': self.env.user.email,
                        'email_to': self._get_users(),
                        'email_cc': rec.sale_cost_approval_history[-1].user.login,
                    }
                    self.message_post(body=message_body, subject=subject)
                    template_id = self.env['mail.mail'].sudo().create(template_data)
                    template_id.sudo().send()
                elif rec.approval_state == 'approved':
                    subject = 'Costing Approved'
                    body = """
                                                    <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                                                        <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                                            <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                                                Costing Approved
                                                            </strong>
                                                        </div>
                                                        <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                                            <p>Hello %s,</p>

                                                            <p>Respective approval %s-%s has been done. You may proceed further from your end. </p>
                                                        </div>
                                                        <center>
                                                        <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Costing</a>
                                                        <br/><br/><br/>
                                                        </center>
                                                        <center>
                                                          <p style="font-size: 30px;">
                                                            <i>THIS IS AN AUTOMATICALLY GENERATED NOTIFICATION EMAIL</i>
                                                          </p>
                                                        </center>
                                                    </div>
                                                             """ % (rec.sale_cost_approval_history[-1].user.name,self.name,self.partner_id.name,self.get_mail_url())
                    message_body = body
                    template_data = {
                        'subject': subject,
                        'body_html': message_body,
                        'email_from': self.env.user.email,
                        'email_to': rec.sale_cost_approval_history[-1].user.login,
                    }
                    self.message_post(body=message_body, subject=subject)
                    template_id = self.env['mail.mail'].sudo().create(template_data)
                    template_id.sudo().send()

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url

    # @api.onchange('line_ids')
    # def onchange_for_call_rule_ids(self):
    #     values = self._get_data_sale_cost_approval_rule_ids()
    #     if values:
    #         for v in values:
    #             v.update({'state': 'draft'})
    #             self.env['sale.cost.approval.rules'].create(v)

    def _get_data_sale_cost_approval_rule_ids(self):
        self.sale_cost_approval_rule_ids.unlink()
        values = []
        # margin = 0
        approval_rule = ''
        # for rec in self.line_ids:
        # margin = self.line_ids.filtered(lambda x: x.service_type_id)
        #     margin += rec.margin
        # total_margin = margin/len(self.line_ids) if margin > 0 else 0
        approval_rule = (
            self.company_id.sale_cost_double_approval_rule_id
            if any(rec.service_type_id.service_margin >= rec.margin for rec in self.line_ids)
            else self.company_id.sale_cost_single_approval_rule_id
        )
        if self.company_id.sale_cost_approval and approval_rule.approval_rule_ids:
            if approval_rule.approval_rule_ids:
                for rule in approval_rule.approval_rule_ids.sorted(key=lambda r: r.sequence):
                    if not (
                            rule.quotation_lower_limit == -1 or rule.quotation_upper_limit == -1) and sum(self.line_ids.mapped('last_total_price')):
                        if rule.quotation_lower_limit <= sum(self.line_ids.mapped('last_total_price')) and sum(self.line_ids.mapped('last_total_price')) <= rule.quotation_upper_limit:
                            values.append({
                                'sequence': rule.sequence,
                                'approval_role': rule.approval_role.id,
                                'email_template': rule.email_template.id,
                                'sale_costing': self.id,
                            })
                    else:
                        if rule.quotation_upper_limit == -1 and sum(self.line_ids.mapped('last_total_price')) >= rule.quotation_lower_limit and sum(self.line_ids.mapped('last_total_price')):
                            values.append({
                                'sequence': rule.sequence,
                                'approval_role': rule.approval_role.id,
                                'email_template': rule.email_template.id,
                                'sale_costing': self.id,
                            })
                        if rule.quotation_lower_limit == -1 and sum(self.line_ids.mapped('last_total_price')) <= rule.quotation_upper_limit and sum(self.line_ids.mapped('last_total_price')):
                            values.append({
                                'sequence': rule.sequence,
                                'approval_role': rule.approval_role.id,
                                'email_template': rule.email_template.id,
                                'sale_costing': self.id,
                            })
        return values

    @api.model
    def create(self, vals):
        res = super(SaleCosting, self).create(vals)
        if not vals.get('sale_cost_approval_rule_ids'):
            values = res._get_data_sale_cost_approval_rule_ids()
            if values:
                for v in values:
                    v.update({'state': 'draft'})
                    self.env['sale.cost.approval.rules'].create(v)
        return res

    def write(self, vals):
        res = super(SaleCosting, self).write(vals)
        if self.line_ids:
            values = self._get_data_sale_cost_approval_rule_ids()
            if values:
                for v in values:
                    v.update({'state': 'draft'})
                    self.env['sale.cost.approval.rules'].create(v)
            for a in self.sale_cost_approval_rule_ids:
                if a.approval_role.id not in map(lambda x: x['approval_role'], values):
                    a.unlink()
        return res

    def reject_quotation(self):
        return {
            'name': _('Rejection Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cost.rejection.reason',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def action_send_for_approval(self):
        self.is_generate_epo = True
        if not self.markup_percentage:
            raise ValidationError('Please update Markup Percentage.')
        for record in self:
            for line in record.line_ids:
                if line.last_total_price <= 0.0:
                    context = dict(self._context or {})
                    context['sale_costing'] = True
                    context['default_sale_costing_id'] = self.id
                    return {
                        'name': _('Warning !'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'cost.custom.warning',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': context
                    }
            if record.sale_cost_approval_rule_ids:
                msg = _("Costing is waiting for approval.")
                record.message_post(body=msg)#removed subtype

            self.env['sale.cost.approval.history'].create({
                'sale_costing': record.id,
                'user': self.env.user.id,
                'date': fields.Datetime.now(),
                'state': 'send_for_approval'
            })
            subject = 'Costing Approval Request'
            body = """
                       <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                            <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                    Costing approval request
                                </strong>
                            </div>
                            <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                <p>Hello Approvers,</p>
                        
                                <p>Costing approval %s-%s has been raised by %s. Please review and approve or reject (with reason given) this costing. </p>
                            </div>
                            <center>
                            <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Costing</a>
                            <br/><br/><br/>
                            </center>
                            <center>
                              <p style="font-size: 30px;">
                                <i>THIS IS AN AUTOMATICALLY GENERATED NOTIFICATION EMAIL</i>
                              </p>
                            </center>
                        </div>
                                                     """ % (self.name,self.partner_id.name,self.env.user.name,self.get_mail_url())
            message_body = body
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': self.env.user.email,
                'email_to': self._get_users(),
            }
            self.message_post(body=message_body, subject=subject)
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
            record.write({'send_for_approval': True, 'is_rejected': False})


class SaleCostApprovalRules(models.Model):
    _name = 'sale.cost.approval.rules'
    _description = 'Sale Costing Approval Rules'
    _order = 'sequence'

    sale_costing = fields.Many2one('sale.costing', string='Sale Costing', ondelete='cascade')
    sequence = fields.Integer(required=True)
    approval_role = fields.Many2one('cost.approval.role', string='Approval Role', required=True)
    users = fields.Many2many('res.users', compute='_compute_users')
    user_id = fields.Many2one('res.users', string='User')
    email_template = fields.Many2one('mail.template', string='Mail Template')
    date = fields.Datetime()
    is_approved = fields.Boolean(string='Approved ?')
    state = fields.Selection([
        ('approve', 'Approved'),
        ('reject', 'Reject'),
        ('draft', 'Draft')
    ], string='Status', index=True, readonly=True, default='draft')

    @api.depends('approval_role')
    def _compute_users(self):
        for rec in self:
            rec.users = [(6, 0, [])]
            if rec.approval_role:
                employees = self.env['hr.employee'].sudo().search([('cost_approval_role', '=', rec.approval_role.id), ('user_id.company_ids', 'in', rec.sale_costing.company_id.id)])
                users = self.env['res.users'].search([('employee_ids', 'in', employees.ids)])
                rec.users = [(6, 0, users.ids)]


class CostRejectionReason(models.TransientModel):
    _name = 'cost.rejection.reason'
    _description = 'Costing Rejection Reason'
    _rec_name = 'reason'

    reason = fields.Text(required=True)

    def button_reject(self):
        template_id = self.env.ref('sale_costing_approval.email_template_sale_costing_rejected')
        if self.env.context.get('active_id'):
            order = self.env['sale.costing'].browse(self.env.context['active_id'])
            if order.sale_cost_approval_rule_ids:
                rules = order.sale_cost_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': False, 'date': fields.Datetime.now(), 'state': 'reject',
                             'user_id': self.env.user.id})
                msg = _("Costing has been rejected by %s.") % (self.env.user.name)
                order.message_post(body=msg, subtype_xmlid='mail.mt_comment')#removed subtype
                template_id.send_mail(order.id, force_send=True)
                order.write({'state': 'reject', 'is_rejected': True, 'send_for_approval': False})
                self.env['sale.cost.approval.history'].create({
                    'sale_costing': order.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'reject',
                    'rejection_reason': self.reason
                })


class ResUsers(models.Model):
    _inherit = 'res.users'

    sale_cost_id = fields.Many2one('sale.costing', string="Costing")
