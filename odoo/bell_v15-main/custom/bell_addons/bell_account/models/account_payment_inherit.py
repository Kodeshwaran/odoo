from odoo import api, fields, models, _
MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}


class AccountPayment(models.Model):
    _inherit = "account.payment"

    cheque_number = fields.Char("Cheque/DD Number")
    cheque_date = fields.Date("Cheque Date")
    note = fields.Char("Notes")
    cheque_narration = fields.Char("Cheque Narration")
    reference = fields.Char("Reference")


    def _get_move_vals(self, journal=None):
        """ Return dict to create the payment move
        """
        result = super(AccountPayment, self)._get_move_vals(journal)
        result.update({
            'note': self.note or '',
            #~ 'cheque_narration': self.narration or '',
            'reference': self.reference or '',
            'cheque_number': self.cheque_number or '',
            'cheque_date': self.cheque_date or '',
        })

        return result

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        invoice_defaults = rec.get('invoice_ids')
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            rec['note'] = invoice['note'] or ''
            rec['cheque_narration'] = invoice['narration'] or ''
            rec['reference'] = invoice['reference'] or ''
            rec['cheque_number'] = invoice['cheque_number'] or ''
            rec['cheque_date'] = invoice['cheque_date'] or ''
        return rec


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    narration = fields.Char("Narration")
    
    #~ @api.model
    #~ def default_get(self, fields):
        #~ rec = super(AccountRegisterPaymentInherit, self).default_get(fields)
        #~ invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        #~ if invoice_defaults and len(invoice_defaults) == 1:
            #~ invoice = invoice_defaults[0]
            #~ rec['narration'] = invoice['cheque_narration'] or ''           
        #~ return rec

    def _create_payment_vals_from_wizard(self):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        res.update({'cheque_narration': self.narration})
        return res

    # def _prepare_payment_vals(self, invoices):
    #     '''Create the payment values.
    #
    #     :param invoices: The invoices that should have the same commercial partner and the same type.
    #     :return: The payment values as a dictionary.
    #     '''
    #     amount = self._compute_payment_amount(invoices) if self.multi else self.amount
    #     payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
    #     return {
    #         'journal_id': self.journal_id.id,
    #         'cheque_narration': self.narration,
    #         'payment_method_id': self.payment_method_id.id,
    #         'payment_date': self.payment_date,
    #         'communication': self.communication, # DO NOT FORWARD PORT TO V12 OR ABOVE
    #         'invoice_ids': [(6, 0, invoices.ids)],
    #         'payment_type': payment_type,
    #         'amount': abs(amount),
    #         'currency_id': self.currency_id.id,
    #         'partner_id': invoices[0].commercial_partner_id.id,
    #         'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
    #     }
