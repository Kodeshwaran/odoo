from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    allow_pro_forma = fields.Boolean('Allow Pro-Forma Invoices')
    pro_forma_sequence = fields.Many2one('ir.sequence', string='Pro-forma sequence')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_pro_forma = fields.Boolean('Allow Pro-Forma Invoices', related='company_id.allow_pro_forma', readonly=False)
    pro_forma_sequence = fields.Many2one(related='company_id.pro_forma_sequence', readonly=False)



