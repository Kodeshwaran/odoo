from odoo import api, fields, models, _
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
    approval_state = fields.Selection([('no', 'No Approvals'),
                                       ('not_sent', 'Not Sent'),
                                       ('to_approve', 'Waiting for Approval'),
                                       ('approved', 'Approved'),
                                       ], string="Approval Status", compute='_get_approval_status', copy=False)
    dummy_compute = fields.Float("Dummy compute", compute='compute_rules_for_amount')
    minimum_approval = fields.Integer(related="sale_order_approval_rule_id.minimum_approval")
    maximum_approval = fields.Integer(related="sale_order_approval_rule_id.maximum_approval")
    amount_total_value = fields.Integer(compute="_get_amount_total_value")

    @api.depends('amount_total')
    def _get_amount_total_value(self):
        for rec in self:
            rec.amount_total_value = rec.amount_total

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

    def _get_users(self):
        upcoming_approvals = self.sale_order_approval_rule_ids.filtered(lambda x: not x.is_approved).sorted(key=lambda x: x.sequence)
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
            if rec.sale_order_approval_rule_ids:
                values = rec._get_data_sale_order_approval_rule_ids()
                if not values:
                    rec.sale_order_approval_rule_ids = False
                    rec.ready_for_so = True

            rec.dummy_compute = 0

    @api.depends('sale_order_approval_rule_ids')
    def _compute_user(self):
        for order in self:
            order.user_ids = []
            for approve_rule in order.sale_order_approval_rule_ids:
                order.user_ids = [(4, user.id) for user in approve_rule.users]

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
                approval_lines = rec.sale_order_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(
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

    @api.depends('sale_order_approval_rule_ids.is_approved')
    def _compute_ready_for_so(self):
        for rec in self:
            if rec.company_id.sale_order_approval and rec.company_id.sale_order_approval_rule_id and rec.sale_order_approval_rule_ids:
                if all([i.is_approved for i in rec.sale_order_approval_rule_ids]) and rec.sale_order_approval_rule_ids:
                    rec.ready_for_so = True
                else:
                    rec.ready_for_so = False
            else:
                rec.ready_for_so = True

    def action_button_approve(self):
        for rec in self:
            if rec.sale_order_approval_rule_ids:
                rules = rec.sale_order_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': True, 'date': fields.Datetime.now(), 'state': 'approve',
                             'user_id': self.env.user.id})
                msg = _("Quotation has been approved by %s.") % (self.env.user.name)
                self.message_post(body=msg)
                self.env['sale.order.approval.history'].create({
                    'sale_order': rec.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'approved'
                })
                if rec.approval_state == 'to_approve':
                    subject = 'Quotation Approved'
                    body = """
                                       <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                                           <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                               <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                                   Quotation Approved
                                               </strong>
                                           </div>
                                           <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                               <p>Hello,</p>

                                               <p>Quotation %s-%s has been approved by %s. You may proceed further to approve from your end. Please Ignore if already approved. </p>
                                           </div>
                                           <center>
                                               <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Quotation</a>
                                               <br/><br/><br/>
                                           </center>
                                       </div>
                                                     """ % (
                    self.name, self.partner_id.name, self.env.user.name, self.get_mail_url())
                    message_body = body
                    template_data = {
                        'subject': subject,
                        'body_html': message_body,
                        'email_from': self.env.user.email,
                        'email_to': self._get_users(),
                        'email_cc': rec.sale_order_approval_history[-1].user.login,
                    }
                    self.message_post(body=message_body, subject=subject)
                    template_id = self.env['mail.mail'].sudo().create(template_data)
                    template_id.sudo().send()
                elif rec.approval_state == 'approved':
                    subject = 'Quotation Approved'
                    body = """
                               <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                                   <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                       <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                           Quotation Approved
                                       </strong>
                                   </div>
                                   <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                       <p>Hello %s,</p>

                                       <p>Respective approval for %s-%s has been done. You may proceed further from your end. </p>
                                   </div>
                                   <center>
                                   <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Quotation</a>
                                   <br/><br/><br/>
                                   </center>
                               </div>
                                     """ % (
                    rec.sale_order_approval_history[-1].user.name, self.name, self.partner_id.name, self.get_mail_url())
                    message_body = body
                    template_data = {
                        'subject': subject,
                        'body_html': message_body,
                        'email_from': self.env.user.email,
                        'email_to': rec.sale_order_approval_history[-1].user.login,
                    }
                    self.message_post(body=message_body, subject=subject)
                    template_id = self.env['mail.mail'].sudo().create(template_data)
                    template_id.sudo().send()

    def reject_quotation(self):
        return {
            'name': _('Rejection Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'quotation.rejection.reason',
            'type': 'ir.actions.act_window',
            'context': {'default_sale_order_id': self.id},
            'target': 'new'
        }

    def _get_data_sale_order_approval_rule_ids(self):
        values = []
        approval_rule = self.company_id.sale_order_approval_rule_id
        if self.company_id.sale_order_approval and approval_rule.approval_rule_ids:
            if approval_rule.approval_rule_ids:
                for rule in approval_rule.approval_rule_ids.sorted(key=lambda r: r.sequence):
                    if not rule.approval_category:
                        if self.amount_total == 0:
                            if (rule.quotation_lower_limit == self.amount_total) and (rule.quotation_upper_limit == self.amount_total):
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

    def action_send_for_approval(self):
        for record in self:
            if record.sale_order_approval_rule_ids:
                msg = _("Quotation is waiting for approval.")
                record.message_post(body=msg)

            self.env['sale.order.approval.history'].create({
                'sale_order': record.id,
                'user': self.env.user.id,
                'date': fields.Datetime.now(),
                'state': 'send_for_approval'
            })
            subject = 'Quotation Approval Request'
            body = """
                        <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                            <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                    Quotation approval request
                                </strong>
                            </div>
                            <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                <p>Hello Approvers,</p>

                                <p>Quotation approval %s-%s has been raised by %s. Please review and approve or reject (with reason given) this quotation. </p>
                            </div>
                            <center>
                                <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View Quotation</a>
                                <br/><br/><br/>
                            </center>
                        </div>
                                  """ % (self.name, self.partner_id.name, self.env.user.name, self.get_mail_url())
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


    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url

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
                employees = self.env['hr.employee'].search([('approval_role', '=', rec.approval_role.id), (
                'user_id.company_ids', 'in', rec.sale_order.company_id.id)])
                users = self.env['res.users'].search([('employee_ids', 'in', employees.ids)])
                rec.users = [(6, 0, users.ids)]

class QuotationRejectionReason(models.TransientModel):
    _name = 'quotation.rejection.reason'
    _description = 'Quotation Rejection Reason'
    _rec_name = 'reason'

    reason = fields.Text(required=True)
    sale_order_id = fields.Many2one('sale.order', string="Sale Order ID")

    def button_reject(self):
        subject = 'Quotation Rejected'
        body = """
                <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                    <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                        <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                            Quotation Rejected
                        </strong>
                    </div>
                    <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                        <p>Hello %s,</p>
                
                        <p>Quotation %s has been rejected by %s. Please review this with the approver and make changes to the record, then re-send for approval. </p>
                    </div>
                </div>
                """ % (self.sale_order_id.sale_order_approval_history[-1].user.name, self.sale_order_id.name, self.sale_order_id.user_id.name)
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.email,
            'email_to': self.sale_order_id.sale_order_approval_history[-1].user.email,
        }
        self.sale_order_id.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        if self.env.context.get('active_id'):
            order = self.env['sale.order'].browse(self.env.context['active_id'])
            if order.sale_order_approval_rule_ids:
                rules = order.sale_order_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': False, 'date': fields.Datetime.now(), 'state': 'reject', 'user_id': self.env.user.id})
                msg = _("Quotation has been rejected by %s.") % (self.env.user.name)
                order.message_post(body=msg, subtype_xmlid='mail.mt_comment')
                template_id.send(order.id)
                order.write({'is_rejected': True, 'send_for_approval': False})
                self.env['sale.order.approval.history'].create({
                    'sale_order': order.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'reject',
                    'rejection_reason': self.reason
                })