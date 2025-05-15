from odoo import api, models, fields, _


class PaymentRequestWizard(models.TransientModel):
    _name = 'payment.request.wizard'
    _description = 'Payment Request'

    request_id = fields.Many2one('payment.request', string='Payment Request')
    payment_request_lines = fields.Many2many('account.payment.register', string='Payment Request Lines')

    def action_register_payments(self):
        for line in self.payment_request_lines:
            line.action_create_payments()
        self.request_id.write({'state': 'paid'})