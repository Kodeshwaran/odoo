from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import base64
from num2words import num2words
from datetime import date
import xlsxwriter
import json


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
    get_invoice_report = fields.Binary('Invoice Report', readonly=True)
    invoice_report_name = fields.Char('Filename', size=64, readonly=True)

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
            if not rec.cancel_reason:
                raise ValidationError(_('Please fill the cancel reason'))
            mail_body = """<table border="0" cellpadding="0" cellspacing="0" width="1000"style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                                <tr>
                                    <td valign="top" style="padding: 0px 10px;">
                                        <div style="font-size: 13px; margin: 0px; padding: 0px;">
                                            Dear {name},
                                            <br/>
                                             I wanted to inform you that the payment request you submitted on {date} for {prf} has been canceled.
                                            <br/><br/>
                                             Thank you for understanding.
                                             <br/><br/>
                                             Best regards,<br/>
                                             {user}
                                        </div>
                                    </td>
                                </tr>
                            </table>""".format(name=rec.user_id.name, date=rec.create_date.date(), prf=rec.request_number, user=self.env.user.name)

            mail_subject = f"Cancellation of Payment Request {rec.request_number}"
            to_email = rec.user_id.login
            md_logins = ', '.join(
                user.login for user in self.env['res.users'].search([])
                if user.has_group('mm_master.group_company_managing_director')
            )

            self.env['mail.mail'].create({
                'subject': mail_subject,
                'email_to': to_email,
                'email_cc': md_logins,
                'body_html': mail_body,
            }).send()
            rec.state = 'cancel'

    def action_rejected(self):
        for rec in self:
            if not rec.reject_reason:
                raise ValidationError(_('Please fill the reject reason'))
            mail_body = """<table border="0" cellpadding="0" cellspacing="0" width="1000"style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                                            <tr>
                                                <td valign="top" style="padding: 0px 10px;">
                                                    <div style="font-size: 13px; margin: 0px; padding: 0px;">
                                                        Dear {name},
                                                        <br/>
                                                         I wanted to inform you that the payment request you submitted on {date} for {prf} has been rejected.
                                                        <br/><br/>
                                                         Thank you for understanding.
                                                         <br/><br/>
                                                         Best regards,<br/>
                                                         {user}
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>""".format(name=rec.user_id.name, date=rec.create_date.date(),
                                                           prf=rec.request_number, user=self.env.user.name)

            mail_subject = f"Rejection of Payment Request {rec.request_number}"
            to_email = rec.user_id.login

            self.env['mail.mail'].create({
                'subject': mail_subject,
                'email_to': to_email,
                'body_html': mail_body,
            }).send()
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
            'name': "Payment Request " + self.request_number,
            'type': 'binary',
            'datas': data_record,
            'store_fname': self.request_number + ".pdf",
            'mimetype': 'application/x-pdf',
            'res_model': 'payment.request',
            'res_id': self.id,
        }
        attachment = self.env['ir.attachment'].create(ir_values)

        account_move_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', 'in', self.account_move_ids.ids)
        ])

        new_attachments = []
        for record in account_move_attachments:
            copied_data = record.copy_data()[0]
            new_attachment = self.env['ir.attachment'].create(copied_data)
            new_attachments.append(new_attachment.id)

        all_attachments = [attachment.id] + new_attachments


        mail_template = self.env.ref('payment_request.email_payment_request_for_vendor_payment')
        mail_template.attachment_ids = [(6, 0, all_attachments)]
        mail_template.send_mail(self.id, force_send=True)
        self.env['ir.attachment'].browse(new_attachments).unlink()
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

    def generate_invoice_details_report(self):
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Invoice Report.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 11, 'align': 'vcenter', 'valign': 'center'})
        parent_format = workbook.add_format({'font_size': 13, 'bold': True, 'align': 'center'})
        center_format = workbook.add_format({'font_size': 11, 'align': 'center'})
        left_format = workbook.add_format({'font_size': 11, 'align': 'left'})
        right_format = workbook.add_format({'font_size': 11, 'align': 'right'})
        amount_format = workbook.add_format({'font_size': 11, 'align': 'right', 'num_format': '#,##0.00'})
        margin_format = workbook.add_format({'font_size': 11, 'align': 'right', 'num_format': '0.00'})
        total_format = workbook.add_format(
            {'font_size': 13, 'bold': True, 'align': 'left', 'valign': 'center', 'bg_color': '#FFCCCB'})
        format1.set_text_wrap()
        format2 = workbook.add_format({'font_size': 12, 'align': 'center'})
        format3 = workbook.add_format({'font_size': 12, 'align': 'left', 'num_format': 'dd-mm-yyyy'})

        bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        bold_1 = workbook.add_format({'align': 'right', 'valign': 'vcenter'})

        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 20)

        sheet.merge_range('B3:E3', 'INVOICE REPORT', bold)
        sheet.write(5, 0, 'Customer Invoice No.', parent_format)
        sheet.write(5, 1, 'Total Amount', parent_format)
        sheet.write(5, 2, 'Payment Status', parent_format)
        sheet.write(5, 3, 'Sale Order No.', parent_format)
        sheet.write(5, 4, 'Total Amount', parent_format)
        sheet.write(5, 5, 'Invoice Status', parent_format)
        sheet.write(5, 6, 'PO No.', parent_format)
        sheet.write(5, 7, 'Vendor Name', parent_format)
        sheet.write(5, 8, 'Total Amount', parent_format)
        sheet.write(5, 9, 'Status', parent_format)

        rows = 6
        for bill in self.account_move_ids.filtered(lambda x: x.cust_invoice_id):
            sale_order = self.env['sale.order'].search([('name', '=', bill.cust_invoice_id.invoice_origin)])
            sale_order_json = ''
            if sale_order:
                sale_order_json = json.loads(sale_order.tax_totals_json)
            sheet.write(rows, 0, bill.cust_invoice_id.name if bill.cust_invoice_id else '', center_format)
            if bill and bill.cust_invoice_id.currency_id != self.env.company.currency_id:
                amount_total_company = bill.cust_invoice_id.currency_id._convert(bill.cust_invoice_id.amount_total,
                                                                                 self.env.company.currency_id,
                                                                                 self.env.company,
                                                                                 bill.cust_invoice_id.invoice_date)
                sheet.write(rows, 1, amount_total_company if bill.cust_invoice_id else '', amount_format)
            else:
                sheet.write(rows, 1, bill.cust_invoice_id.amount_total if bill.cust_invoice_id else '', amount_format)
            sheet.write(rows, 2, dict(bill.cust_invoice_id._fields['payment_state'].selection).get(
                bill.cust_invoice_id.payment_state) if bill.cust_invoice_id else '', center_format)
            sheet.write(rows, 3, bill.cust_invoice_id.invoice_origin if bill.cust_invoice_id else '', center_format)
            if sale_order and sale_order.currency_id != self.env.company.currency_id:
                amount_so_total_company = sale_order.currency_id._convert(sale_order_json['amount_total'],
                                                                          self.env.company.currency_id,
                                                                          self.env.company, sale_order.date_order)
                sheet.write(rows, 4, amount_so_total_company if sale_order else '', amount_format)
            else:
                sheet.write(rows, 4, sale_order_json['amount_total'] if sale_order else '', amount_format)
            sheet.write(rows, 5, dict(sale_order._fields['invoice_status'].selection).get(
                sale_order.invoice_status) if sale_order else '', center_format)
            purchase_orders = self.env['purchase.order'].search(
                [('sale_id', '!=', False), ('sale_id', '=', sale_order.id)])
            if purchase_orders:
                for po in purchase_orders:
                    po_json = json.loads(po.tax_totals_json)
                    vendor_bill = self.env['account.move'].search([('invoice_origin', '=', po.name)])
                    sheet.write(rows, 6, po.name, center_format)
                    sheet.write(rows, 7, po.partner_id.name, center_format)
                    if po and po.currency_id != self.env.company.currency_id:
                        amount_po_total_company = po.currency_id._convert(po_json['amount_total'],
                                                                          self.env.company.currency_id,
                                                                          self.env.company, po.date_order)
                        sheet.write(rows, 8, amount_po_total_company, amount_format)
                    else:
                        sheet.write(rows, 8, po_json['amount_total'] if po else '', amount_format)
                    sheet.write(rows, 9, dict(po._fields['state'].selection).get(po.state), center_format)
                    if vendor_bill:
                        for b in vendor_bill:
                            sheet.write(rows, 10, b.name, center_format)
                            if b and b.currency_id != self.env.company.currency_id:
                                amount_vb_total_company = b.currency_id._convert(b.amount_total,
                                                                                 self.env.company.currency_id,
                                                                                 self.env.company, b.invoice_date)
                                sheet.write(rows, 11, amount_vb_total_company, amount_format)
                            else:
                                sheet.write(rows, 11, b.amount_total if b else '', amount_format)
                            sheet.write(rows, 12, dict(b._fields['state'].selection).get(b.state), center_format)
                            sheet.write(rows, 13, dict(b._fields['payment_state'].selection).get(b.payment_state),
                                        center_format)
                            rows += 1
                    else:
                        rows += 1
            else:
                rows += 1
        workbook.close()
        fo = open(url + 'Invoice Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodestring(data)
        self.write({'get_invoice_report': out, 'invoice_report_name': 'Invoice Report.xlsx'})


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



