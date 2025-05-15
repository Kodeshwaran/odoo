# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError

class crm_stage(models.Model):
        _inherit = ['crm.stage']

        sequence=fields.Integer('Sequence', help="Used to order stages. Lower is better.")
        
        #
        # @api.multi
        # def unlink(self):
        #     raise UserError(_('You Cannot Delete Any Stages!!!'))
        #     return models.Model.unlink(self)
