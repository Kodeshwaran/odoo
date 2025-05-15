from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mt_cc_mail = fields.Char(string="CC Mail", related="company_id.mt_cc_mail", readonly=False)
    mt_to_mail = fields.Char(string="TO Mail", related="company_id.mt_to_mail", readonly=False)
    mt_days = fields.Integer(string="Days", related="company_id.mt_days", readonly=False)
    is_mt = fields.Boolean(string="Monitoring Threshold Alert Mail", related="company_id.is_mt", readonly=False)

class ResCompany(models.Model):
    _inherit = 'res.company'

    mt_cc_mail = fields.Char(string="CC Mail")
    mt_to_mail = fields.Char(string="TO Mail")
    mt_days = fields.Integer(string="Days")
    is_mt = fields.Boolean(string="Monitoring Threshold Alert Mail")
