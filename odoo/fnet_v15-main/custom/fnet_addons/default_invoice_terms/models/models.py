# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    is_default_invoice = fields.Boolean("is Default in Invoice")
    is_default_bill = fields.Boolean("is Default in Bill")


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_terms(self):
        if self._context.get('default_move_type') == 'out_invoice':
            return self.env['account.payment.term'].search([('is_default_invoice', '=', True)], limit=1).id

    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
                                              check_company=True,
                                              readonly=True, states={'draft': [('readonly', False)]}, default=_get_terms)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_terms(self):
        return self.env['account.payment.term'].search([('is_default_invoice', '=', True)], limit=1).id

    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", default=_get_terms, store=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            payment_term = self.env['account.payment.term'].search([('is_default_invoice', '=', True)], limit=1)
            if payment_term:
                self.payment_term_id = payment_term.id
            else:
                self.payment_term_id = self.partner_id.property_payment_term_id.id if self.partner_id.property_payment_term_id else False