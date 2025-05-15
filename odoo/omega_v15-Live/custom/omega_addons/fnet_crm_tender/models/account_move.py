from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _get_journal(self):
        res = []
        ttype = self._context.get('journal_type')
        if ttype:
            res = self.env['account.journal'].search([('name', '=', ttype)], limit=1)
        else:
            res = self._get_default_journal()
        return res

    aed_amount = fields.Float("AED Amount")
    bank_name = fields.Many2one("res.partner.bank", string="Bank Name")
    exchange_rate = fields.Float("Exchange Rate")
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain="[('company_id', '=', company_id)]",
                                 default=_get_journal)
    commitment_date = fields.Datetime('Commitment Date', help="This is the delivery date promised to the customer. "
                                           "If set, the delivery order will be scheduled based on "
                                           "this date rather than product lead times.")

    @api.onchange('currency_id')
    def onchange_currency(self):
        result = {}
        banks = self.env['res.partner.bank'].search([])
        for bank in banks:
            if bank.currency_id == self.currency_id:
                self.bank_name = bank
                self.update({'exchange_rate': self.currency_id.rate})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    item_no = fields.Char('Item No', store=True)
    # product_note = fields.Html("Notes")
    name = fields.Html(string='Label', tracking=True)


class ResBank(models.Model):
    _inherit = 'res.bank'

    bic = fields.Char('Swift Code', index=True, help="Sometimes called BIC or Swift.")
