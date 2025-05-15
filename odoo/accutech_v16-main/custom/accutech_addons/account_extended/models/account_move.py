from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.osv import expression


class AccountMoveExtended(models.Model):
    _inherit = "account.move"

    suitable_journal_ids = fields.Many2many(
        'account.journal',
        compute='_compute_suitable_journal_ids',
    )
    to_self = fields.Char("To")
    delivery_basis = fields.Selection([
        ('direct', 'As soon as possible'),
        ('one', 'When all products are ready')],
        string='Delivery Basis', required=True, default='direct',
        help="If you deliver all products at once, the delivery order will be scheduled based on the greatest "
        "product lead time. Otherwise, it will be based on the shortest.")

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = m.invoice_filter_type_domain or 'general'
            company_id = m.company_id.id or self.env.company.id
            if m.move_type == 'entry':
                domain=[('company_id', '=', company_id)]
            else:
                domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    cheque_number = fields.Char("Cheque Number")
    cheque_date = fields.Date("Cheque Date")

class ResBankInherit(models.Model):
    _inherit = "res.bank"

    branch = fields.Char("Branch")