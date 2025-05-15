# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    sale_id = fields.Many2one('sale.order', 'Sale')
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('validate', 'Approved'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    def button_confirm(self):
        for rec in self.order_line:
            if rec.product_qty == 0:
                raise ValidationError("One of the line items have 0 quantity. To Confirm, please delete that line.")
        for po_line in self.order_line:
            if po_line.sale_line_id:
                po_quantity = 0
                so_quantity = po_line.sale_line_id.product_uom_qty
                po_line_ids = self.env['purchase.order.line'].search([('sale_line_id', '=', po_line.sale_line_id.id), ('state', '=', 'purchase')])
                for line in po_line_ids:
                    po_quantity += line.product_qty
                if so_quantity == po_quantity:
                    dublicate_po_lines = self.env['purchase.order.line'].search(
                        [('sale_line_id', '=', po_line.sale_line_id.id), ('state', '!=', 'purchase')])
                    for po in dublicate_po_lines:
                        self.env.cr.execute(""" update purchase_order_line set product_qty = 0.0 where id=%s""" % po.id)
                if so_quantity == po_quantity:
                    raise ValidationError('Sum of all purchase order has been exceeded.')
                remaining_qty = so_quantity - po_quantity
                if po_line.product_qty > remaining_qty:
                    raise ValidationError(_('You can confirm with purchase quantity as %s for %s' %
                                            (remaining_qty, po_line.name)))
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            if order.state not in ['draft', 'sent', 'validate']:
                continue
            order._add_supplier_to_product()
            order.write({'state': 'purchase'})
            order._create_picking()
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        for line in self.order_line:
            po_quantity = 0
            so_quantity = line.sale_line_id.product_uom_qty
            dublicate_po_lines = self.env['purchase.order.line'].search([('sale_line_id', '=', line.sale_line_id.id), ('state', '=', 'purchase')])
            for dub_l in dublicate_po_lines:
                po_quantity += dub_l.product_qty
            if po_quantity == so_quantity:
                pos = self.env['purchase.order.line'].search(
                    [('sale_line_id', '=', line.sale_line_id.id), ('state', '!=', 'purchase')])
                pos.write({'product_qty': 0, 'price_unit': 0})
                po_ids = pos.mapped('order_id')
                for po in po_ids:
                    if sum(po.order_line.mapped('product_qty')) < 1:
                        po.write({'state': 'cancel'})
        return res

    # def cancel_quantity(self):
    #     for line in self.order_line:
    #         dublicate_po_lines = self.env['purchase.order.line'].search([('sale_line_id', '=', line.sale_line_id.id), ('id', '!=', line.id)])
    #         po_ids = dublicate_po_lines.mapped('order_id')
    #         for dub_l in dublicate_po_lines:
    #             dub_l.write({'product_qty': 0, 'price_unit': 0})
    #         for po in po_ids:
    #             if sum(po.order_line.mapped('product_qty')) < 1:
    #                 po.write({'state': 'cancel'})

    def get_tax_amt(self, obj, amount):
        amt = obj.currency_id.amount_to_text(amount)
        return amt


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    sale_line_id = fields.Many2one('sale.order.line', 'Sale')
    # is_line = fields.Boolean()

    def cancel_quantity(self):
        for rec in self:
            rec.write({'product_qty': 0, 'price_unit': 0})

class SupplierCreation(models.Model):
    _name = 'supplier.creation'
    _rec_name = 'supplier_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    supplier_name = fields.Char(string="Supplier Name")
    # address fields
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string="Country Code")
    technical_name = fields.Char('Name')
    tech_mobile_no = fields.Char('Mobile')
    tech_email = fields.Char('Email')
    commercial_name = fields.Char('Name')
    commercial_mobile_no = fields.Char('Mobile')
    commercial_email = fields.Char('Email')
    statutory_details = fields.Text('Statutory details (Firm registration, GST etc..)')
    supplier_type = fields.Selection([('oem', 'OEM'), ('distributor', 'Distributor'), ('reseller', 'Reseller')], string="Nature of supplier (Dealer / Manufacturer)")
    product_ids = fields.Many2many('product.product', string="Products")
    delivery_type = fields.Selection([('free', 'Free'), ('extra_cost', 'Extra Cost'), ('to_pay', 'To Pay')], string="Mode of Delivery")
    point_delivery_type = fields.Selection([('futurenet', 'Futurenet'), ('customer', 'Customer'), ('both', 'Both')], string="Point of Delivery")
    technical_support = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Technical Support After Sales")
    refund_policy = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Return / Refund Policies in Place")
    credit_facility = fields.Text('Credit Facility')
    response_time = fields.Text('Response Time')
    assessor_conclusion = fields.Text("Assessor's Conclusion")
    submitted_date = fields.Date('Date')
    md_approved_date = fields.Date('Date')
    bu_approved_date = fields.Date('Date')
    submitted_name = fields.Many2one('res.users', 'Name')
    bu_approved_name = fields.Many2one('res.users', 'Name')
    md_approved_name = fields.Many2one('res.users', 'Name')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('bu_approve', 'BU Approved'), ('md_approve', 'MD Approved'), ('rejected', 'Rejected')], default="draft", string="Technical Support After Sales")
    delivery_lead_time = fields.Text(string='Delivery Lead Time')
    created_partner = fields.Many2one('res.partner', string='Created Partner')
    product_type_id = fields.Many2one('purchase.product.types', string='Product Type')

    def action_submit(self):
        self.write({'state': 'submitted',
                    'submitted_name': self.env.user.id,
                    'submitted_date': fields.Date.today(),
                    })
        bu_head_approvers = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('mm_purchase.group_vendor_creation_bu_head'):
                bu_head_approvers.append(user.login)
        subject = 'Vendor Evaluation - Approval'
        body = """<p>Please approve the vendor evaluation.<br/>
                <br/>
                <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" href="%s">
                    View Vendor Evaluation Form
                </a>
                <br/>
                <br/>
              Thank You.</p>""" % (self.get_mail_url())
        message_body = body
        template_data = {
            'subject': subject,
            'body_html': message_body,
            'email_from': self.env.user.email,
            'email_to': (str(bu_head_approvers).strip('[]').replace("', '", ", ")).strip("'"),
        }
        self.message_post(body=message_body, subject=subject)
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

    # def action_verify(self):
    #     self.write({
    #         'state': 'verified',
    #
    #     })
    #     bu_head_approvers = []
    #     users = self.env['res.users'].search([])
    #     for user in users:
    #         if user.has_group('mm_purchase.group_vendor_creation_bu_head'):
    #             bu_head_approvers.append(user.login)
    #     subject = 'Vendor Evaluation - Approval'
    #     body = """<p>Please approve the vendor evaluation.<br/>
    #             <br/>
    #             <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" href="%s">
    #                 View Vendor Evaluation Form
    #             </a>
    #             <br/>
    #             <br/>
    #           Thank You.</p>""" % (self.get_mail_url())
    #     message_body = body
    #     template_data = {
    #         'subject': subject,
    #         'body_html': message_body,
    #         'email_from': self.env.user.email,
    #         'email_to': (str(bu_head_approvers).strip('[]').replace("', '", ", ")).strip("'"),
    #     }
    #     self.message_post(body=message_body, subject=subject)
    #     template_id = self.env['mail.mail'].sudo().create(template_data)
    #     template_id.sudo().send()

    def action_bu_approve(self):
        self.write({
            'state': 'bu_approve',
            'bu_approved_name': self.env.user.id,
            'bu_approved_date': fields.Date.today(),
        })
        for rec in self:
            create_vendors = self.env['res.partner'].create({
                'company_type': 'company',
                'name': rec.supplier_name,
                'street': rec.street,
                'street2': rec.street2,
                'city': rec.city,
                'state_id': rec.state_id.id,
                'zip': rec.city,
                'country_id': rec.country_id.id,
            })
            create_vendors.approve()
            rec.write({'created_partner': create_vendors.id})
        # md_approver = []
        # users = self.env['res.users'].search([])
        # for user in users:
        #     if user.has_group('partner_creation.group_partner_creation_md'):
        #         md_approver.append(user.login)
        # subject = 'Vendor Evaluation - Approval'
        # body = """<p>Please approve the vendor evaluation.<br/>
        #                 <br/>
        #                 <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;" href="%s">
        #                     View Vendor Evaluation Form
        #                 </a>
        #                 <br/>
        #                 <br/>
        #               Thank You.</p>""" % (self.get_mail_url())
        # message_body = body
        # template_data = {
        #     'subject': subject,
        #     'body_html': message_body,
        #     'email_from': self.env.user.email,
        #     'email_to': (str(md_approver).strip('[]').replace("', '", ", ")).strip("'"),
        # }
        # self.message_post(body=message_body, subject=subject)
        # template_id = self.env['mail.mail'].sudo().create(template_data)
        # template_id.sudo().send()

    def action_md_approve(self):
        self.write({
            'state': 'md_approve',
            'md_approved_name': self.env.user.id,
            'md_approved_date': fields.Date.today(),
        })
        for rec in self:
            create_vendors = self.env['res.partner'].create({
                'company_type': 'company',
                'name': rec.supplier_name,
                'street': rec.street,
                'street2': rec.street2,
                'city': rec.city,
                'state_id': rec.state_id.id,
                'zip': rec.city,
                'country_id': rec.country_id.id,
            })
            create_vendors.approve()

    def action_reject(self):
        self.write({'state': 'rejected'})

    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return url

    def action_view_open_supplier(self):
        return {
            'name': _('Vendor'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.created_partner.id)]
        }

class PurchaseProductTypes(models.Model):
    _name = 'purchase.product.types'

    name = fields.Selection([('laptop', 'Laptop'),
                           ('desktop', 'Desktop'),
                           ('server', 'Server & Storage'),
                           ('switches', 'Switches'),
                           ('networking', 'Networking')], string="Product Type", copy=False, required=True)