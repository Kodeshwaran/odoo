from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    sales_mail_to = fields.Char(string="Sales Mail TO")
    sales_mail_cc = fields.Char(string="Sales Mail CC")
