# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    old_number = fields.Char(string="Old Invoice Number")

    old_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Old Status')

    is_duplicate = fields.Boolean(string="is duplicate")

    old_origin = fields.Char('Old Origin')

    old_payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'paid')
    ], string='Old Payment Status')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    old_invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Old Invoice Status')

    old_origin = fields.Char('Old origin')

    old_opportunity_id = fields.Char('Old Opportunity ID')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    old_invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Old Billing Status')


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    old_opportunity_id = fields.Char('Old Opportunity ID')



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    j_name = fields.Char(string="Old Move Name")
    old_name = fields.Char(string="Old Name")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    effective_date_copy = fields.Datetime('Effective Date Copy')
    state_copy = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status')
    old_name = fields.Char('Old Name')
