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
    can_validate_quote = fields.Boolean(copy=False)
    show_quote_sent_stage = fields.Boolean(copy=False)
    draft_so = fields.Boolean(string='Draft SO ?', copy=False)
    quotation_name = fields.Char(string='Quotation Reference', required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _('New'))
    approval_send_button = fields.Boolean("Send For Approval two")
    is_revision = fields.Boolean("Revision")
    approve_button_2 = fields.Boolean('Approve Button 2')


    def send_manager_pricing_approval(self):
        res = super(SaleOrder, self).send_manager_pricing_approval()

        for rec in self:
            if self.sale_order_approval_rule_ids:
            # Get employees with the specified approval role
                employees = self.env['hr.employee'].search([
                    ('approval_role', '=', rec.sale_order_approval_rule_ids.approval_role.ids)
                ])

                #  Collect employee work emails
                user_emails = [emp.work_email for emp in employees if emp.work_email]
                if not user_emails:
                    raise ValidationError(_('The selected users do not have email addresses configured.'))

                # Email subject and body
                subject = _('Pricing Approval Alert for Quotation %s') % rec.quotation_name
                body = f"""
                <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                    <strong><center><h1 style="color: #29408c; border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                    Pricing Approval Alert for Quotation</h1></center></strong>
                    <p style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">Hello,</p>
                    <p style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">The quotation <strong>{rec.quotation_name}</strong> requires your approval for pricing.</p>
                    <p style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">Please review and provide your feedback or approval.</p>
                    <br/>
                    <p style="font-size: 10px; color: #454748;"><i>This is an automatically generated email.</i></p>
                </div>
                """

                # Email template data
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.env.user.email or self.env.user.login,
                    'email_to': ','.join(user_emails),  # Join email addresses with commas
                }

                # Create and send the email
                mail = self.env['mail.mail'].sudo().create(template_data)
                mail.sudo().send()

                # Log activity in the Chatter
                rec.message_post(
                    body=f"The following email has been sent to: {', '.join(user_emails)}.<br/><br/>{body}",
                    subject=subject,
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )

        return res


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
                rec.sale_order_approval_rule_ids.users
                approval_lines = rec.sale_order_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(key=lambda r: r.sequence)
                if approval_lines:
                    same_seq_lines = approval_lines.filtered(lambda b: b.sequence == approval_lines[-1].sequence)
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

    # @api.depends('sale_order_approval_rule_ids.is_approved')
    # def _compute_approve_button(self):
    #     for rec in self:
    #         if rec.company_id.sale_order_approval and rec.company_id.sale_order_approval_rule_id:
    #             last_rule = rec.sale_order_approval_rule_ids[-1] if rec.sale_order_approval_rule_ids else False
    #             if last_rule and self.env.user in last_rule.users:
    #                 rec.approve_button = True
    #             else:
    #                 rec.approve_button = False
    #         else:
    #             rec.approve_button = False


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
            # Get the email template for approved quotations
            template_internal_id = self.env.ref('sale_approval_kanak.email_template_sale_quotation_approved')

            # Process approval rules
            if rec.sale_order_approval_rule_ids:
                rules = rec.sale_order_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({
                    'is_approved': True,
                    'date': fields.Datetime.now(),
                    'state': 'approve',
                    'user_id': self.env.user.id
                })

                # Post approval message
                msg = _("Quotation has been approved by %s.") % (self.env.user.name)
                rec.message_post(body=msg, subtype_xmlid='mail.mt_comment')

                # Log approval history
                self.env['sale.order.approval.history'].create({
                    'sale_order': rec.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'approved'
                })

                # Notify accounts team about OTI creation (removed OTI creation wizard)
                account_users = ', '.join(
                    user.login for user in self.env['res.users'].search([])
                    if user.has_group('account.group_account_manager')
                )
                if account_users:
                    subject = 'OTI Creation for Sale Quotation - %s' % rec.quotation_name
                    body = """
                        <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                        <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                            OTI Creation
                        </strong>
                        </div>
                        <br/>
                        <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                            <p>Dear Accounts Team, </p>
                            <p>Please proceed further and create the OTI products in stock and as well as confirm the order.</p>
                        </div>
                        <br/><br/>
                        <center>
                            <p style="font-size: 10px;">
                                <i>THIS IS AN AUTOMATICALLY GENERATED NOTIFICATION EMAIL</i>
                            </p>
                        </center>
                    """
                    mail_data = {
                        'subject': subject,
                        'body_html': body,
                        'email_from': self.env.user.login,
                        'email_to': account_users,
                    }
                    mail = self.env['mail.mail'].sudo().create(mail_data)
                    mail.sudo().send()

                # Send internal email for approval
                template_internal_id.send_mail(rec.id, force_send=True)

            # Update the 'can_validate_quote' flag
            if not rec.can_validate_quote:
                rec.write({'can_validate_quote': True})

            # Check if all rules are approved and update the sale order state
            all_approved = all(rule.state == 'approve' for rule in rec.sale_order_approval_rule_ids)
            if all_approved:
                if rec.state == 'revision':
                    rec.write({'is_stage_3': True})

            # Ensure quote validation stage updates (removed OTI check)
            rec.write(
                {'can_validate_quote': False, 'show_quote_sent_stage': True, 'draft_so': True, 'confirm_button': False})

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
        if not self.sale_order_approval_rule_ids:
            if self.state == 'revision':
                self.write({'is_stage_3': True})
        if not self.sale_order_approval_rule_ids:
            self.confirm_button = False
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
            if record.state == 'revision':
                record.write({'is_stage_1': True})
                order_line_ids = set(line.id for line in record.order_line)
                for picking in record.picking_ids:
                    for pick_line in picking.move_ids_without_package:
                        if pick_line.sale_line_id.id not in order_line_ids:
                            for line in record.order_line:
                                if line.id == pick_line.sale_line_id.id:
                                    if pick_line.quantity_done >= 1:
                                        raise ValidationError(f"The line item you are trying to delete already has {pick_line.quantity_done} received quantities, so it cannot be deleted")
                    for pick_line in picking.move_ids_without_package:
                        for line in record.order_line:
                            if line.id == pick_line.sale_line_id.id:
                                if line.product_uom_qty != pick_line.product_uom_qty:
                                    if line.product_uom_qty < pick_line.quantity_done:
                                        raise ValidationError(
                                            f"You have already completed {pick_line.quantity_done} units, so you cannot reduce the product count to {line.product_qty}. You can only increase the count to more than the {pick_line.quantity_done} units already done.")
                    order_line_ids = set(line.id for line in record.order_line)

    def action_confirm_quote(self):
        if self.name:
            self.name = self.env['ir.sequence'].next_by_code('sale.order.seq.1') or _('New')
        for rec in self:
            if any(line.is_oti for line in rec.order_line):
                context = dict(self._context or {})
                context['sale_order'] = True
                context['default_order_id'] = self.id
                return {
                    'name': _('One x Item - Creation'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'create.oti',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': context,
                }
            else:
                rec.action_confirm()

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
                order.message_post(body=msg, subtype_xmlid='mail.mt_comment')
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