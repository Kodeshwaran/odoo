 # -*- coding: utf-8 -*-
import base64
import datetime
import logging
import psycopg2
import threading

from email.utils import formataddr

from odoo import _, api, fields, models
from odoo import tools
from odoo.addons.base.ir.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, AccessError

class crm_lead_contact(models.Model):
          _name='crm.lead.contact'
          crm_id=fields.Many2one('crm.lead','Crm Connect')
          name=fields.Char('Name', select=True)
          title=fields.Many2one('res.partner.title', 'Title')
          function=fields.Char('Job Position')
          email=fields.Char('Email')
          phone=fields.Char('Phone')
          mobile=fields.Char('Mobile')
          comment=fields.Text('Notes')



class crm_lead(models.Model):

         _inherit = ['crm.lead']

         partner_id = fields.Many2one('res.partner','Customer')
         date_action = fields.Datetime('Next Activity Date', index=True)
         parent_id=fields.Many2one('res.partner', 'Related Lead', select=True)
         stage_name= fields.Char(related='stage_id.name',string="stage",store=True)
         stage_ids1=fields.Many2one(related='stage_id',string="stage",store=True, track_visibility='onchange',relation="crm.stage")
         state=fields.Boolean(string="stage",store=True,default=False)
         ded=fields.Boolean(string="decision",store=True,default=False)
         test=fields.Integer(related='partner_id.id',string='Test',store=True)
         child_ids=fields.One2many('res.partner', 'crm_id', 'Contact*',help='You Can Create Contact If There Is No Available Contact Persons')
         child_id=fields.One2many('crm.lead.contact','crm_id','Available Contact Persons' ,copy=True)
         contact=fields.Many2many('res.partner','crm_leads_rel','partner_id','tagss_id','Contacts*',store=True)
         date_order = fields.Datetime(string='Order Date',default=fields.Datetime.now)
         managernotes=fields.Text('Sales Team Manager Remark')
         manager_decision=fields.Selection([('yes','Yes'),('no','No')],'Sales Team Manager Approval',default='no')
         sel=fields.Boolean(string="Status Of manager_decision",store=True,default=False)
         phone=fields.Char('Phone*')
         email_from=fields.Char('Email*', size=128, help="Email address of the contact", select=1)
         visible_drop=fields.Boolean('DROP BUTTON visible_drop')
         vam = fields.Many2one('res.users','Virtual Account Manager',default=lambda self: self.env.user)
         stages = fields.Char('Stage')
         meeting_count = fields.Integer('# Meetings', compute='_compute_meeting_counts')
         regrets = fields.Text("Reason for Regrets")
         
         @api.multi
         def _compute_meeting_counts(self):
             meeting_data = self.env['calendar.event'].read_group([('opportunity_id', 'in', self.ids)], ['opportunity_id'], ['opportunity_id'])
             mapped_data = {m['opportunity_id'][0]: m['opportunity_id_count'] for m in meeting_data}
             for lead in self:
                 a = len(lead.next_activity_id)
                 b = mapped_data.get(lead.id, 0)
                 lead.meeting_count = a+b

         def _add_followers(self):
             user_ids = []
             employee = self.team_id
             self.env.cr.execute('select user_id from crm_team where id = %d'%(employee))
             emp = self.env.cr.fetchall()
             self.message_subscribe_users(user_ids=emp[0][0])

         @api.model
         def create(self, vals):
             sheet = super(crm_lead, self).create(vals)
             if vals.get('team_id'):
                 sheet._add_followers()
             return sheet

         @api.multi
         def action_schedule_meeting(self):
             """ Open meeting's calendar view to schedule meeting on current opportunity.
                 :return dict: dictionary value for created Meeting view
             """
             count = None
             self.ensure_one()
             action = self.env.ref('calendar.action_calendar_event').read()[0]
             partner_ids = self.env.user.partner_id.ids
             if self.partner_id:
                 partner_ids.append(self.partner_id.id)
             action['context'] = {
                 'search_default_opportunity_id': self.id if self.type == 'opportunity' else False,
                 'default_opportunity_id': self.id if self.type == 'opportunity' else False,
                 'default_partner_id': self.partner_id.id,
                 'default_partner_ids': partner_ids,
                 'default_team_id': self.team_id.id,
                 'default_name': self.name,
             }
             vals = {
                 'name': self.name,
                 'start':self.date_action,
                 'stop':self.date_action,
                 'opportunity_id':self.ids[0],
                 'location':self.title_action,
             }
             self.env.cr.execute("""select opportunity_id as id from calendar_event""")
             get = self.env.cr.dictfetchall()
             opp_id = [x['id'] for x in get]
             if vals['opportunity_id'] not in opp_id:
                 if vals['start'] != False and vals['stop'] != False:
                     calendar = self.env['calendar.event'].create(vals)
             else:
                  if vals['start'] != False and vals['stop'] != False:
                      calendar = self.env['calendar.event'].write(vals)
             return action

         @api.onchange('partner_id')
         def onchange_contact(self):
             gg = self.partner_id.ids
             if gg !=[]:
                 res = self.env['res.partner'].search([('parent_id','in',gg)])
                 prod=[]
                 for i in res.ids:
                     prod.append(i)
                 return {'domain':{'contact':[('id','in',prod)]}}

         @api.onchange('partner_id')
         def onchange_contact_remove(self):
             result={}
             result['value'] ={'contact':False}
             return result

         @api.model
         @api.onchange('manager_decision')
         def send_mail_to_manager(self):
                lead_obj = self.env['crm.lead'].browse(self.ids)
                mail_mail = self.env['mail.mail']
                mail_ids=[]
                template_obj = self.env['mail.template']
                if self.manager_decision=='yes':
                    body_html=' '
                    sss=' '
                    partner=''
                    cost=''
                    self.env.cr.execute("""select name,partner_id,planned_revenue from crm_lead where id=%d"""%(self._origin.id))
                    dd = self.env.cr.fetchall()
                    for i in range(len(dd)):
                        body_html+='        '+str(dd[i][0])
                        self.env.cr.execute("""select name from res_partner where id=%d"""%(dd[i][1]))
                        pp=self.env.cr.fetchall()
                        partner+='      '+str(pp[0][0])
                        cost+='     '+str(dd[i][2])
                    self.env.cr.execute("""SELECT DISTINCT
                      res_users.login
                      FROM res_groups_users_rel
                      JOIN res_groups
                      ON res_groups.id = res_groups_users_rel.gid
                      JOIN public.res_users
                      ON res_groups_users_rel.uid = res_users.id
                      JOIN ir_module_category
                      ON res_groups.category_id = ir_module_category.id
                      WHERE res_groups.name='Team Manager' and ir_module_category.name='Sales' """)
                    d = self.env.cr.fetchall()
                    try:
                        for i in range(len(d)):
                              email_to = d[i][0]
                              subject = "Approval Needed For An Opportunity!"
                              body = _("Dear Sales Team Manager,<br/>")
                              body += _("<br/> The Below Opportunity Is Waiting For Your Approval ")
                              footer="With Regards,<br/>ADMIN<br/>"
                              mail_ids.append(mail_mail.create({
                                  'email_to': email_to,
                                  'subject': subject,
                                  'body_html':'''<span  style="font-size:14px"><br/>
                                      <br/>%s<br/>
                                      <ul>
                                            <li><strong>Opportunity Name:</strong>%s.</li>
                                            <li><strong>Partner Name:</strong>%s.</li>
                                            <li><strong>Expected Revenue:</strong>%s.</li>
                                      </ul>
                                      <br/>%s</span>''' %(body,body_html,partner,cost,footer),
                               }))
                              for i in range(len(mail_ids)):
                                mail_ids[i].send(self)
                    except Exception as z :
                       print("Exception", z ,'****************************')
                return None

         @api.multi
         def write(self, vals):
             flag = self.env['res.users'].has_group('base.group_team_managers')
             if flag==True:

                 self.env.cr.execute("""UPDATE crm_lead set visible_drop='TRUE' where id=%d"""%(self.ids[0]))
             else:
                 self.env.cr.execute("""UPDATE crm_lead set visible_drop='FALSE' where id=%d"""%(self.ids[0]))

             warning = {}
             self.env.cr.execute("""SELECT DISTINCT
                      res_users.login
                      FROM res_groups_users_rel
                      JOIN res_groups
                      ON res_groups.id = res_groups_users_rel.gid
                      JOIN public.res_users
                      ON res_groups_users_rel.uid = res_users.id
                      JOIN ir_module_category
                      ON res_groups.category_id = ir_module_category.id
                      WHERE res_groups.name='Team Manager' and ir_module_category.name='Sales'""")
             d= self.env.cr.fetchall()
             if vals.get('stage_id'):
                 self.env.cr.execute("""UPDATE crm_lead SET state='FALSE' WHERE stage_ids1 < 4 and id=%d"""%(self.ids[0]))
                 self.env.cr.execute("""UPDATE crm_lead SET ded='FALSE' WHERE stage_ids1 < 3 and id=%d"""%(self.ids[0]))
                 stage = self.env['crm.lead'].browse(vals['stage_id'])
                 flag = self.env['res.users'].has_group('base.group_team_managers')
                 u = self.env['crm.lead'].browse(self.ids)
                 if self.stage_ids1.id == 1 :
                     if  ((self.phone==False) and (self.email_from==False) and (self.child_ids.ids==[])):

                         raise UserError(_('Customer Phone Number,Email Id and Contacts Required To Move Next Stage!!!'))
                     elif self.phone==False:
                          raise UserError(_('Customer Phone Number Required To Move Next Stage!!!'))
                     elif self.email_from==False:
                         raise UserError(_('Customer Email Id Required To Move Next Stage!!!'))
                     elif ((self.child_ids.ids==[]) and (self.contact.ids==[])):
                         raise UserError(_('Customer Contact Required To Move Next Stage!!!'))
                 elif self.stage_ids1.id ==2:
                     self.write({'ded':True})
                     #~ self.env.cr.execute("""UPDATE crm_lead  SET ded='True' WHERE stage_ids1 = 3""")
                 elif self.stage_ids1.id ==3:
                     self.write({'state':True})
                     #~ self.env.cr.execute("""UPDATE crm_lead  SET state='True' WHERE stage_ids1 = 4""")
                     if  self.opportunity_order_line.ids==[]  and self.manager_decision==False:

                         raise UserError(_('Products And Manager Approval Required To Move Next Stage!!!'))
                     elif  self.opportunity_order_line.ids==[]:
                         raise UserError(_('Products Required To Move Next Stage!!!'))
                     elif self.manager_decision==False:

                         raise UserError(_('Sales Team Manager Approval Required To Move Next Stage!!!'))
                     elif  self.manager_decision != False:
                        if self.manager_decision=='yes'  and flag==False:
                            self.write({'sel':True})
                            #~ self.env.cr.execute("""UPDATE crm_lead  SET sel='True' WHERE manager_decision = 'yes' """)
                 #~ elif self.stage_ids1.id==5:
                     #~ self.write({'active': True})
             res = super(crm_lead, self).write(vals)
             return res

         def _stage_finds(self, team_id=False, domain=None, order='sequence'):

           """ Determine the stage of the current lead with its teams, the given domain and the given team_id
               :param team_id
               :param domain : base search domain for stage
               :returns crm.stage recordset
           """
           # collect all team_ids by adding given one, and the ones related to the current leads
           team_ids = set()
           if team_id:
               team_ids.add(team_id)
           for lead in self:
               if lead.team_id:
                   team_ids.add(lead.team_id.id)
           # generate the domain
           if team_ids:
               search_domain = ['|', ('team_id', '=', False), ('team_id', 'in', list(team_ids))]
           else:
               search_domain = [('team_id', '=', False)]
           # AND with the domain in parameter
           if domain:
               search_domain += list(domain)
           # perform search, return the first found
           return self.env['crm.stage'].search(search_domain, order=order,limit=5)

         @api.multi
         def action_set_won(self):
             """ Won semantic: probability = 100 (active untouched) """
             for lead in self:
                 self.env.cr.execute("""update crm_lead  set stages = 'won' """)
                 #~ self.env.cr.execute("""update crm_lead set stages = 'won' where id= '%s' """%(self.id))
                 stage_id = lead._stage_find(domain=[('probability', '=', 100.0), ('on_change', '=', True)])
                 lead.write({'stage_id': stage_id.id, 'probability': 100})
             return True

         @api.multi
         def action_set_losts(self):
             """ Won semantic: probability = 100 (active untouched) """
             for lead in self:
                 self.env.cr.execute("""update crm_lead  set stages = 'lost' """)
                 self.write({'active': False})
                #~ #  stage_id = lead._stage_finds(domain=[('probability', '>', 100.0), ('on_change', '=', True)])
                #~ #  lead.write({'stage_id': stage_id.id, 'probability': 100})
             return True
