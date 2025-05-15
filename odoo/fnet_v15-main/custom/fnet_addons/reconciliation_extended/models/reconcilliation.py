from odoo import models, fields, api, exceptions
import re
from odoo.exceptions import ValidationError

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    reconcill_reason = fields.Text("Unreconcile Reason")


class PaymentRequest(models.Model):
    _inherit = 'payment.request'

    description = fields.Text("Description")
    cancel_reason = fields.Char("Cancel Reason")
    reject_reason = fields.Char("Reject Reason")
    user_id = fields.Many2one('res.users', string='Requested By', tracking=True, default=lambda self: self.env.user)#
class UnreconcileHistory(models.Model):
    _name = 'unreconcile.history'

    user_id = fields.Many2one('res.users', string="Unreconciled Person")
    date = fields.Date('Reconcile Date')
    reconcill_reason = fields.Text("Unreconcile Reason")
    account_move_id = fields.Many2one('account.move', string="Account Move")

class PaymentTracker(models.Model):
    _name = 'payment.tracker'

    user_id = fields.Many2one('res.partner', string="Vendor")
    description = fields.Text("Description")
    amount = fields.Integer("Amount")
    budget_or_un_budget = fields.Text("Budget / Un budget")
    remarks = fields.Text("Remarks")


