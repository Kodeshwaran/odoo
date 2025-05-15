# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_order_approval_rule_ids = fields.One2many('sale.order.approval.rules', 'sale_order', string='Sale Order Approval Lines', readonly=True, copy=False)
    sale_order_approval_history = fields.One2many('sale.order.approval.history', 'sale_order', string='Sale Order Approval History', readonly=True, copy=False)
    approve_button = fields.Boolean(compute='_compute_approve_button', string='Approve Button ?', search='_search_to_approve_orders', copy=False)
    ready_for_so = fields.Boolean(compute='_compute_ready_for_so', string='Ready For SO ?', copy=False)
    send_for_approval = fields.Boolean(string="Send For Approval", copy=False)
    is_rejected = fields.Boolean(string='Rejected ?', copy=False)
    user_ids = fields.Many2many('res.users', 'sale_user_rel', 'sale_id', 'uid', 'Request Users', compute='_compute_user')

    sale_order_approval_rule_id = fields.Many2one('sale.order.approval.rule', related='company_id.sale_order_approval_rule_id', string='Sale Order Approval Rules')
    sale_order_approval = fields.Boolean(related='company_id.sale_order_approval', string='Sale Order Approval By Rule')
    send_approve_process = fields.Boolean()
    dummy_compute = fields.Float("Dummy compute", compute='compute_rules_for_amount')
    approval_state = fields.Selection([('no', 'No Approvals'),
                                       ('not_sent', 'Not Sent'),
                                       ('to_approve', 'Waiting for Approval'),
                                       ('approved', 'Approved'),
                                       ], string="Approval Status", compute='_get_approval_status', copy=False)

    @api.depends('sale_order_approval_rule_ids.is_approved')
    def _get_approval_status(self):
        for rec in self:
            if rec.company_id.sale_order_approval and rec.company_id.sale_order_approval_rule_id and rec.sale_order_approval_rule_ids:
                if all([i.is_approved for i in rec.sale_order_approval_rule_ids]) and rec.sale_order_approval_rule_ids:
                    rec.approval_state = 'approved'
                else:
                    if rec.send_for_approval:
                        rec.approval_state = 'to_approve'
                    else:
                        rec.approval_state = 'not_sent'
            else:
                rec.approval_state = 'no'

    def get_user_emails(self):
        emails = self.user_ids.mapped('login')
        return emails

    @api.depends('amount_total')
    def compute_rules_for_amount(self):
        for rec in self:
            if not rec.sale_order_approval_rule_ids:
                values = rec._get_data_sale_order_approval_rule_ids()
                if values:
                    rec.write({'send_approve_process': True})
                    for v in values:
                        v.update({'state': 'draft'})
                        self.env['sale.order.approval.rules'].create(v)
            rec.dummy_compute = 0

    @api.depends('sale_order_approval_rule_ids')
    def _compute_user(self):
        for order in self:
            order.user_ids = []
            for approve_rule in order.sale_order_approval_rule_ids:
                order.user_ids = [(4, user.id) for user in approve_rule.users]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(
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

    def _search_to_approve_orders(self, operator, value):
        res = []
        for i in self.search([('sale_order_approval_rule_ids', '!=', False)]):
            approval_lines = i.sale_order_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(key=lambda r: r.sequence)
            if approval_lines:
                same_seq_lines = approval_lines.filtered(lambda b: b.sequence == approval_lines[0].sequence)
                if self.env.user in same_seq_lines.mapped('users') and i.send_for_approval:
                    res.append(i.id)
        return [('id', 'in', res)]

    @api.depends('sale_order_approval_rule_ids.is_approved')
    def _compute_approve_button(self):
        for rec in self:
            if rec.company_id.sale_order_approval and rec.company_id.sale_order_approval_rule_id:
                approval_lines = rec.sale_order_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(key=lambda r: r.sequence)
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

    def _compute_ready_for_so(self):
        for rec in self:
            if rec.company_id.sale_order_approval and rec.company_id.sale_order_approval_rule_id:
                values = rec._get_data_sale_order_approval_rule_ids()
                if values:
                    if rec.sale_order_approval_rule_ids and all([i.is_approved for i in rec.sale_order_approval_rule_ids]):
                        rec.ready_for_so = True
                    else:
                        rec.ready_for_so = False
                else:
                    rec.ready_for_so = True
            else:
                rec.ready_for_so = True

    def action_button_approve(self):
        for rec in self:
            template_id = self.env.ref('sale_approval_kanak.email_template_sale_quotation_approved')
            if rec.sale_order_approval_rule_ids:
                rules = rec.sale_order_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': True, 'date': fields.Datetime.now(), 'state': 'approve', 'user_id': self.env.user.id})
                msg = _("Quotation has been approved by %s.") % (self.env.user.name)
                self.message_post(body=msg, subtype_xmlid='mail.mt_comment')
                self.env['sale.order.approval.history'].create({
                    'sale_order': rec.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'approved'
                })
                template_id.send_mail(rec.id, force_send=True)

    def _get_data_sale_order_approval_rule_ids(self):
        values = []
        approval_rule = self.company_id.sale_order_approval_rule_id
        if self.company_id.sale_order_approval and approval_rule.approval_rule_ids:
            if approval_rule.approval_rule_ids:
                for rule in approval_rule.approval_rule_ids.sorted(key=lambda r: r.sequence):
                    if not rule.approval_category:
                        if not(rule.quotation_lower_limit == -1 or rule.quotation_upper_limit == -1) and self.amount_total:
                            if rule.quotation_lower_limit <= self.amount_total and self.amount_total <= rule.quotation_upper_limit:
                                values.append({
                                    'sequence': rule.sequence,
                                    'approval_role': rule.approval_role.id,
                                    'email_template': rule.email_template.id,
                                    'sale_order': self.id,
                                })
                        else:
                            if rule.quotation_upper_limit == -1 and self.amount_total >= rule.quotation_lower_limit and self.amount_total:
                                values.append({
                                    'sequence': rule.sequence,
                                    'approval_role': rule.approval_role.id,
                                    'email_template': rule.email_template.id,
                                    'sale_order': self.id,
                                })
                            if rule.quotation_lower_limit == -1 and self.amount_total <= rule.quotation_upper_limit and self.amount_total:
                                values.append({
                                    'sequence': rule.sequence,
                                    'approval_role': rule.approval_role.id,
                                    'email_template': rule.email_template.id,
                                    'sale_order': self.id,
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
                                        'sale_order': self.id,
                                    })
                            else:
                                if rule.quotation_upper_limit == -1 and subtotal >= rule.quotation_lower_limit:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'sale_order': self.id,
                                    })
                                if rule.quotation_lower_limit == -1 and subtotal <= rule.quotation_upper_limit:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'sale_order': self.id,
                                    })
        return values

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if not vals.get('sale_order_approval_rule_ids'):
            values = res._get_data_sale_order_approval_rule_ids()
            if values:
                res.write({'send_approve_process': True})
                for v in values:
                    v.update({'state': 'draft'})
                    self.env['sale.order.approval.rules'].create(v)
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if vals.get('order_line'):
            values = self._get_data_sale_order_approval_rule_ids()
            approval_roles = self.sale_order_approval_rule_ids.mapped('approval_role')
            for v in values:
                if not v.get('approval_role') in approval_roles.ids:
                    v.update({'state': 'draft'})
                    self.env['sale.order.approval.rules'].create(v)
            for a in self.sale_order_approval_rule_ids:
                if a.approval_role.id not in map(lambda x: x['approval_role'], values):
                    a.unlink()
        return res

    def reject_quotation(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'res_model': 'quotation.rejection.reason',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def action_send_for_approval(self):
        for record in self:
            template_id = self.env.ref('sale_approval_kanak.email_template_quotation_approval_request')
            for line in record.order_line:
                if line.price_subtotal <= 0.0:
                    context = dict(self._context or {})
                    context['sale_order'] = True
                    context['order_id'] = self.id
                    return {
                            'name': _('Warning !'),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'custom.warning',
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                            'context': context
                        }
            if record.sale_order_approval_rule_ids:
                record.message_subscribe(
                    partner_ids=record.sale_order_approval_rule_ids.mapped('users.partner_id.id'))
                msg = _("Quotation is waiting for approval.")
                record.message_post(body=msg, subtype_xmlid='mail.mt_comment')

            self.env['sale.order.approval.history'].create({
                'sale_order': record.id,
                'user': self.env.user.id,
                'date': fields.Datetime.now(),
                'state': 'send_for_approval'
            })
            template_id.send_mail(record.id, force_send=True)
            record.write({'send_for_approval': True, 'is_rejected': False})


class SaleOrderApprovalRules(models.Model):
    _name = 'sale.order.approval.rules'
    _description = 'Sale Order Approval Rules'
    _order = 'sequence'

    sale_order = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade')
    sequence = fields.Integer(required=True)
    approval_role = fields.Many2one('approval.role', string='Approval Role', required=True)
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
                employees = self.env['hr.employee'].search([('approval_role', '=', rec.approval_role.id)])
                users = self.env['res.users'].search([('employee_ids', 'in', employees.ids)])
                rec.users = [(6, 0, users.ids)]


class QuotationRejectionReason(models.TransientModel):
    _name = 'quotation.rejection.reason'
    _description = 'Quotation Rejection Reason'
    _rec_name = 'reason'

    reason = fields.Text(required=True)

    def button_reject(self):
        template_id = self.env.ref('sale_approval_kanak.email_template_sale_quotation_rejected')
        if self.env.context.get('active_id'):
            order = self.env['sale.order'].browse(self.env.context['active_id'])
            if order.sale_order_approval_rule_ids:
                rules = order.sale_order_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': False, 'date': fields.Datetime.now(), 'state': 'reject', 'user_id': self.env.user.id})
                msg = _("Quotation has been rejected by %s.") % (self.env.user.name)
                order.sudo().message_post(body=msg, subtype_id=self.env.ref('mail.mt_comment').id)
                template_id.send_mail(order.id, force_send=True)
                order.write({'is_rejected': True, 'send_for_approval': False})
                self.env['sale.order.approval.history'].create({
                    'sale_order': order.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'reject',
                    'rejection_reason': self.reason
                })


class ResUsers(models.Model):
    _inherit = 'res.users'

    sale_id = fields.Many2one('sale.order', string="sale")



class ResPartner(models.Model):
    _inherit = 'res.partner'

    import_code = fields.Char('Import Code')
    expiry_date = fields.Date('Expiry Date')