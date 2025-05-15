from openerp import models, api, fields
import datetime
# ~ from odoo.tools import amount_to_text_en


# class BalanceConfirmation(models.AbstractModel):
#     _name = 'report.balance_confirmation_letter.balance_confirm_report'

    # @api.model
    # def get_report_values(self, ids, data=None):
    #     report_obj = self.env['balance.confirmation.wizard'].browse(ids)
    #     return {
    #         'doc_ids': ids,
    #         'doc_model': 'balance.confirmation.wizard',
    #         'docs': report_obj,
    #         'data': data,
    #     }

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     report_obj = self.env['res.partner'].browse(data.get('partner_id'))
    #     self.env.context.get('active_id')
    #     return {
    #         'doc_ids': report_obj,
    #         'doc_model': self.env['res.partner'],
    #         'data': data,
    #         'docs': report_obj,
    #         # 'time': time,
    #         # 'lines': res,
    #         # 'sum_credit': self._sum_credit,
    #         # 'sum_debit': self._sum_debit,
    #         # 'get_taxes': self._get_taxes,
    #         # 'company_id': self.env['res.company'].browse(
    #         #     data['form']['company_id'][0]),
    #     }

