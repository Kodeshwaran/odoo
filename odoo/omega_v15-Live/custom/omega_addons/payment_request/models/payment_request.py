from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import base64
from num2words import num2words
from datetime import date


class PaymentRequest(models.Model):
    _name = 'payment.request'
    _description = 'Payment Request'
    _rec_name = 'request_number'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name')
    request_number = fields.Char(string='PR No.', required=True, copy=False, readonly=True,
                                 default=lambda self: _('New'), store=True, tracking=True)
    state = fields.Selection([
        ('finance_approval', 'Waiting for Finance Approval'),
        ('md_approval', 'Waiting for MD Approval'),
        ('approved', 'Approved'),
        ('paid','Paid'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')
    ], default='finance_approval', tracking=True)
    account_move_ids = fields.Many2many('account.move', string='Bills')
    payment_request_date = fields.Date(string='Date', default=fields.Date.today())
    payment_approved_date = fields.Date('Approved Date')
    total_due_amount = fields.Float(string='Total Due Amount', compute='_compute_total_due_amount')
    email = fields.Char(string='Email', default='lashok@futurenet.in')
    payment_ids = fields.Many2many('account.payment')
    bill_select = fields.Boolean('Select')
    url_link = fields.Char('Url')
    cancel_reason = fields.Text('Reset to Draft Reason', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    file_data = fields.Binary('Download File')
    filename = fields.Char()

    # reset to draft
    def action_state_draft(self):

        for rec in self:
            rec.state = 'finance_approval'

    # Finance approve button

    def action_finance_approval(self):
        for rec in self:
            rec.state = 'md_approval'
            rec.action_payment_request_email()
            rec.print_account_details()
            for invoices in rec.account_move_ids:
                invoices.payment_request_number = rec.request_number

    # MD final approval
    def action_md_approved(self):
        for rec in self:
            rec.state = 'approved'
            rec.payment_approved_date = fields.date.today()
            print(rec.payment_approved_date, 'approved Date')
            report_template_id = self.env.ref('payment_request.report_partner_bills_details')._render_qweb_pdf(self.id)
            data_record = base64.b64encode(report_template_id[0])
            ir_values = {
                'name': "Payment Request" + ' ' + self.request_number,
                'type': 'binary',
                'datas': data_record,
                'store_fname': data_record,
                'mimetype': 'application/x-pdf',
            }
            attachment = self.env['ir.attachment'].create(ir_values)

            mail_template = self.env.ref('payment_request.email_payment_request_md_approved')
            mail_template.write({'attachment_ids': [(6, 0, [attachment.id])]})
            mail_template.send_mail(self.id, force_send=True)

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_rejected(self):
        for rec in self:
            rec.state = 'reject'

    def action_draft_payment_request(self):
        action = self.env.ref('payment_request.action_payment_request_cancel_reason').read()[0]
        action['context'] = {'default_payment_request_id': self.id}
        return action

    @api.model
    def create(self, vals):
        print('vals', vals)
        if vals.get('request_number', _('New')) == _('New'):
            vals['request_number'] = self.env['ir.sequence'].next_by_code('payment.request') or _('New')
        res = super(PaymentRequest, self).create(vals)
        return res

    @api.depends('account_move_ids')
    def _compute_total_due_amount(self):
        print('total Due Amount')
        for rec in self:
            for line in rec.account_move_ids:
                rec.total_due_amount += abs(line.amount_residual_signed)
        print("end")


    def action_payment_request_email(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%s&model=payment.request&view_type=form' % (self.id)
        self.write({'url_link': base_url})

        report_template_id = self.env.ref('payment_request.report_partner_bills_details')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Payment Request" + ' ' + self.request_number,
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        attachment = self.env['ir.attachment'].create(ir_values)

        mail_template = self.env.ref('payment_request.email_payment_request_for_vendor_payment')
        mail_template.write({'attachment_ids': [(6, 0, [attachment.id])]})
        mail_template.send_mail(self.id, force_send=True)
        return True

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''

        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.account_move_ids.ids,
                # 'active_ids': acc,
                'return_payments': True,
                'return_model': 'payment.request',
                'return_field': 'payment_ids',
                'return_record': self.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_open_payments(self):
        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.payment_ids.ids)],
        }
        return action

    def action_open_bills(self):
        action = {
            'name': _('Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'tree,form',
            # 'views': [(self.env.ref('account.view_invoice_tree').id, 'list')],
            'domain': [('id', 'in', self.account_move_ids.ids)],
        }
        return action


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        payments = self._create_payments()

        if self._context.get('dont_redirect_to_payments'):
            return True
        if self._context.get('return_payments'):
            model = self._context.get('return_model')
            record = self._context.get('return_record')
            field = self._context.get('return_field')
            record_obj = self.env[model].browse(record)
            record_obj.write({field: [(6, 0, payments.ids)]})
            record_obj.write({'state' : 'paid'})
            print(record_obj.payment_ids)
        print(self._context)

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }

        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action


class Payments(models.Model):
    _inherit = 'account.payment'

    utr_number = fields.Char('UTR No.')
    cheque_number = fields.Char(string='Cheque Number')
    cheque_date = fields.Date(string='Cheque date')

    def action_utr_number_update(self):
        action = self.env.ref('payment_request.action_payment_update_utr_number').read()[0]
        action['context'] = {'default_payment_line_ids': self.ids}
        return action

    def action_cheque_number_update(self):
        action = self.env.ref('payment_request.action_payment_update_cheque_number').read()[0]
        partner_name = self.mapped('partner_id.name')[0]
        count_of_invoice = len(self.ids)
        print(count_of_invoice)
        if count_of_invoice == 1:
            action['context'] = {'default_payment_line_ids': self.ids, 'default_cheque_name': partner_name}
        else:
            action['context'] = {'default_payment_line_ids': self.ids}

        return action

    def payment_advice_mail(self):
        for rec in self:
            if not rec.partner_id.bank_ids:
                raise ValidationError(_('Please fill the "%s" account details in customer master'% rec.partner_id.name))
            if not rec.bank_reference:
                raise ValidationError(_('Please fill the UTR Bank Reference Number'))
            if not rec.partner_id.payment_receipt_email_to:
                raise ValidationError(_('Please fill the "%s" payment receipt email_to address in customer master'% rec.partner_id.name))
        for rec in self:
            report_template_id = self.env.ref('payment_request.action_report_vendor_payment_receipt')._render_qweb_pdf(rec.id)
            data_record = base64.b64encode(report_template_id[0])
            ir_values = {
                'name': "Payment Advice.pdf",
                'type': 'binary',
                'datas': data_record,
                'store_fname': data_record,
                'mimetype': 'application/x-pdf',
            }
            attachment = self.env['ir.attachment'].create(ir_values)
            mail_template = self.env.ref('payment_request.email_account_payment_advice_email_template')
            if not rec.partner_id.payment_receipt_email_to:
                raise ValidationError(_('Please enter the "Email To" Address'))
            email = {
                'email_to': rec.partner_id.payment_receipt_email_to or '',
                'email_cc': rec.partner_id.payment_receipt_email_cc or '',
                'partner_to': False,
            }
            mail_template.write(email)
            mail_template.write({'attachment_ids': [(6, 0, [attachment.id])]})
            mail_template.send_mail(rec.id, force_send=True)

    def amount_in_text(self):
        for rec in self:
            amount_text = 'Zero'
            if rec.amount:
                amount_text = num2words(rec.amount, lang='en_IN').title()
            return amount_text

    def payment_advice_date(self):
        today = date.today()
        today_date = today.strftime("%d/%m/%Y")
        return today_date



