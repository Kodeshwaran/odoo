from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, except_orm
import re


class Purchase(models.Model):
    _inherit = 'purchase.order'

    purchase_order_approval_rule_ids = fields.One2many('purchase.order.approval.rules', 'purchase_order',
                                                       string='Purchase Order Approval Lines', readonly=True,
                                                       copy=False)
    purchase_order_approval_history = fields.One2many('purchase.order.approval.history', 'purchase_order',
                                                      string='Purchase Order Approval History', readonly=True,
                                                      copy=False)
    approve_button = fields.Boolean(compute='_compute_approve_button', string='Approve Button ?',
                                    search='_search_to_approve_orders', copy=False)
    ready_for_po = fields.Boolean(compute='_compute_ready_for_po', string='Ready For PO ?', copy=False)
    send_for_approval = fields.Boolean(string="Send For Approval", copy=False)
    is_rejected = fields.Boolean(string='Rejected ?', copy=False)
    user_ids = fields.Many2many('res.users', 'purchase_user_rel', 'purchase_id', 'uid', 'Request Users',
                                compute='_compute_user')
    state = fields.Selection([
        ('draft', 'Draft PO'),
        ('sent', 'RFQ Sent'),
        ('bid received', 'Bid Received'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('amendment', 'Amendment'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    states = fields.Selection([('load', 'Load Order'), ('in_progress', 'In Progress'), ('done', 'Done')], readonly=True,
                              default='load', track_visibility='onchange')
    margin_line = fields.One2many('sale.quotes.line', 'purchaseorder_id', string='Margin Rate')
    history_line = fields.One2many('bid.received.history', 'order_id', string='History')
    expected_closing = fields.Date('Expected closing')
    delivery_term = fields.Char('Delivery Terms')
    delivery_date = fields.Date("Delivery Date")
    order_reference = fields.Char("Reference")
    omega_trn_no = fields.Char("Omega TRN No.", related='company_id.vat', store=True, readonly=True)
    enquiry_id = fields.Many2one('crm.lead', string="Enquiry")
    purchase_order_approval_rule_id = fields.Many2one('purchase.order.approval.rule',
                                                      related='company_id.purchase_order_approval_rule_id',
                                                      string='Purchase Order Approval Rules')
    purchase_order_approval = fields.Boolean(related='company_id.purchase_order_approval',
                                             string='Purchase Order Approval By Rule')
    send_approve_process = fields.Boolean()
    dummy_compute = fields.Float("Dummy compute", compute='compute_rules_for_amount')
    approval_state = fields.Selection([('no', 'No Approvals'),
                                       ('not_sent', 'Not Sent'),
                                       ('to_approve', 'Waiting for Approval'),
                                       ('approved', 'Approved'),
                                       ], string="Approval Status", compute='_get_approval_status', copy=False)
    revision = fields.Integer(string='Amendment Revision')
    amendment_name = fields.Char('Order Reference', copy=True, readonly=True)
    current_amendment_id = fields.Many2one('purchase.order', 'Current Amendment', readonly=True, copy=True)
    old_amendment_ids = fields.One2many('purchase.order', 'current_amendment_id', 'Old Amendment', readonly=True,
                                        context={'active_test': False})
    is_amend = fields.Boolean()


    def create_amendment(self):
        self.ensure_one()
        view_ref = self.env['ir.model.data'].sudo()._xmlid_lookup('purchase.purchase_order_form')
        view_id = view_ref and view_ref[1] or False,
        self.with_context(new_purchase_amendment=True).copy()
        self.write({'state': 'draft'})
        self.order_line.write({'state': 'draft'})
        return {'type': 'ir.actions.act_window',
                'name': ('Purchase Order'),
                'res_model': 'sale.order',
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'current',
                'nodestroy': True}

    def button_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent', 'amendment'])
        orders.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        if 'amendment_name' not in vals:
            if vals.get('name', 'New') == 'New':
                seq = self.env['ir.sequence']
                vals['name'] = seq.next_by_code('purchase.order') or '/'
            vals['amendment_name'] = vals['name']
        return super(Purchase, self).create(vals)

    @api.returns('self', lambda value: value.id)
    def copy(self, defaults=None):
        if not defaults:
            defaults = {}
        if self.env.context.get('new_purchase_amendment'):
            prev_name = self.name
            revno = self.revision
            self.write({'revision': revno + 1, 'name': '%s-%02d' % (self.amendment_name, revno + 1)})
            defaults.update({'name': prev_name, 'revision': revno, 'state': 'cancel', 'invoice_count': 0,
                             'current_amendment_id': self.id, 'amendment_name': self.amendment_name, })
        return super(Purchase, self).copy(defaults)

    def button_amend(self):
        for purchase in self:
            for picking_loop in purchase.picking_ids:
                if picking_loop.state == 'done':
                    raise UserError(
                        'Unable to amend this purchase order, You must first cancel all receptions related to this purchase order.')
                else:
                    picking_loop.filtered(lambda r: r.state != 'cancel').action_cancel()

            for invoice_loop in purchase.invoice_ids:
                if invoice_loop.state != 'draft':
                    raise UserError(
                        'Unable to amend this purchase order, You must first cancel all Supplier Invoices related to this purchase order.')
                else:
                    invoice_loop.filtered(lambda r: r.state != 'cancel').action_invoice_cancel()
            if purchase.purchase_order_approval_rule_ids:
                for approval in purchase.purchase_order_approval_rule_ids:
                    if approval.state != 'draft':
                        approval.state = 'draft'
                        approval.date = False
                        approval.user_id = False
                        approval.is_approved = False
            for history in purchase.purchase_order_approval_history:
                if history.state in ['send_for_approval', 'approved']:
                    history.unlink()
            purchase.button_draft()
            purchase.create_amendment()
            purchase.write({'send_for_approval': False, 'is_amend': True, 'state': 'amendment'})

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
                record.message_post(body=msg)

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

                            <p>RFQ approval %s-%s has been raised by %s. Please review and approve or reject (with reason given) this RFQ. </p>
                        </div>
                        <center>
                        <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View RFQ</a>
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
            if record.is_amend:
                record.write({'is_amend': False})

    def action_button_approve(self):
        for rec in self:
            if rec.purchase_order_approval_rule_ids:
                rules = rec.purchase_order_approval_rule_ids.filtered(lambda b: self.env.user in b.users)
                rules.write({'is_approved': True, 'date': fields.Datetime.now(), 'state': 'approve',
                             'user_id': self.env.user.id})
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

                            <p>RFQ %s-%s has been approved by %s. You may proceed further to approve from your end. Please Ignore if already approved. </p>
                        </div>
                        <center>
                            <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View RFQ</a>
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

                                    <p>Respective approval %s-%s has been done. You may proceed further from your end. </p>
                                </div>
                                <center>
                                <a href="%s" style="background-color: #1abc9c; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" class="o_default_snippet_text">View RFQ</a>
                                <br/><br/><br/>
                                </center>
                            </div>
                                          """ % (
                    rec.purchase_order_approval_history[-1].user.name, self.partner_id.name, self.name,
                    self.get_mail_url())
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

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url


    def reject_quotation(self):
        return {
            'name': _('Rejection Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rfq.rejection.reason',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def bid_received(self):
        # for rec in self.order_line:
        #     if rec.price_subtotal == 0:
        #         raise UserError(_("Please enter the product price and quantity"))
        bid_receive_obj = self.env['bid.received.line']
        if self.requisition_id:
            for line in self.order_line:
                bid_receive_obj.create({
                            'tender_id': self.requisition_id.id,
                            'purchase_order_id': self.id,
                            'vender_id': self.partner_id.id,
                            'product_id': line.product_id.id,
                            'quantity': line.product_qty,
                            'purchase_unit_price': line.price_unit,
                            'unit_price': line.price_unit,
                            'purchase_total_price': line.price_subtotal,
                            'sub_total': line.price_subtotal,
                            'unit_measure': line.product_id.uom_id.id,
                        })
        self.write({'state': 'bid received'})

    def send_rfq(self):
        self.write({'state': 'sent'})

    def button_approve(self, force=False):
        val = self.env['ir.sequence'].next_by_code('confirm.purchase')
        if val:
            self.write({'name': val})
        if self.requisition_id and not self.requisition_id.quote_count:
            raise UserError(_('Please select the sale quotes in Purchase Agreements..!'))
        else:
            return super(Purchase, self).button_approve(force=force)

    def bids_confirm(self):
        """
        This function is call from button confirm,
        This process done in set margin price for product
        It is change the state on done and create the recored on bid received line.
        """
        product = []
        count = 0
        cnt = []
        offer = 1
        for mrg in self.margin_line:
            if mrg.customer_price == 0 and mrg.margin_unit_price == 0:
                count = 1
                product.append(mrg.product_id.name)

        if count == 0:
            self.write({'states': 'done'})
            requisition_id = self.env['purchase.requisition'].search([('name', '=', self.origin)])
            history_obj = self.env['costing.history.line']
            for line in self.margin_line:
                bid_id = self.env['bid.received.line'].search(
                    [('tender_id', '=', self.requisition_id.id), ('product_id', '=', line.product_id.id),
                     ('purchase_order_id', '=', self.id)])
                if bid_id:
                    res_value = {
                        'quantity': line.quantity,
                        'purchase_unit_price': line.purchase_unit_price,
                        'purchase_total_price': line.purchase_total_price,
                        'unit_price': line.margin_unit_price,
                        'sub_total': line.customer_price,
                    }
                    bid_id.write(res_value)
                else:
                    res_value = {
                        'tender_id': requisition_id.id,
                        'purchase_order_id': self.id,
                        'vender_id': self.partner_id.id,
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'purchase_unit_price': line.purchase_unit_price,
                        'unit_price': line.margin_unit_price,
                        'purchase_total_price': line.purchase_total_price,
                        'sub_total': line.customer_price,
                        'unit_measure': line.unit_measure.id,
                    }
                    self.env['bid.received.line'].create(res_value)
            if self.history_line:
                for i in self.history_line:
                    string_val = i.offer
                    val = string_val.split(" ")
                    cnt.append(val[1])
                x = [int(n) for n in cnt]
                next_off = max(x)
                offer = next_off + 1
            vals = {
                'offer': 'OFFER ' + str(int(offer)),
                'order_id': self.id,
            }
            off_id = self.history_line.create(vals)
            for line in self.margin_line:
                history_value = {
                    'offer_id': off_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'purchase_unit_price': line.purchase_unit_price,
                    'transfort_charge': line.transfort_charge,
                    'margin_percentage': line.margin_percentage,
                    'unit_measure': line.unit_measure.id,
                    'margin_unit_price': line.margin_unit_price,
                    'customer_price': line.customer_price,
                }
                history_obj.create(history_value)
        else:
            raise UserError(_('Please Calculate the Customer Price..!'))

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'bid received']:
                continue
            order._add_supplier_to_product()
            if order.company_id.po_double_validation == 'one_step':
                order.button_approve(force=True)
            else:
                order.write({'state': 'to approve'})
        return True

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

    @api.depends('purchase_order_approval_rule_ids')
    def _compute_user(self):
        for order in self:
            order.user_ids = []
            for approve_rule in order.purchase_order_approval_rule_ids:
                order.user_ids = [(4, user.id) for user in approve_rule.users]

    @api.depends('purchase_order_approval_rule_ids.is_approved')
    def _get_approval_status(self):
        for rec in self:
            if rec.company_id.purchase_order_approval and rec.company_id.purchase_order_approval_rule_id and rec.purchase_order_approval_rule_ids:
                if all([i.is_approved for i in
                        rec.purchase_order_approval_rule_ids]) and rec.purchase_order_approval_rule_ids:
                    rec.approval_state = 'approved'
                else:
                    if rec.send_for_approval:
                        rec.approval_state = 'to_approve'
                    else:
                        rec.approval_state = 'not_sent'
            else:
                rec.approval_state = 'no'

    @api.depends('purchase_order_approval_rule_ids.is_approved')
    def _compute_ready_for_po(self):
        for rec in self:
            if rec.company_id.purchase_order_approval and rec.company_id.purchase_order_approval_rule_id and rec.purchase_order_approval_rule_ids:
                if all([i.is_approved for i in
                        rec.purchase_order_approval_rule_ids]) and rec.purchase_order_approval_rule_ids:
                    rec.ready_for_po = True
                else:
                    rec.ready_for_po = False
            else:
                rec.ready_for_po = True

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

    @api.depends('purchase_order_approval_rule_ids.is_approved')
    def _compute_approve_button(self):
        for rec in self:
            if rec.company_id.purchase_order_approval and rec.company_id.purchase_order_approval_rule_id:
                approval_lines = rec.purchase_order_approval_rule_ids.filtered(lambda b: not b.is_approved).sorted(
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

    def _get_data_purchase_order_approval_rule_ids(self):
        values = []
        approval_rule = self.company_id.purchase_order_approval_rule_id
        if self.company_id.purchase_order_approval and approval_rule.approval_rule_ids:
            if approval_rule.approval_rule_ids:
                for rule in approval_rule.approval_rule_ids.sorted(key=lambda r: r.sequence):
                    if not rule.approval_category:
                        if rule.team_id:
                            if self.team_id == rule.team_id:
                                if not(rule.quotation_lower_limit == -1 or rule.quotation_upper_limit == -1) and self.amount_total:
                                    if rule.quotation_lower_limit <= self.amount_total and self.amount_total <= rule.quotation_upper_limit:
                                        values.append({
                                            'sequence': rule.sequence,
                                            'approval_role': rule.approval_role.id,
                                            'email_template': rule.email_template.id,
                                            'purchase_order': self.id,
                                        })
                                else:
                                    if rule.quotation_upper_limit == -1 and self.amount_total >= rule.quotation_lower_limit and self.amount_total:
                                        values.append({
                                            'sequence': rule.sequence,
                                            'approval_role': rule.approval_role.id,
                                            'email_template': rule.email_template.id,
                                            'purchase_order': self.id,
                                        })
                                    if rule.quotation_lower_limit == -1 and self.amount_total <= rule.quotation_upper_limit and self.amount_total:
                                        values.append({
                                            'sequence': rule.sequence,
                                            'approval_role': rule.approval_role.id,
                                            'email_template': rule.email_template.id,
                                            'purchase_order': self.id,
                                        })
                        else:
                            if not (
                                    rule.quotation_lower_limit == -1 or rule.quotation_upper_limit == -1) and self.amount_total:
                                if rule.quotation_lower_limit <= self.amount_total and self.amount_total <= rule.quotation_upper_limit:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'purchase_order': self.id,
                                    })
                            else:
                                if rule.quotation_upper_limit == -1 and self.amount_total >= rule.quotation_lower_limit and self.amount_total:
                                    values.append({
                                        'sequence': rule.sequence,
                                        'approval_role': rule.approval_role.id,
                                        'email_template': rule.email_template.id,
                                        'purchase_order': self.id,
                                    })
                                if rule.quotation_lower_limit == -1 and self.amount_total <= rule.quotation_upper_limit and self.amount_total:
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

    def get_purchase_quote(self):
        """
        This function get the details from orderline
        """
        if self.state in ['draft', 'sent']:
            raise except_orm('Messages', 'Please change the state to bid received!')
        quote_obj = self.env['sale.quotes.line']
        for line in self.order_line:
            if line.price_unit != 0:
                val = {
                    'purchaseorder_id': line.order_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.product_qty,
                    'purchase_unit_price': line.price_unit,
                    'purchase_total_price': line.price_subtotal,
                    'unit_measure': line.product_uom.id,
                }
                quote_obj.create(val)
            else:
                raise UserError(_('Please set the product unit price..!! '))
        self.write({'states': 'in_progress'})

    def set_margin_price(self):
        """
        This function is calculate the margin price for product
        margin=(unit price/100)*percent
        transfort+margin
        then the above value is added to unit price
        """
        for line in self.margin_line:
            if line.margin_percentage and line.purchase_unit_price != 0:
                margin = (((line.quantity*line.purchase_unit_price)+(line.transfort_charge)+(line.finance_cost))*(line.margin_percentage / 100))
                extra_charge = line.transfort_charge+line.finance_cost
                margin_percentage = line.margin_percentage / 100
                total_unit_price = line.purchase_unit_price * line.quantity
                margin_per_unit = ((((total_unit_price+extra_charge)+((total_unit_price+extra_charge)*margin_percentage))/line.quantity))
                line.write({
                    'margin_unit_price': margin_per_unit,
                    'customer_price': margin_per_unit*line.quantity,
                })
            else:
                raise UserError(_('Please set the margin price for these product"%s"') % (line.product_id.name))

    def return_draft(self):
        quote_obj = self.env['sale.quotes.line'].search([('purchaseorder_id', '=', self.id)])
        if quote_obj:
            quote_obj.unlink()
        self.write({'states': 'load'})

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
                employees = self.env['hr.employee'].search([('purchase_approval_role', '=', rec.approval_role.id), (
                'user_id.company_ids', 'in', rec.purchase_order.company_id.id)])
                users = self.env['res.users'].search([('employee_ids', 'in', employees.ids)])
                rec.users = [(6, 0, users.ids)]


class QuotationRejectionReason(models.TransientModel):
    _name = 'rfq.rejection.reason'
    _description = 'Quotation Rejection Reason'
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
                order.message_post(body=msg)
                template_id.send_mail(order.id, force_send=True)
                order.write({'is_rejected': True, 'send_for_approval': False})
                self.env['purchase.order.approval.history'].create({
                    'purchase_order': order.id,
                    'user': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'state': 'reject',
                    'rejection_reason': self.reason
                })


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    item_no = fields.Char('Item No')
    requisition_line_id = fields.Many2one('purchase.requisition.line', string="Requisition Line")
    name = fields.Html(string='Description', required=True)

    @api.constrains('item_no')
    def _check_my_field(self):
        for record in self:
            value = record.item_no
            if value:
                if not re.match(r'^\d+(\.\d+)?$', value):
                    raise models.ValidationError("Only float and integer values are allowed in 'Item No'.")


class sale_quotes_line(models.Model):
    _name = 'sale.quotes.line'
    _description = 'sale_quotes_line'

    purchaseorder_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    purchase_unit_price = fields.Float('Purchase Unit Price', readonly=True)
    transfort_charge = fields.Float('Purchase Cost')
    finance_cost = fields.Float(string="Finance Cost")
    purchase_total_price = fields.Float('Total Price', readonly=True)
    margin_unit_price = fields.Float('Margin Unit Price', readonly=True)
    customer_price = fields.Float('Customer Price', readonly=True)
    unit_measure = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    margin_percentage = fields.Float(string='Margin Percentage')


class MarginRate(models.Model):
    _name = 'margin.rate'
    _description = 'MarginRate'

    name = fields.Char('Name', size=5)
    active = fields.Boolean('Active')
    values = fields.Float('Value', default=True)


class costing_history_line(models.Model):
    _name = 'costing.history.line'
    _description = 'costing_history_line'

    offer_id = fields.Many2one('bid.received.history', string='Bid Received', readonly=True)
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float('Quantity')
    purchase_unit_price = fields.Float('Purchase Unit Price')
    transfort_charge = fields.Float('Purchase Cost')
    finance_cost = fields.Float(string="Finance Cost")
    margin_percentage = fields.Float(string='Margin Percentage')
    unit_measure = fields.Many2one('uom.uom', string='Unit of Measure')
    margin_unit_price = fields.Float('Margin Unit Price')
    customer_price = fields.Float('Customer Price')


class bid_received_history(models.Model):
    _name = 'bid.received.history'
    _description = 'bid_received_history'

    offer = fields.Char('OFFER', size=64)
    costing_history_line = fields.One2many('costing.history.line', 'offer_id', 'Offers')
    order_id = fields.Many2one('purchase.order', 'Purchase Order')
