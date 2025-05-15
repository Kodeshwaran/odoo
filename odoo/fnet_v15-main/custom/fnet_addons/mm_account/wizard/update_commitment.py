# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)



class SaleOrderLineWizard(models.TransientModel):
    _name = 'commitment.date.update.wizard'
    _description = 'Commitment Date Update in Account Move'

    date_commitment = fields.Date(string='Commitment Date',  required=True)
    old_date_commitment = fields.Date(string='Old Commitment Date')
    move_id = fields.Many2one('account.move', 'Move ID')

    def action_commitment_date_update(self):
        if self.move_id:
            self.env.cr.execute("""update account_move set date_commitment='%s' where id=%s;""" % (self.date_commitment, self.move_id.id))
            if self.old_date_commitment:
                self.move_id.sudo().message_post(body="Commitment Date: %s --> %s" % (self.old_date_commitment.strftime('%d-%m-%Y'), self.date_commitment.strftime('%d-%m-%Y')))
            else:
                self.move_id.sudo().message_post(
                    body="Commitment Date Updated: %s" % self.date_commitment.strftime('%d-%m-%Y'))
            # self.move_id.write({'date_commitment': self.date_commitment})
        else:
            raise UserError(_('Please refresh your screen and try again.'))
