from odoo import fields, models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    expense_bill = fields.Boolean(string="Expense")


    def _get_default_journal(self):
        if self._context.get('default_move_type') == 'in_invoice' and not self._context.get('default_expense_bill'):
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1, order="id asc")
            return journal
        elif self._context.get('default_expense_bill'):
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1, order="id desc")
            return journal
        return super(AccountMove, self)._get_default_journal()

