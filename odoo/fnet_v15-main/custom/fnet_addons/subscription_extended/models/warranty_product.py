# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class WarrantyProduct(models.Model):
    _inherit = 'product.product'

    warranty_product = fields.Boolean(string="Warranty/Licence", default=False)
    warranty_period = fields.Integer(string="Period",store=True)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('invoice_line_ids')
    def _onchange_warranty_id(self):
        warranty_product = []
        for rec in self:
            for line in rec.invoice_line_ids:
                if line.warranty_product:
                    warranty_product.append(line.product_id.id)
                else:
                    continue
            if warranty_product:
                rec.warranty_product = True
            else:
                rec.warranty_product = False

    @api.onchange('warranty_lines')
    def _onchange_warranty_lines(self):
        for rec in self:
            if not rec.warranty_lines:
                self.warranty_created = False
            else:
                pass


    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    warranty_product = fields.Boolean(string="Warranty", default=False)
    warranty_created = fields.Boolean(string="Warranty Created",default=False)
    warranty_lines = fields.One2many('warranty.lines','move_id',string="Warranty Lines")

    def action_create_warranty(self):
        for rec in self:
            invoice_lines = rec.invoice_line_ids.filtered(lambda x: x.product_id.warranty_product == True)

        for line in invoice_lines:
            values = {
                'product_id': line.product_id.id,
                'start_date': self.invoice_date,
                'period': line.product_id.warranty_period,
                'move_id':self.id,
            }
            lines = self.env['warranty.lines']
            lines.create(values)

        return self.write({'warranty_created': True})


class WarrantyLines(models.Model):
    _name = 'warranty.lines'

    move_id = fields.Many2one('account.move',string="Move ID")
    partner_id = fields.Many2one('res.partner', related='move_id.partner_id', store=True)
    invoice_id = fields.Many2one('account.move', related='move_id',string="Invoice Name")
    renewal_type = fields.Many2one('invoice.renewal.type', string='Type')
    product_id = fields.Many2one('product.product',string="Product")
    start_date = fields.Date(string="Start Date")
    period = fields.Integer(string="Warranty Period(Months)")
    end_date = fields.Date(string="End Date", compute='_compute_end_date', store=True)
    serial_number = fields.Char(string='Serial Number')
    invoice_date = fields.Date(string="Invoice Date", related='move_id.invoice_date')

    @api.depends('start_date','period')
    def _compute_end_date(self):
        for rec in self:
            if rec.start_date and rec.period:
                rec.end_date = rec.start_date + relativedelta(months=rec.period)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    warranty_product = fields.Boolean(string="Warranty", related="product_id.warranty_product")


class InvoiceRenewalType(models.Model):
    _name = 'invoice.renewal.type'
    _description = 'Renewal Type'

    name = fields.Char(string='Name')


