# from odoo import models, fields
from odoo import models, fields, api, exceptions
import re
from odoo.exceptions import ValidationError
class UnreconcileReasonWizard(models.TransientModel):
    _name = 'unreconcile.reason.wizard'
#     _description = 'Wizard to capture unreconcile reason'
#
#     reconcill_reason = fields.Text(string="Unreconcile Reason")
#
#     def action_confirm(self):
#         self.ensure_one()
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'trigger_unreconcile',
#             'params': {
#                 'reconcill_reason': self.reconcill_reason,
#             }
#         }