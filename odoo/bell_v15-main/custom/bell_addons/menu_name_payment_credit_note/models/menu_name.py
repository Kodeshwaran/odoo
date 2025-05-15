from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    def name_get(self):
        TYPES = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Credit Note'),
            'in_refund': _('Vendor Debit note'),
            'entry': _('Journal Entry'),
        }
        result = []
        for inv in self:
            result.append((inv.id, "%s %s" % (TYPES[inv.move_type], inv.name or '')))
        return result
