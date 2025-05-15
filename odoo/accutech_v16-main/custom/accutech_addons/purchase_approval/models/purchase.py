# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from lxml import etree
from odoo.tools.misc import clean_context, split_every
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_order_approval_rule_ids = fields.One2many('purchase.order.approval.rules', 'purchase_order', string='Purchase Order Approval Lines', readonly=True, copy=False)
    purchase_order_approval_history = fields.One2many('purchase.order.approval.history', 'purchase_order', string='Purchase Order Approval History', readonly=True, copy=False)
    approve_button = fields.Boolean(compute='_compute_approve_button', string='Approve Button ?', search='_search_to_approve_orders', copy=False)
    ready_for_po = fields.Boolean(compute='_compute_ready_for_po', string='Ready For PO ?', copy=False)
    send_for_approval = fields.Boolean(string="Send For Approval", copy=False)
    is_rejected = fields.Boolean(string='Rejected ?', copy=False)
    user_ids = fields.Many2many('res.users', 'purchase_user_rel', 'purchase_id', 'uid', 'Request Users', compute='_compute_user')

    purchase_order_approval_rule_id = fields.Many2one('purchase.order.approval.rule', related='company_id.purchase_order_approval_rule_id', string='Purchase Order Approval Rules')
    purchase_order_approval = fields.Boolean(related='company_id.purchase_order_approval', string='Purchase Order Approval By Rule')
    send_approve_process = fields.Boolean()
    dummy_compute = fields.Float("Dummy compute", compute='compute_rules_for_amount')
    approval_state = fields.Selection([('no', 'No Approvals'),
                                       ('not_sent', 'Not Sent'),
                                       ('to_approve', 'Waiting for Approval'),
                                       ('approved', 'Approved'),
                                       ], string="Approval Status", compute='_get_approval_status', copy=False)
    amount_in_company_currency = fields.Float("Amount in Company Currency", compute="_currency_conversion")
    company_currency = fields.Many2one('res.currency', 'Company Currency', related="company_id.currency_id")

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    team_id = fields.Many2one(
        'crm.team', 'Purchase Team',
        change_default=True, default=_get_default_team, check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.depends('amount_total')
    def _currency_conversion(self):
        for rec in self:
            rec.amount_in_company_currency = rec.currency_id.with_context(date=rec.date_order).compute(rec.amount_total,
                                                                                                       rec.company_id.currency_id)

    def _get_users(self):
        upcoming_approvals = self.purchase_order_approval_rule_ids.filtered(lambda x: not x.is_approved).sorted(key=lambda x: x.sequence)
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


    @api.depends('purchase_order_approval_rule_ids.is_approved')
    def _get_approval_status(self):
        for rec in self:
            if rec.company_id.purchase_order_approval and rec.company_id.purchase_order_approval_rule_id and rec.purchase_order_approval_rule_ids:
                if all([i.is_approved for i in rec.purchase_order_approval_rule_ids]) and rec.purchase_order_approval_rule_ids:
                    rec.approval_state = 'approved'
                else:
                    if rec.send_for_approval:
                        rec.approval_state = 'to_approve'
                    else:
                        rec.approval_state = 'not_sent'
            else:
                rec.approval_state = 'no'

    @api.depends('amount_total')
    def compute_rules_for_amount(self):
        for rec in self:
            if not rec.purchase_order_approval_rule_ids:
                values = rec._get_data_purchase_order_approval_rule_ids()
                if values:
                    rec.write({'send_approve_process': True})
                    for v in values:
                        v.update({'state': 'draft'})
                        self.env['purchase.order.approval.rules'].create(v)
            rec.dummy_compute = 0

    @api.depends('purchase_order_approval_rule_ids')
    def _compute_user(self):
        for order in self:
            order.user_ids = []
            for approve_rule in order.purchase_order_approval_rule_ids:
                order.user_ids = [(4, user.id) for user in approve_rule.users]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type in ['tree', 'form'] and (self.user_has_groups('purchase.group_purchase_user') and not self.user_has_groups('purchase.group_purchase_manager')):
            if self._context.get('purchase_approve'):
                for node in doc.xpath("//tree"):
                    node.set('create', 'false')
                    node.set('edit', 'false')
                for node_form in doc.xpath("//form"):
                    node_form.set('create', 'false')
                    node_form.set('edit', 'false')
        res['arch'] = etree.tostring(doc)
        return res

    def _search_to_approve_orders(self, operator, value):
        res = []
        for i in self.search([('purchase_order_approval_rule_ids', '!=', False)]):
            approval_lines = i.purchase_order_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(key=lambda r: r.sequence)
            if approval_lines:
                same_seq_lines = approval_lines.filtered(lambda b: b.sequence == approval_lines[0].sequence)
                if self.env.user in same_seq_lines.mapped('users') and i.send_for_approval:
                    res.append(i.id)
        return [('id', 'in', res)]

    @api.depends('purchase_order_approval_rule_ids.is_approved')
    def _compute_approve_button(self):
        for rec in self:
            if rec.company_id.purchase_order_approval and rec.company_id.purchase_order_approval_rule_id:
                approval_lines = rec.purchase_order_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(key=lambda r: r.sequence)
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

    @api.depends('purchase_order_approval_rule_ids.is_approved')
    def _compute_ready_for_po(self):
        for rec in self:
            if rec.company_id.purchase_order_approval and rec.company_id.purchase_order_approval_rule_id and rec.purchase_order_approval_rule_ids:
                if all([i.is_approved for i in rec.purchase_order_approval_rule_ids]) and rec.purchase_order_approval_rule_ids:
                    rec.ready_for_po = True
                else:
                    rec.ready_for_po = False
            else:
                rec.ready_for_po = True

    def action_button_approve(self):
        for rec in self:
            if rec.purchase_order_approval_rule_ids:
                rules = rec.purchase_order_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': True, 'date': fields.Datetime.now(), 'state': 'approve', 'user_id': self.env.user.id})
                msg = _("Quotation has been approved by %s.") % (self.env.user.name)
                self.message_post(body=msg)
                self.env['purchase.order.approval.history'].create({
                    'purchase_order': rec.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'approved'
                })
                if rec.approval_state == 'to_approve':
                    subject = 'RFQ Approved'
                    body = """
                    <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                        <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                            <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                RFQ Approved
                            </strong>
                        </div>
                        <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                            <p>Hello,</p>
                    
                            <p>RFQ %s has been approved by %s. You may proceed further to approve from your end. Please Ignore if already approved. </p>
                        </div>
                    </div>
                                  """ % (self.name, self.env.user.name)
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
                elif rec.approval_state == 'approved':
                    subject = 'RFQ Approved'
                    body = """
                                        <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                                            <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                                <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                                    RFQ Approved
                                                </strong>
                                            </div>
                                            <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                                <p>Hello %s,</p>

                                                <p>Respective approval has been done. You may proceed further from your end. </p>
                                            </div>
                                        </div>
                                                      """ % (rec.purchase_order_approval_history[-1].user.name)
                    message_body = body
                    template_data = {
                        'subject': subject,
                        'body_html': message_body,
                        'email_from': self.env.user.email,
                        'email_to': rec.purchase_order_approval_history[-1].user.login,
                    }
                    self.message_post(body=message_body, subject=subject)
                    template_id = self.env['mail.mail'].sudo().create(template_data)
                    template_id.sudo().send()

    def _get_data_purchase_order_approval_rule_ids(self):
        values = []
        approval_rule = self.company_id.purchase_order_approval_rule_id
        if self.company_id.purchase_order_approval and approval_rule.approval_rule_ids:
            if approval_rule.approval_rule_ids:
                for rule in approval_rule.approval_rule_ids.sorted(key=lambda r: r.sequence):
                    if not rule.approval_category:
                        if rule.team_id:
                            if self.team_id == rule.team_id:
                                if not(rule.quotation_lower_limit == -1 or rule.quotation_upper_limit == -1) and self.amount_in_company_currency:
                                    if rule.quotation_lower_limit <= self.amount_in_company_currency and self.amount_in_company_currency <= rule.quotation_upper_limit:
                                        values.append({
                                            'sequence': rule.sequence,
                                            'approval_role': rule.approval_role.id,
                                            'email_template': rule.email_template.id,
                                            'purchase_order': self.id,
                                        })
                                else:
                                    if rule.quotation_upper_limit == -1 and self.amount_in_company_currency >= rule.quotation_lower_limit and self.amount_in_company_currency:
                                        values.append({
                                            'sequence': rule.sequence,
                                            'approval_role': rule.approval_role.id,
                                            'email_template': rule.email_template.id,
                                            'purchase_order': self.id,
                                        })
                                    if rule.quotation_lower_limit == -1 and self.amount_in_company_currency <= rule.quotation_upper_limit and self.amount_in_company_currency:
                                        values.append({
                                            'sequence': rule.sequence,
                                            'approval_role': rule.approval_role.id,
                                            'email_template': rule.email_template.id,
                                            'purchase_order': self.id,
                                        })
                        else:
                            if not (
                                    rule.quotation_lower_limit == -1 or rule.quotation_upper_limit == -1) and self.amount_in_company_currency:
                                if rule.quotation_lower_limit <= self.amount_in_company_currency and self.amount_in_company_currency <= rule.quotation_upper_limit:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'purchase_order': self.id,
                                    })
                            else:
                                if rule.quotation_upper_limit == -1 and self.amount_in_company_currency >= rule.quotation_lower_limit and self.amount_in_company_currency:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'purchase_order': self.id,
                                    })
                                if rule.quotation_lower_limit == -1 and self.amount_in_company_currency <= rule.quotation_upper_limit and self.amount_in_company_currency:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'purchase_order': self.id,
                                    })

                    if rule.approval_category:
                        rule_approval_category_order_lines = self.order_line.filtered(lambda b: b.product_id.approval_category == rule.approval_category)
                        if rule_approval_category_order_lines:
                            subtotal = sum(rule_approval_category_order_lines.mapped('price_subtotal'))
                            if not(rule.quotation_lower_limit == -1 or rule.quotation_upper_limit == -1):
                                if rule.quotation_lower_limit <= subtotal and subtotal <= rule.quotation_upper_limit:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'purchase_order': self.id,
                                    })
                            else:
                                if rule.quotation_upper_limit == -1 and subtotal >= rule.quotation_lower_limit:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'purchase_order': self.id,
                                    })
                                if rule.quotation_lower_limit == -1 and subtotal <= rule.quotation_upper_limit:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'purchase_order': self.id,
                                    })
        return values

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        if not vals.get('purchase_order_approval_rule_ids'):
            values = res._get_data_purchase_order_approval_rule_ids()
            if values:
                res.write({'send_approve_process': True})
                for v in values:
                    v.update({'state': 'draft'})
                    self.env['purchase.order.approval.rules'].create(v)
        return res

    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        if vals.get('order_line'):
            values = self._get_data_purchase_order_approval_rule_ids()
            approval_roles = self.purchase_order_approval_rule_ids.mapped('approval_role')
            for v in values:
                if not v.get('approval_role') in approval_roles.ids:
                    v.update({'state': 'draft'})
                    self.env['purchase.order.approval.rules'].create(v)
            for a in self.purchase_order_approval_rule_ids:
                if a.approval_role.id not in map(lambda x: x['approval_role'], values):
                    a.unlink()
        return res

    def reject_rfq(self):
        return {
            'name': _('Rejection Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rfq.rejection.reason',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def action_send_for_approval(self):
        for record in self:
            for line in record.order_line:
                if line.price_subtotal <= 0.0:
                    context = dict(self._context or {})
                    context['purchase_order'] = True
                    return {
                            'name': _('Warning !'),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'purchase.custom.warning',
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                            'context': context
                        }
            if record.purchase_order_approval_rule_ids:
                msg = _("Quotation is waiting for approval.")
                record.message_post(body=msg, subtype_xmlid='mail.mt_comment')

            self.env['purchase.order.approval.history'].create({
                'purchase_order': record.id,
                'user': self.env.user.id,
                'date': fields.Datetime.now(),
                'state': 'send_for_approval'
            })
            subject = 'RFQ Approval Request'
            body = """
                    <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                        <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                            <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                RFQ approval request
                            </strong>
                        </div>
                        <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                            <p>Hello Approvers,</p>
                    
                            <p>RFQ approval %s has been raised by %s. Please review and approve or reject (with reason given) this RFQ. </p>
                        </div>
                    </div>
                          """ % (self.name, self.env.user.name)
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


class PurchaseOrderApprovalRules(models.Model):
    _name = 'purchase.order.approval.rules'
    _description = 'Purchase Order Approval Rules'
    _order = 'sequence'

    purchase_order = fields.Many2one('purchase.order', string='Purchase Order', ondelete='cascade')
    sequence = fields.Integer(required=True)
    approval_role = fields.Many2one('purchase.approval.role', string='Approval Role', required=True)
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
                employees = self.env['hr.employee'].search([('purchase_approval_role', '=', rec.approval_role.id), ('user_id.company_ids', 'in', rec.purchase_order.company_id.id)])
                users = self.env['res.users'].search([('employee_ids', 'in', employees.ids)])
                rec.users = [(6, 0, users.ids)]


class QuotationRejectionReason(models.TransientModel):
    _name = 'rfq.rejection.reason'
    _description = 'RFQ Rejection Reason'
    _rec_name = 'reason'

    reason = fields.Text(required=True)

    def button_reject(self):
        template_id = self.env.ref('purchase_approval.email_template_purchase_rfq_rejected')
        if self.env.context.get('active_id'):
            order = self.env['purchase.order'].browse(self.env.context['active_id'])
            if order.purchase_order_approval_rule_ids:
                rules = order.purchase_order_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': False, 'date': fields.Datetime.now(), 'state': 'reject', 'user_id': self.env.user.id})
                msg = _("Quotation has been rejected by %s.") % (self.env.user.name)
                order.message_post(body=msg, subtype_xmlid='mail.mt_comment')
                template_id.send_mail(order.id, force_send=True)
                order.write({'is_rejected': True, 'send_for_approval': False})
                self.env['purchase.order.approval.history'].create({
                    'purchase_order': order.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'reject',
                    'rejection_reason': self.reason
                })


class ResUsers(models.Model):
    _inherit = 'res.users'

    purchase_id = fields.Many2one('purchase.order', string="Purchase")
