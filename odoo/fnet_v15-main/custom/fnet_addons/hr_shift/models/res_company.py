from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    shift_cc_mail = fields.Char(string="CC Mail")
