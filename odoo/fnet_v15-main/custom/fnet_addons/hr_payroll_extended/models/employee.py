from odoo import models, fields, api, _
from odoo.exceptions import UserError
from calendar import monthrange


class HREmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    is_admin = fields.Boolean('Is Admin', default=False)
    entry_account_id = fields.Many2one('account.account', string="Entry Account")

    is_canteen = fields.Boolean('Is Canteen', default=False)
    debit_entry_account_id = fields.Many2one('account.account', string="Debit Entry Account")
    credit_entry_account_id = fields.Many2one('account.account', string="Credit Entry Account")