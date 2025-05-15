from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_approval = fields.Boolean(compute="_check_sale_id_approval")
    send_for_approval = fields.Boolean('Send for Approval')
    approve_button = fields.Boolean(compute="_compute_approve_button", search="_search_to_approve_orders", copy=False)
    ready_for_po = fields.Boolean(string='Ready For PO ?', copy=False)
    po_type = fields.Selection([('sales', 'Sales'), ('regular', 'Regular')], string="PO Type", required=True, default='sales')
    is_finance_users = fields.Boolean(compute="check_users")
    is_po_approval = fields.Boolean(compute="check_users")
    approval_required = fields.Boolean(compute="check_approval_required")
    show_confirm = fields.Boolean(compute='show_confirm_button')
    # show_approve = fields.Boolean(compute='show_approve_button')



    def check_users(self):
        if self.env.user.has_group('account.group_account_manager'):
            self.is_finance_users = True
        else:
            self.is_finance_users = False
        if self.env.user.has_group('purchase_approval.group_po_type_approval'):
            self.is_po_approval = True
        else:
            self.is_po_approval = False

    @api.depends('sale_approval')
    def _compute_approve_button(self):
        for rec in self:
            if rec.sale_approval:
                rec.approve_button = True
            else:
                rec.approve_button = False

    def get_mail_recipient(self):
        po_type_sale = ''
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('purchase_approval.group_po_type_approval_sales'):
                po_type_sale += user.login
                po_type_sale += ', '
        po_type_regular = ''
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('purchase_approval.group_po_type_approval_regular'):
                po_type_regular += user.login
                po_type_regular += ', '
        if self.po_type == 'sales':
            return po_type_sale
        else:
            return po_type_regular

    @api.depends('sale_approval')
    def _check_sale_id_approval(self):
        for rec in self:
            if rec.sale_id.send_for_approval:
                rec.sale_approval = True
            else:
                rec.sale_approval = False


    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url

    @api.depends('po_type')
    def check_approval_required(self):
        if self.po_type == 'sales' and self.sale_id and self.sale_approval:
            self.approval_required = True
        elif self.po_type == 'sales' and self.sale_id and not self.sale_approval:
            self.approval_required = False
        elif self.po_type == 'sales' and not self.sale_id and not self.sale_approval:
            self.approval_required = True
        elif self.po_type == 'regular':
            self.approval_required = True

    @api.depends('po_type')
    def show_confirm_button(self):
        if self.po_type == 'sales' and self.sale_id and not self.sale_approval and self.state in ['draft', 'sent']:
            self.show_confirm = True
        elif self.state == 'validate':
            self.show_confirm = True
        else:
            self.show_confirm = False

    # @api.depends('po_type')
    # def show_approve_button(self):

    def action_send_for_approval(self):
        for rec in self:
            # Scenario 1 user approvers - FINANCE
            finance_approvers = ''
            users = self.env['res.users'].search([])
            for user in users:
                if user.has_group('account.group_account_manager'):
                    finance_approvers += user.login
                    finance_approvers += ', '
            # Scenario 3 user approvers - PO type Sales
            po_type_sales = ''
            users = self.env['res.users'].search([])
            for user in users:
                if user.has_group('purchase_approval.group_po_type_approval_sales'):
                    po_type_sales += user.login
                    po_type_sales += ', '
            # Scenario 4 user approvers - PO type Regular
            po_type_regular = ''
            users = self.env['res.users'].search([])
            for user in users:
                if user.has_group('purchase_approval.group_po_type_approval_regular'):
                    po_type_regular += user.login
                    po_type_regular += ', '

            if self.po_type == 'sales' and self.sale_id and self.sale_approval:
                if finance_approvers:
                    subject = 'Purchase Order Approval Request'
                    body = """
                            <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                                <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                    <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                        Purchase Order Approval Request
                                    </strong>
                                </div>
                                <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                    <p>Hello Approvers,</p>
    
                                    <p>Order approval %s-%s has been raised by %s. Please review and approve or reject (with reason given) this quotation. </p>
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
                        'email_to': finance_approvers,
                        'email_cc': 'lashok@futurenet.in'
                    }
                    self.message_post(body=message_body, subject=subject)
                    template_id = self.env['mail.mail'].sudo().create(template_data)
                    template_id.sudo().send()
                    rec.write({'send_for_approval': True, 'state': 'to approve'})
            if self.po_type == 'sales' and not self.sale_id and not self.sale_approval:
                if po_type_sales:
                    subject = 'Direct PO Approval Request'
                    body = """
                                            <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                                                <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                                    <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                                        Purchase Order Approval Request
                                                    </strong>
                                                </div>
                                                <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                                    <p>Hello Approver,</p>
    
                                                    <p>Order approval %s-%s has been raised by %s. Please review and approve or reject (with reason given) this quotation. </p>
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
                        'email_to': po_type_sales,
                    }
                    self.message_post(body=message_body, subject=subject)
                    template_id = self.env['mail.mail'].sudo().create(template_data)
                    template_id.sudo().send()
                    rec.write({'send_for_approval': True, 'state': 'to approve'})
            if self.po_type == 'regular' and not self.sale_id and not self.sale_approval:
                if po_type_regular:
                    subject = 'Direct PO Approval Request'
                    body = """
                                <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                                    <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                        <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                            Purchase Order Approval Request
                                        </strong>
                                    </div>
                                    <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                        <p>Hello Approver,</p>
    
                                        <p>Order approval %s-%s has been raised by %s. Please review and approve or reject (with reason given) this quotation. </p>
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
                        'email_to': po_type_regular,
                    }
                    self.message_post(body=message_body, subject=subject)
                    template_id = self.env['mail.mail'].sudo().create(template_data)
                    template_id.sudo().send()
                    rec.write({'send_for_approval': True, 'state': 'to approve'})

    def action_send_for_approval_type(self):
        for rec in self:
            rec.write({'send_for_approval': True, 'state': 'to approve'})
            if self.po_type:
                subject = 'Direct PO Approval Request'
                body = """
                        <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                            <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                                <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                                    Purchase Order Approval Request
                                </strong>
                            </div>
                            <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                                <p>Hello Approver,</p>

                                <p>Order approval %s-%s has been raised by %s. Please review and approve or reject (with reason given) this quotation. </p>
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
                    'email_to': self.get_mail_recipient(),
                }
                self.message_post(body=message_body, subject=subject)
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                rec.write({'send_for_approval': True, 'state': 'to approve'})

    def button_approve(self, force=False):
        self.write({'state': 'validate', 'date_approve': fields.Datetime.now()})
        subject = 'Order Approved'
        body = """
                   <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF; ">
                       <div style="height:auto; text-align: center; font-size: 30px; color: #29408c;">
                           <strong style="border-bottom: 2px solid #29408c; padding-bottom: 1px; text-transform: uppercase;">
                               Order Approved
                           </strong>
                       </div>
                       <div style="text-align: left; font-size: 20px; margin-top: 10px; color: #29408c;">
                           <p>Hello,</p>

                           <p>Order %s-%s has been approved and confirmed by %s. Please do the needful.</p>
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
            'email_to': self.user_id.login,
        }
        self.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
