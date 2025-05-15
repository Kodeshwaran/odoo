import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError
class crm_lead(models.Model):
        _inherit = "crm.lead"
        
       
        attachment_number = fields.Integer(compute='_get_attachment_number', string="Number of Attachments") 
        attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'crm.lead')], string='Attachments')		
        @api.multi
        def _get_attachment_number(self):
            read_group_res = self.env['ir.attachment'].read_group(
                [('res_model', '=', 'crm.lead'), ('res_id', 'in', self.ids)],
                ['res_id'], ['res_id'])
            attach_data = dict((res['res_id'], res['res_id_count']) for res in read_group_res)
            for record in self:
                record.attachment_number = attach_data.get(record.id, 0)
        
        @api.multi
        def action_get_attachment_tree_view(self):
            attachment_action = self.env.ref('base.action_attachment')
            action = attachment_action.read()[0]
            action['context'] = {'default_res_model': self._name, 'default_res_id': self.ids[0]}
            action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
            return action
          
