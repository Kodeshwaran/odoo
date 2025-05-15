from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class Lead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def create(self,vals):
        partner = super(Lead, self).create(vals)
        phonecall = self.env['crm.phonecall']
        phonecall.create({
            'date': partner.create_date,
            'partner_id': partner.partner_id.id,
            'name': 'lead',
            'description':partner.name,
            'partner_phone': partner.phone,
            'user_id': partner.user_id.id,
            'state':'open',
            'partner_mobile': partner.mobile,
            'lead_id':partner.id,
        })        
        return partner
    
    
    @api.multi
    def write(self, vals):
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = fields.Datetime.now()
        if vals.get('user_id') and 'date_open' not in vals:
            vals['date_open'] = fields.Datetime.now()
        # stage change with new stage: update probability and date_closed
        if vals.get('stage_id') and 'probability' not in vals:
            vals.update(self._onchange_stage_id_values(vals.get('stage_id')))
        if vals.get('probability') >= 100 or not vals.get('active', True):
            vals['date_closed'] = fields.Datetime.now()
        elif vals.get('probability') < 100:
            vals['date_closed'] = False
        partner = super(Lead, self).write(vals)
        if self.next_activity_id.id == 1:
            if self.type=='opportunity':        
                phonecall = self.env['crm.phonecall']
                phonecall.create({
                    'date': self.date_action,
                    'partner_id': self.partner_id.id,
                    'name': 'reply',
                    'description':self.title_action,
                    'partner_phone': self.phone,
                    'user_id': self.user_id.id,
                    'state':'open',
                    'partner_mobile': self.mobile,
                    'lead_id':False,
                    'opportunity_id':self.id
                })
        if self.type:
            if self.type == 'opportunity':
                phonecall = self.env['crm.phonecall'].search([('lead_id','=',self.id)])
                phonecall.update({
                    'date': self.create_date,
                    'partner_id': self.partner_id.id,
                    'name': 'opportunity',
                    'description':self.name,
                    'partner_phone': self.phone,
                    'user_id': self.user_id.id,
                    'state':'open',
                    'partner_mobile': self.mobile,
                    'lead_id':False,
                    'opportunity_id':self.id
                })
        return partner
        
    @api.multi
    def create_call_in_queue(self):
        for opp in self:
            self.env['crm.phonecall'].create({
                'name': 'customermeetingnew',
                'duration': 0,
                'user_id': self.env.user.id,
                'opportunity_id': opp.id,
                'partner_id': opp.partner_id.id,
                'state': 'open',
                'partner_phone': opp.phone or opp.partner_id.phone,
                'partner_mobile': opp.partner_id.mobile,
                'in_queue': True,
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }

    # Function call by the stat button
    @api.multi
    def create_custom_call_in_queue(self):
        return {
            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'src_model': "crm.phonecall",
            'res_model': "crm.schedule_phonecall",
            'multi': "True",
            'target': 'new',
            'context': {
                'default_name': 'customermeetingnew',
                'default_partner_id': self.partner_id.id,
                'default_user_id': self.env.uid,
                'default_opportunity_id': self.id,
                'default_partner_phone': self.phone or self.partner_id.phone,
                'default_partner_mobile': self.mobile or self.partner_id.mobile,
                'default_team_id': self.team_id.id,
            },
            'views': [[False, 'form']],
        }
                
    @api.multi
    def log_new_phonecall(self):
        return {
            'name': _('Log a call'),
            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'src_model': "crm.phonecall",
            'res_model': "crm.phonecall.log.wizard",
            'multi': "True",
            'target': 'new',
            'context': {
                        'default_opportunity_id': self.id,
                        'default_name': 'customermeetingnew',
                        #~ 'default_duration': self.duration,
                        'default_description': self.description,
                        'default_opportunity_name': self.oppor_order,
                        'default_opportunity_planned_revenue': self.planned_revenue,
                        'default_opportunity_title_action': self.title_action,
                        'default_opportunity_date_action': self.date_action,
                        'default_opportunity_probability': self.probability,
                        'default_partner_id': self.partner_id.id,
                        'default_partner_name': self.partner_id.name,
                        'default_partner_email': self.partner_id.email,
                        'default_partner_phone': self.phone or self.partner_id.phone,
                        'default_partner_image_small': self.partner_id.image_small,},
                        'default_show_duration': self._context.get('default_show_duration'),
            'views': [[False, 'form']],
            'flags': {
                'headless': True,
            },
        }
    

    hold_reason = fields.Char('Hold Reason')
    drop_reason = fields.Char('Drop Reason')
    
    
    @api.multi
    def action_set_drop(self):
        """ Drop semantic: probability = 0, active = False """
        return self.write({'probability': 0, 'active': False})
        
        
    @api.multi
    def action_set_hold(self):
        """ Hold semantic: probability = 50, active = True """
        return self.write({'probability': 50, 'active': True})
        
    
class crm_lead_lost(models.TransientModel):
    _inherit = 'crm.lead.lost'
    
    reason_val = fields.Selection([('hold', 'Hold'),('lost', 'Drop')],string='Type',track_visibility='onchange', default='hold',required=True)
    hold_reason_val = fields.Char('Hold Reason')
    drop_reason_val = fields.Char('Drop Reason')
    
    
    @api.multi
    def action_drop_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.write({'drop_reason': self.drop_reason_val})
        return leads.action_set_drop()
        
        
    @api.multi
    def action_hold_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.write({'hold_reason': self.hold_reason_val})
        return leads.action_set_hold()
    
        
class crm_phonecall(models.Model):
    
    _inherit = 'crm.phonecall'
    
    name = fields.Selection([('database','Customer Research'),('call','Customer Appointment fixing'),('reply','Mail read/reply'),
    ('order','Order followup'),('meeting','Vendor followup'),('portal','Registration-Vendor/portal'),('quotation','Proposal/Quotation'),
    ('followup','Other followup'),('payment','Payment followup'),
    ('tender','Tender search/reading/preparation'),('internalmeeting','Internal meeting'),('report','Report/Review'),
    ('travel','Travel/Out of office'),('customermeetingexisting','Customer meeting-Existing'),('customermeetingnew','Customer meeting- New'),
    ('lead','Lead'),('opportunity','Opportunity'),], string='Call Summary',required=True)
    lead_id = fields.Many2one('crm.lead','Lead')
    opportunity_id = fields.Many2one('crm.lead', 'Opportunity',
        ondelete='cascade', track_visibility='onchange')
    partner_mobile = fields.Char('Mobile')
    
    
class phone_call_crm_inherit(models.TransientModel):
    _inherit = "crm.schedule_phonecall"
    
    
    @api.multi
    def action_schedule(self):
        Phonecall = self.env['crm.phonecall']

        phonecall_to_cancel_id = self._context.get('phonecall_to_cancel')
        if phonecall_to_cancel_id:
            phonecall_to_cancel = Phonecall.browse(phonecall_to_cancel_id)
            phonecall_to_cancel.write({
                'state': 'cancel',
                'in_queue': False,
            })
        Phonecall.create({
            'name': 'customermeetingnew',
            'user_id': self.user_id.id,
            'date': self.date,
            'description':self.name,
            'team_id': self.team_id.id,
            'partner_id': self.partner_id.id,
            'partner_phone': self.partner_phone,
            'partner_mobile': self.partner_mobile,
            'opportunity_id': self.opportunity_id.id,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload_panel',
        }
        
    
    
class Meeting(models.Model):
    _inherit = 'calendar.event'    
    
        
    @api.model
    def create(self, values):
        if not 'user_id' in values:  # Else bug with quick_create when we are filter on an other user
            values['user_id'] = self.env.user.id

        # compute duration, if not given
        if not 'duration' in values:
            values['duration'] = self._get_duration(values['start'], values['stop'])

        meeting = super(Meeting, self).create(values)

        final_date = meeting._get_recurrency_end_date()
        # `dont_notify=True` in context to prevent multiple notify_next_alarm
        meeting.with_context(dont_notify=True).write({'final_date': final_date})
        meeting.with_context(dont_notify=True).create_attendees()

        # Notify attendees if there is an alarm on the created event, as it might have changed their
        # next event notification
        if not self._context.get('dont_notify'):
            if len(meeting.alarm_ids) > 0:
                self.env['calendar.alarm_manager'].notify_next_alarm(meeting.partner_ids.ids)
        
        
        Phonecall = self.env['crm.phonecall']
        Phonecall.create({
            'partner_id': meeting.opportunity_id.partner_id.id,
            'name': 'internalmeeting',
            'description':values['name'],
            'date': meeting.start,
            'partner_phone':meeting.opportunity_id.phone,            
            'user_id': meeting.opportunity_id.user_id.id,
            'state':'open',
            'opportunity_id': meeting.opportunity_id.id,
            'duration':meeting.duration,            
        })       
        
        return meeting                                