#~
         @api.multi
         def action_set_hold(self):
             """ Won semantic: probability = 100 (active untouched) """
             for lead in self:
                 self.env.cr.execute("""update crm_lead  set stages = 'hold' """)
                 self.write({'active': False})
                #~ #  stage_id = lead._stage_finds(domain=[('probability', '=', 100.0), ('on_change', '=', True)])
                #~ #  lead.write({'stage_id': stage_id.id, 'probability': 100})
             return True

         @api.multi
         def action_send_mail(self):
            send_mail = self.env['mail.mail']
            mail_ids=[]
            email_to = self.email_from
            product_details = ''' <table width = 100% style ="border-collapse: collapse; border:1px solid black"> <tr>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> S.No. </th>            
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Product </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Product Category </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Description </th>
            <th style ="border-collapse: collapse; border-bottom:1px solid black;border-bottom:1px solid black;text-align:left"> Quantity </th> </tr>
            '''
            var = 0
            for rec in self.opportunity_order_line:
                var = var+1
                product_details += ''' <tr>
                <td style = "border-collapse: collapse; border-right:1px solid black;;border-bottom:1px solid black;padding: 5px;"> %s </td>                
                <td style = "border-collapse: collapse; border-right:1px solid black;;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "padding: 5px;border-bottom:1px solid black;"> %s </td> </tr>
                    ''' %(var,rec.product_id.name, rec.product_category_id.name,rec.name,rec.quantity)
            product_details+= "</table>"

            subject = "Enquiry - Reg!"
            body = _("Dear %s," %(self.partner_id.name))
            body += _("<br/> <br/>Thanks for your enquiry about the following products: %s <br/> Will update further details soon." %(product_details))
            footer="With Regards,<br/>%s." %(self.company_id.name)
            mail_ids.append(send_mail.create({
                        'email_to': email_to,
                        'subject': subject,
                        'body_html':'''<span  style="font-size:14px"><br/>
                            <br/>%s<br/>
                            <br/>%s</span>''' %(body,footer),
                    }))
            for i in range(len(mail_ids)):
                mail_ids[i].send(self)

         def _onchange_partner_id_values(self, partner_id):
                """ returns the new values when partner_id has changed """
                values = {}
                s=[]
                partner_obj = self.env['crm.lead.contact']
                c_id=partner_obj.browse( )
                self.env.cr.execute('''select name,title,function,email,phone,mobile,comment from res_partner where parent_id=%d'''%(partner_id))
                res=self.env.cr.fetchall()
                self.env.cr.execute('''select id from res_partner where parent_id=%d'''%(partner_id))
                re=self.env.cr.fetchall()
                vals={}
                n=[]

                for i in range(len(re)):
                        s.append(re[i][0])
                for i in range(len(res)):
                        n.append({
                            'crm_id':c_id.id,
                            'name':res[i][0],
                            'title':res[i][1],
                            'function':res[i][2],
                            'email':res[i][3],
                            'phone':res[i][4],
                            'mobile':res[i][5],
                            'comment':  res[i][6]
                            })
                if partner_id:
                    partner = self.env['res.partner'].browse(partner_id)

                    partner_name = partner.parent_id.name
                    if not partner_name and partner.is_company:
                        partner_name = partner.name

                    return {
                        'partner_name': partner_name,
                        'contact_name': partner.name if not partner.is_company else False,
                        'title': partner.title.id,
                        'street': partner.street,
                        'street2': partner.street2,
                        'city': partner.city,
                        'state_id': partner.state_id.id,
                        'country_id': partner.country_id.id,
                        'email_from': partner.email,
                        'phone': partner.phone,
                        'mobile': partner.mobile,
                        'fax': partner.fax,
                        'zip': partner.zip,
                        'function': partner.function,
                        'child_ids':False,

                    }
                return {}

         @api.onchange('partner_id')
         def _onchange_partner_id(self):
            values = self._onchange_partner_id_values(self.partner_id.id if self.partner_id else False)
            self.update(values)

class CrmLeadLost(models.TransientModel):
    _inherit='crm.lead.lost'

    @api.multi
    def action_lost_reason_apply(self):
        self.env.cr.execute("""update crm_lead  set stages = 'drop' """)
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.write({'lost_reason': self.lost_reason_id.id})
        return leads.action_set_lost()
