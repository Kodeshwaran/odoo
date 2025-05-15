from odoo import models,fields,_
from odoo import api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError,except_orm

class Crm_Lead(models.Model):
    _inherit='crm.lead'

    req = fields.Boolean('Product')

    @api.onchange('partner_id')
    def onchange_product_id(self):
        if self.partner_id.id == False:
            self.req = True


