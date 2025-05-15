from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, AccessError
import base64


class AccountPaymentUtrWizard(models.TransientModel):
    _name = 'account.payment.utr.wizard'
    _description = 'Payment UTR Number Generations'

    utr_number = fields.Char(string='UTR No.')
    payment_line_ids = fields.Many2many('account.payment')

    def action_action_update_utr(self):
        for record in self:
            for payment in record.payment_line_ids:
                if payment.state not in "posted":
                    raise UserError(_('Please select the Posted payment journals'))
            record.payment_line_ids.write({'bank_reference': record.utr_number})
