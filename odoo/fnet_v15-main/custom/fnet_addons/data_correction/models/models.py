# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import binascii
import base64
import tempfile
import xlrd
import csv
from odoo.exceptions import UserError, Warning
import datetime
from datetime import timedelta
import pytz


class DataCorrectionWizard(models.TransientModel):
    _name = 'data.correction.wizard'
    _description = 'Data Correction Wizard'

    document = fields.Selection([('attachment', 'Attachments'), ('partner', 'Contact'), ('sale', 'Sale'), ('purchase', 'Purchase'), ('account', 'Account')], string="Document", default='sale', required=True)
    document_type = fields.Selection([('in_invoice', 'Customer Invoice'), ('in_refund', 'Credit Note'), ('out_invoice', 'Vendor Bill'), ('out_refund', 'Debit Note')], string="Document Type")
    update_by = fields.Selection([('file', 'XLS File'), ('csv', 'CSV File'), ('record', 'Filter Name')], default='file', required=True)
    record_name = fields.Char("Record", help="Comma(,) separated records need to entered.")
    filename = fields.Char()
    file = fields.Binary("XLS file")
    value = fields.Char("Value")

    sale_ids = fields.Many2many('sale.order', string="Sales")
    purchase_ids = fields.Many2many('purchase.order', string="Purchase")
    account_ids = fields.Many2many('account.move', string="Moves")
    line_ids = fields.One2many('data.correction.line', 'wizard_id', string="Lines")
    update_to = fields.Selection([
        ('gst', 'GST No'),
        ('due_amount', 'Due Amount'),
        ('state', 'Status'),
        ('origin', 'Origin'),
        ('payment_status', 'Payment Status'),
        ('old_state', 'Old State'),
        ('old_number', 'Old Number'),
        ('date', 'Date'),
        ('narration', 'Terms and Conditions'),
        ('commitment_date', 'Commitment Date'),
        ('einvoice', 'E-invoice'),
        ('cust_invoice', "Customer Invoice")
    ], string="Update To", required=True, default='state')
    attachment_line_ids = fields.Many2many('ir.attachment', string="Attachments")

    @api.onchange('file', 'record_name')
    def onchange_records(self):
        vals = []
        if self.document == 'purchase':
            model = 'purchase.order'
        elif self.document == 'account':
            model = 'account.move'
        elif self.document == 'sale':
            model = 'sale.order'
        elif self.document == 'partner':
            model = 'res.partner'
        elif self.document == 'attachment':
            model = 'ir.attachment'
        else:
            raise(_("Please select document type...!"))
        if self.file and self.update_by == 'file':
            try:
                fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                worksheet = workbook.sheet_by_index(0)
            except Exception as E:
                raise Warning(_("Invalid file !: %s" % E))
            for row in range(worksheet.nrows):
                record = self.env[model].search(([('name', '=', worksheet.cell_value(row, 0))]))
                if record:
                    prep_val = {
                        'sale_ids': record.ids if self.document == 'sale' else False,
                        'purchase_ids': record.ids if self.document == 'purchase' else False,
                        'account_ids': record.ids if self.document == 'account' else False,
                        'partner_ids': record.ids if self.document == 'partner' else False,
                        'value': worksheet.cell_value(row, 1),
                    }
                    if self.update_to == 'narration':
                        prep_val.update({
                            'value_html': worksheet.cell_value(row, 1)
                        })
                    if self.update_to == 'einvoice':
                        prep_val.update({
                            'value_text': worksheet.cell_value(row, 1)
                        })
                    if self.update_to in ['date', 'commitment_date']:
                        dt_vl = worksheet.cell_value(row, 1)
                        if dt_vl:
                            str_dt = datetime.datetime(*xlrd.xldate_as_tuple(dt_vl, workbook.datemode))
                            prep_val.update({
                                'date_value': str_dt
                            })
                    vals.append((0, 0, prep_val))
        elif self.file and self.update_by == 'csv':
            """
            Row[0] = Name
            Row[1] = Resource Name
            Row[2] = Resource Model
            Row[3] = File Content
            Row[4] = Type
            Row[5] = Mime Type
            Row[6] = Resource Field
            Row[7] = Resource ID
            Row[8] = File Size
            Row[9] = Created by
            Row[10] = Created on
            Row[11] = Display Name
            Row[12] = Description
            """
            try:
                fp = tempfile.NamedTemporaryFile(suffix=".csv")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                with open(fp.name) as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    line_count = 0
                    for row in csv_reader:
                        if line_count == 0:
                            line_count += 1
                        else:
                            print("\n---",row,"--row--\n")
                            user_id = self.env['res.users'].search([('name', '=', row[9])])
                            res_id = self.env[row[2]].search([('name', '=', row[1].split(" (")[0])])
                            print("\n---", user_id, res_id, "--user_id, res_id--\n")
                            bytes = base64.decodebytes(row[3].encode())
                            file_cont = base64.b64encode(bytes)
                            # pdf = tempfile.NamedTemporaryFile(suffix=".pdf")
                            # pdf.write(bytes)
                            # pdf.seek(0)
                            # with open(pdf, 'rb') as output:
                            #     output.read()
                            # output.close()
                            print("---", bytes, "--bytes--")
                            vals.append((0, 0, {
                                'name': row[0],
                                'type': 'url' if row[0] == 'URL' else 'binary',
                                'datas': file_cont,
                                'store_fname': 'test',
                                'res_model': row[2],
                                'res_id': res_id.id,
                                'mimetype': 'application/x-pdf'
                            }))
                            line_count += 1
                    print("\n---", vals, "--vals--\n")
            except Exception as E:
                raise UserError(_("Invalid file !: %s" % E))
        if vals and self.document != 'attachment':
            self.line_ids = vals

    def action_update(self):
        if self.document == 'account' and self.update_to == 'origin':
            self.action_update_move_origin()
        elif self.document == 'sale' and self.update_to == 'origin':
            self.action_update_sale_origin()
        elif self.document == 'purchase' and self.update_to == 'origin':
            self.action_update_purchase_origin()
        elif self.document == 'purchase' and self.update_to == 'date':
            self.action_update_purchase_date()
        elif self.document == 'sale' and self.update_to == 'payment_status':
            self.action_update_sale_payment_status()
        elif self.document == 'account' and self.update_to == 'payment_status':
            self.action_update_move_payment_status()
        elif self.document == 'account' and self.update_to == 'due_amount':
            self.action_update_move_due_amount()
        elif self.document == 'account' and self.update_to == 'old_state':
            self.action_update_move_old_state()
        elif self.document == 'sale' and self.update_to == 'state':
            self.action_update_sale_state()
        elif self.document == 'purchase' and self.update_to == 'state':
            self.action_update_purchase_state()
        elif self.document == 'partner' and self.update_to == 'gst':
            self.action_update_partner_gst()
        elif self.document == 'account' and self.update_to == 'narration':
            self.action_update_account_narration()
        elif self.document == 'account' and self.update_to == 'commitment_date':
            self.action_update_account_commitment_date()
        elif self.document == 'account' and self.update_to == 'einvoice':
            self.action_update_account_einvoice()
        elif self.document == 'attachment' and self.update_to == 'einvoice':
            self.action_update_account_einvoice()
        elif self.document == 'account' and self.update_to == 'cust_invoice':
            self.action_update_account_cust_invoice()
        elif self.document == 'attachment':
            self.action_update_attachment()

    def action_update_attachment(self):
        vals = []
        attachment_ids = self.env['ir.attachment']
        try:
            fp = tempfile.NamedTemporaryFile(suffix=".csv")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            with open('/home/ubuntu/attachments.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        line_count += 1
                    else:
                        print("\n---", row, "--row--\n")
                        user_id = self.env['res.users'].search([('name', '=', row[9])])
                        res_id = self.env[row[2]].search([('name', '=', row[1].split(" (")[0])])
                        if res_id:
                            print("\n---", user_id, res_id, "--user_id, res_id--\n")
                            bytes = base64.decodebytes(row[3].encode())
                            file_cont = base64.b64encode(bytes)
                            # pdf = tempfile.NamedTemporaryFile(suffix=".pdf")
                            # pdf.write(bytes)
                            # pdf.seek(0)
                            # with open(pdf, 'rb') as output:
                            #     output.read()
                            # output.close()
                            print("---", bytes, "--bytes--")
                            values ={
                                'name': row[0],
                                'type': 'url' if row[0] == 'URL' else 'binary',
                                'datas': file_cont,
                                'store_fname': 'test',
                                'res_model': row[2],
                                'res_id': res_id.id,
                                'mimetype': row[5]
                            }
                            attachment_ids += attachment_ids.create(values)
            
        except Exception as E:
            raise UserError(_("Invalid file !: %s" % E))
        if attachment_ids:
            self.attachment_line_ids = attachment_ids.ids

    def action_update_account_cust_invoice(self):
        for line in self.line_ids:
            if self.document == 'account':
                for al in line.account_ids:
                    invoice = self.env['account.move'].search([('name', '=', )])
                    self.env.cr.execute(
                        """update account_move set cust_invoice_id='%s' where id=%s;""" % (line.value, al.id))

    def action_update_account_einvoice(self):
        for line in self.line_ids:
            if self.document == 'account' and line.value_text:
                einvoice_obj = self.env['account.einvoice']
                rp_value = line.value_text.replace("null", "None")
                dict_val = eval(rp_value)
                ack_dt = dict_val['AckDt'] if 'AckDt' in dict_val else False
                dt_val = False
                if ack_dt:
                    dt_val = datetime.datetime.strptime(ack_dt, '%Y-%m-%d %H:%M:%S') - timedelta(hours=5, minutes=30)
                vals = {
                    'status': dict_val['Status'] if 'Status' in dict_val else False,
                    'invoice_id': line.account_ids[0].id,
                    'ackno': dict_val['AckNo'] if 'AckNo' in dict_val else False,
                    'ackdt': dt_val,
                    'irn': dict_val['Irn'] if 'Irn' in dict_val else False,
                    'signedinvoice': dict_val['SignedInvoice'] if 'SignedInvoice' in dict_val else False,
                    'signedqrcode': dict_val['SignedQRCode'] if 'SignedQRCode' in dict_val else False,
                    'ewbno': dict_val['EwbNo'] if 'EwbNo' in dict_val else False,
                    'ewbdt': dict_val['EwbDt'] if 'EwbDt' in dict_val else False,
                    'ewbvalidtill': dict_val['EwbValidTill'] if 'EwbValidTill' in dict_val else False,
                    'remarks': dict_val['Remarks'] if 'Remarks' in dict_val else False,
                    'response': line.value,
                }
                einv_id = einvoice_obj.create(vals)
                line.account_ids[0].write({'einvoice_id': einv_id.id})

    def action_update_account_commitment_date(self):
        for line in self.line_ids:
            if self.document == 'account' and line.date_value:
                for al in line.account_ids:
                    self.env.cr.execute("""update account_move set date_commitment='%s' where id=%s;""" % (line.date_value, al.id))

    def action_update_account_narration(self):
        for line in self.line_ids:
            if self.document == 'account' and line.value_html:
                for al in line.account_ids:
                    self.env.cr.execute(
                        """update account_move set narration='%s' where id=%s;""" % (
                        line.value_html, al.id))

    def action_update_partner_gst(self):
        for line in self.line_ids:
            if self.document == 'partner' and line.value:
                for al in line.partner_ids:
                    self.env.cr.execute("""update res_partner set vat='%s',l10n_in_gst_treatment='regular' where id=%s;""" % (line.value, al.id))

    def action_update_purchase_state(self):
        for line in self.line_ids:
            if self.document == 'purchase' and line.value:
                for al in line.purchase_ids:
                    self.env.cr.execute("""update purchase_order set state='%s' where id=%s;""" %(line.value, al.id))

    def action_update_sale_state(self):
        for line in self.line_ids:
            if line.document == 'sale' and line.value:
                for al in line.sale_ids:
                    self.env.cr.execute("""update sale_order set state='%s' where id=%s;""" %(line.value, al.id))

    def action_update_move_old_state(self):
        for line in self.line_ids:
            if self.document == 'account':
                for al in line.account_ids:
                    self.env.cr.execute("""update account_move set payment_state='%s' where id=%s;""" % (line.value, al.id))

    def action_update_move_due_amount(self):
        for line in self.line_ids:
            if line.document == 'account' and (line.value or line.value2):
                for al in line.account_ids:
                    val = float(line.value)
                    val1 = float(line.value2)
                    self.env.cr.execute("""update account_move set amount_residual='%s' where id=%s;""" % (val, al.id))
                    self.env.cr.execute("""update account_move set amount_residual_signed='%s' where id=%s;""" % (val1, al.id))

    def action_update_sale_payment_status(self):
        for line in self.line_ids:
            if line.document == 'sale' and line.value:
                for al in line.sale_ids:
                    self.env.cr.execute("""update sale_order set invoice_status='%s' where id=%s;""" % (line.value, al.id))

    def action_update_sale_origin(self):
        count = 0
        for line in self.line_ids:
            if line.document == 'sale' and line.value:
                for al in line.sale_ids:
                    count += 1
                    self.env.cr.execute("""update sale_order set origin='%s' where id=%s;""" %(line.value, al.id))
        return {"status": "Successfully updated %s documents" % count}

    def action_update_purchase_origin(self):
        raise Warning("Coming Soon...")

    def action_update_move_origin(self):
        for line in self.line_ids:
            if self.document == 'account':
                for al in line.account_ids:
                    self.env.cr.execute("""update account_move set invoice_origin='%s' where id=%s;""" %(line.value, al.id))

    def action_update_purchase_date(self):
        for line in self.line_ids:
            if self.document == 'purchase' and line.date_value:
                for al in line.purchase_ids:
                    self.env.cr.execute("""update purchase_order set date_order='%s' where id=%s;""" %(line.date_value, al.id))

    def action_update_move_payment_status(self):
        for line in self.line_ids:
            if self.document == 'account':
                for al in line.account_ids:
                    self.env.cr.execute("""update account_move set payment_state='%s' where id=%s;""" % (line.value, al.id))


class DataCorrectionLine(models.TransientModel):
    _name = 'data.correction.line'
    _description = 'Data Correction Wizard Line'

    wizard_id = fields.Many2one('data.correction.wizard', string="Wizard")
    document = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase'), ('account', 'Account')], string="Document", default='sale', related='wizard_id.document')
    sale_ids = fields.Many2many('sale.order', string="Sale")
    purchase_ids = fields.Many2many('purchase.order', string="Purchase")
    account_ids = fields.Many2many('account.move', string="Move")
    partner_ids = fields.Many2many('res.partner', string="Partner")
    value = fields.Char("Value")
    value2 = fields.Char("Value2")
    value_html = fields.Html("HTML Value")
    value_text = fields.Text("Text Value")
    date_value = fields.Date("Date Value")
    name = fields.Char('Name')
    res_model = fields.Char('Resource Model')
    res_name = fields.Char('Resource Name')
    res_id = fields.Char('Resource ID')
    type = fields.Selection([('file', 'File'), ('url', 'URL')])
    datas = fields.Binary(string='Attachment')
    file_size = fields.Integer('File Size')
    created_by = fields.Many2one('res.users', string='Created By')
    created_date = fields.Datetime('Created On')

