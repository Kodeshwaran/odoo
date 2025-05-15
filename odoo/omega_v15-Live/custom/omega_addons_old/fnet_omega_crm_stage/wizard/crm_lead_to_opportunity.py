# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    

    @api.multi
    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        self.ensure_one()
        values = {
            'team_id': self.team_id.id,
        }

        if self.partner_id:
            s=[]
            values['partner_id'] = self.partner_id.id
            stage = self.env['crm.lead'].browse(self._context.get('active_ids', []))
            if not stage.contact:
				self.env.cr.execute('''select id from res_partner where parent_id=%d'''%(self.partner_id.id))
				re=self.env.cr.fetchall()
				for i in range(len(re)):
						s.append(re[i][0])	
				dfg=self.env['crm.lead'].browse(stage.id)
				dfg.update({'contact':s,})
        if self.name == 'merge':
            leads = self.opportunity_ids.merge_opportunity()
            if leads.type == "lead":
                values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
                self.with_context(active_ids=leads.ids)._convert_opportunity(values)
            elif not self._context.get('no_force_assignation') or not leads.user_id:
                values['user_id'] = self.user_id.id
                leads.write(values)
        else:
            leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))
            values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
            self._convert_opportunity(values)
            for lead in leads:
                if lead.partner_id and lead.partner_id.user_id != lead.user_id:
                    self.env['res.partner'].browse(lead.partner_id.id).write({'user_id': lead.user_id.id})

        return leads[0].redirect_opportunity_view()
