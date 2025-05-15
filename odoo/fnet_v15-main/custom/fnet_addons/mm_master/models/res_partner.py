# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode


class ResPartner(models.Model):
    _inherit = "res.partner"

    approved = fields.Boolean(string='Approved Customer')
    partner_target_line = fields.One2many('res.target.line', 'partner_id', 'Target')
    customer_type_name = fields.Selection([('Newgen', 'Newgen'), ('HLF', 'HLF'), ('RMKV', 'RMKV'), ('SMVCC', 'SMVCC'), ('Newak', 'Newak'), ('V-Dart', 'V-Dart'), ('TCS', 'TCS'),    
                                          ('Matrix', 'Matrix'), ('Aban', 'Aban'), ('Jayyam', 'Jayyam'), ('MIL', 'MIL'), ('Nelcast', 'Nelcast'), ('Registrar', 'Registrar')], sting="Type Customer")

    def approve(self):
        return self.write({'approved':True})

    def unapprove(self):
        return self.write({'approved':False})

class ResTaget(models.Model):
    _name = "res.target.line"
    _description = 'Target'

    @api.depends('target_amount', 'partner_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            amount = 0
            data = self.env['account.move'].search([('invoice_date','>=',line.date_from), ('invoice_date','<=',line.date_to),('type','in',('out_invoice','out_refund')),('state','=','posted'),('partner_id','=',line.partner_id.id)])
            datavals = [lines for i in data for lines in self.env['account.move.line'].search([('move_id','=', i.id)])]
            data_final = [i.price_subtotal for i in datavals for lines in self.env['product.product'].search([('id','=',i.product_id.id)]) for line_amt in self.env['product.template'].search([('id','=',lines.product_tmpl_id.id)]) if line_amt.code_new == line.account_code and i.product_uom_id.id == 1]
            print (data_final, "SSSSSSSS")
            line.update({
                    'target_achived': sum(data_final),
                })

    partner_id = fields.Many2one('res.partner', 'Partner')
    account_id = fields.Many2one('account.account', 'Account')
    account_code = fields.Char('Account Name')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    target_amount = fields.Float('Target')
    target_achived = fields.Float(compute='_compute_amount', string='Achived', readonly=True)
