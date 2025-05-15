# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_imported = fields.Boolean(string="Is Imported")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_imported = fields.Boolean(string="Is Imported")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    old_name = fields.Char(string='Old Name')
    old_state = fields.Selection([
        ('draft', 'Quotation'),
        ('to_approve', 'Waiting for Approve'),
        ('approved', 'Approved'),
        ('sent', 'Quotation Sent'),
        ('won', 'Quotation Won'),
        ('drop', 'Quotation Drop'),
        ('lost', 'Quotation Lost'),
        ('hold', 'Quotation Hold'),
        ('amendmend', 'Amendmend'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Old Status')
    old_invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ], string='Old Invoice Status')
    is_imported = fields.Boolean(string="Is Imported")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    old_invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ], string='Old Invoice Status')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    old_name = fields.Char(string="Old Name")
    old_state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('bid received', 'Bid Received'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Old Status')
    old_invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Old Billing Status')
    is_imported = fields.Boolean(string="Is Imported")

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    old_invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Old Billing Status')


class AccountMove(models.Model):
    _inherit = 'account.move'

    old_name = fields.Char(string="Old Name")
    old_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Old Status')
    old_payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
            ], string="Old Payment Status")
    is_imported = fields.Boolean(string="Is Imported")
    old_po_number = fields.Char(string="Old PO Number")
    old_po_date = fields.Date(string="Old PO Date")
    old_lead_name = fields.Char(string='Old Lead Name')
    old_origin = fields.Char(string='Old Origin')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    old_name = fields.Char(string="Old Name")
    old_state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Old Status')
    is_imported = fields.Boolean(string="Is Imported")


class StockMove(models.Model):
    _inherit = 'stock.move'

    old_state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Old Status')
    old_qty_done = fields.Float(string="Old Done")
