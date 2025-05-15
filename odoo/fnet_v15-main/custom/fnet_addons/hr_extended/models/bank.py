from odoo import models, fields, api, _

class BankCode(models.Model):
    _inherit = 'res.partner.bank'

    ifsc_code = fields.Char('IFSC Code')