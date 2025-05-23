# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import UserError


class BankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def button_draft(self):
        self.state = 'open'

    def button_cancel(self):
        return super(BankStatement, self.with_context(bank_statement_cancel=True)).button_cancel()


class BankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def cancel(self):
        if not self.env.context.get('bank_statement_cancel'):
            for line in self:
                if line.statement_id.state == 'confirm':
                    raise UserError(_("Please set the bank statement to New before canceling."))
        return super(BankStatementLine, self).cancel()
