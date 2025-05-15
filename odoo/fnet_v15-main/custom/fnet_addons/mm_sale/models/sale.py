# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode
import base64
import json


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        # if not vals['opportunity_id'] and not self.env.user.has_group('mm_sale.group_sale_direct_creation'):
        #     raise UserError(_("You are not allowed to create a Sale Order directly"))
        seq_date = None
        if 'date_order' in vals:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
        res.quotation_name = self.env['ir.sequence'].next_by_code('sale.quotation', sequence_date=seq_date) or _('New')
        return res

    @api.depends('purchase_count')
    def _get_purchase(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            invoices = self.env['purchase.order'].search([('sale_id', '=', order.id)])
            order.purchase_count = len(invoices)

    customer_approve = fields.Boolean('Customer Approval', copy=False)
    purchase_count = fields.Integer(string='Purchase Count', compute='_get_purchase', readonly=True)
    sale_type_id = fields.Many2one('sale.type', string="Sale Type")
    sale_sub_type_id = fields.Many2one('sale.type.line', string="Sale Sub Type")
    quote_validity = fields.Date(string="Quote Validity")
    quotation_name = fields.Char(string='Quotation Reference', required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _('New'))
    commitment_date = fields.Datetime('Delivery Date', copy=False,
                                      states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                      help="This is the delivery date promised to the customer. "
                                           "If set, the delivery order will be scheduled based on "
                                           "this date rather than product lead times.", tracking=True)
    pro_forma_number = fields.Char(string='Pro-forma Number', readonly=True, copy=False)
    pro_forma_generated = fields.Boolean(string='Pro Forma Generated', default=False)


    def generate_pro_forma(self):
        today = fields.Date.today()
        for order in self:
            company = order.company_id or order.env.company
            if company.pro_forma_sequence:
                date = order.date_order or today
                sequence = company.pro_forma_sequence
                order.pro_forma_number = sequence.with_context(ir_sequence_date=date).next_by_id()
                order.pro_forma_generated = True

    # @api.onchange('sale_type_id')
    # def onchange_sale_type(self):
    #     for rec in self:
    #         if rec.sale_type_id.payment_term_id:
    #             rec.payment_term_id = rec.sale_type_id.payment_term_id or False

    def action_confirm(self):
        self._cust_approve()
        res = super(SaleOrder, self).action_confirm()
        return res

    def _cust_approve(self):
        if self.partner_id.approved is False:
            raise UserError(_('Update the Customer Master and get a Approval'))
        # pass

    def action_view_purchase(self):
        self.ensure_one()
        domain = [('sale_id', '=', self.id)]
        return {
            'name': _('Purchase'),
            'domain': domain,
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                        Documents are attached to the tasks of your project.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>'''),
            'limit': 80,
            'context': "{'default_sale_id': %d}" % (self.id)
        }

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({'sale_type_id': self.sale_type_id.id, 'sales_sub_types': self.sale_sub_type_id.id})
        return res

    def action_quotation_send(self):
        res = super(SaleOrder, self).action_quotation_send()
        template = self.env.ref('sale.email_template_edi_sale', False)
        pdf = self.env.ref('mm_sale.sale_quotation_customer_report')
        if pdf:
            template.report_template = pdf
        return res

    def order_line_details(self):
        order_lines = []
        no = 1
        for rec in self.order_line.filtered(lambda x: x.display_type == False):
            if rec.product_id:
                line = {'no': no, 'description': rec.name, 'qty': rec.product_uom_qty, 'price': rec.price_unit,
                        'total': rec.price_subtotal, 'taxes': rec.tax_id.description}
                order_lines.append(line)
                no += 1
        return order_lines

    def get_tax_totals(self, obj):
        tax_totals = json.loads(obj.tax_totals_json)['groups_by_subtotal']['Untaxed Amount']
        print("---", obj.tax_totals_json, "--obj.tax_totals_json--")
        values = []
        cgst = 0.0
        sgst = 0.0
        igst = 0.0
        for tax in tax_totals:
            if tax['tax_group_name'] == 'CGST':
                cgst += tax['tax_group_amount']
            elif tax['tax_group_name'] == 'SGST':
                sgst += tax['tax_group_amount']
            elif tax['tax_group_name'] == 'IGST':
                igst += tax['tax_group_amount']
        values.append({'cgst': cgst, 'sgst': sgst, 'igst': igst})
        print("---", values, "--cgst--")
        return values

    def get_tax_amt(self, obj, amount):
        amt = obj.currency_id.amount_to_text(amount)
        return amt
    def get_bank(self, obj):
        final = []
        data = {}
        for i in obj.company_id.partner_id.bank_ids:
            data['bank_holder'] = i.acc_holder_name
            data['bank_number'] = i.acc_number
            data['bank_name'] = i.bank_id.name
            data['bank_ifsc'] = i.bank_id.bic
        final.append(data)
        return final

    def action_late_delivery_alert(self):
        return {
            'name': 'Late Delivery Alert',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'late.delivery.alert',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_alert_id': self.id}
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ordered_delivery_date = fields.Date(string='Delivery Date')

    def action_delivery_date(self):
        action = self.env.ref('mm_sale.action_sale_order_delivery_date').read()[0]
        action['context'] = {'default_sale_order_line_id': self.id,
                             'default_order_delivery_date': self.ordered_delivery_date}
        return action

    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()

        if self.env.user.company_id.state_id.id == self.order_id.partner_shipping_id.state_id.id:
            self.tax_id = [(6, 0, self.product_id.product_tmpl_id.taxes_id.ids)]
        else:
            self.tax_id = [(6, 0, self.product_id.product_tmpl_id.state_taxes_ids.ids)]
        return result


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quotation_margin_level = fields.Float(string="Default Margin Level(%s)", default=4.00, readonly=False)
    use_quotation_margin_level = fields.Boolean("Default Margin Level(%s)",
                                                config_parameter='mm_sale.use_quotation_margin_level')


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super()._prepare_invoice_values(order, name, amount, so_line)
        if order.sale_type_id:
            res["sale_type_id"] = order.sale_type_id.id
        if order.sale_sub_type_id:
            res['sales_sub_types'] = order.sale_sub_type_id.id

        return res


class ResUsers(models.Model):
    _inherit = 'res.users'

    incharge_id = fields.Many2one('res.users', string="Incharge")
