
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError


class crm_team(models.Model):
    _inherit = "crm.team"
    manager_id = fields.Many2one('res.users', 'Team Manager')
                         

   
