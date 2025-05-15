# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp

class purchase_order(models.Model):
    
    _inherit = 'purchase.order'
    
    expected_closing=fields.Date('Expected closing')
    delay=fields.Text('Delay Reason')
    check=fields.Boolean(' Send Email reminder') 
    state=fields.Selection([
        ('draft', 'Draft PO'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('bid received','Bid Received'),
        ('purchase', 'Purchase Order'),
        ('purchase_amend', 'purchase amendment'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    ### Fields for reports
    delivery_date = fields.Date("Delivery Date")
    order_reference = fields.Char("Reference")           
    omega_trn_no = fields.Char("Omega TRN No.", related='company_id.tin_number', store=True, readonly=True)             
     
    @api.multi
    def purchase_amendment(self):
        self.write({'state': 'purchase_amend'})
        return True
   
    @api.multi
    def action_view_picking(self):
        '''
        This function returns an action that display existing picking orders of given purchase order ids.
        When only one found, show the picking immediately.
        '''
        action = self.env.ref('stock.action_picking_tree')
        result = action.read()[0]

        #override the context to get rid of the default filtering on picking type
        result['context'] = {}
        pick_ids = sum([order.picking_ids.ids for order in self], [])
        #choose the view_mode accordingly
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result
        
    @api.multi
    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]

        #override the context to get rid of the default filtering
        result['context'] = {'type': 'in_invoice', 'default_purchase_id': self.id}

        if not self.invoice_ids:
            # Choose a default account journal in the same currency in case a new invoice is created
            journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.company_id.id),
                ('currency_id', '=', self.currency_id.id),
            ]
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
            if default_journal_id:
                result['context']['default_journal_id'] = default_journal_id.id
        else:
            # Use the same account journal than a previous invoice
            result['context']['default_journal_id'] = self.invoice_ids[0].journal_id.id

        #choose the view_mode accordingly
        if len(self.invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        elif len(self.invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.invoice_ids.id
        return result
        
             #~ warehouse = self.env("stock.warehouse").search([("company_id", "=", "1")])   
        
        
    
    @api.model   
    def send_purchase_order_reminder_mail(self):
        partner_obj = self.env['purchase.order'].browse(self.ids)
        mail_mail = self.env['mail.mail']
        mail_ids=[]
        template_obj = self.env['mail.template']
        dt = datetime.now()
        today_month_day = dt.strftime('%m')+ '/' + dt.strftime('%d') + '/' + dt.strftime('%Y')
        purs = partner_obj.search([('state','=','purchase')]) 
        purchase_line_ids = partner_obj.search([]) 
        for a in purchase_line_ids:
          if a.state == 'purchase':
              par_id = partner_obj.search(['&',('expected_closing','=',today_month_day),('state','=','purchase'),('check','=',True)])
              group_model_id = self.env['ir.model'].search([('model', 'like', 'purchase.order')])[0]
              body_html = ' '
              for val in partner_obj.browse(par_id.ids):
                  body_html += str(val.name) + '           ' +str(val.date_order)+"<br/>"
              s=[]
              self.env.cr.execute("""SELECT DISTINCT
                      res_users.login
                      FROM res_groups_users_rel
                      JOIN res_groups
                      ON res_groups.id = res_groups_users_rel.gid
                      JOIN public.res_users
                      ON res_groups_users_rel.uid = res_users.id
                      JOIN ir_module_category 
                      ON res_groups.category_id = ir_module_category.id
                      WHERE res_groups.name='Manager' and ir_module_category.name='Purchases'""")
              d = self.env.cr.fetchall()
              for val in partner_obj.browse(par_id.ids):
                  s.append(val.name)
              if par_id.ids:
                  try:
                      for i in range(len(d)):
                          email_to = d[i][0]
                          name = val.name                
                          subject = "Purchase order Reminder"
                          body = _("Dear Manager, \n")
                                            
                          body += _("\t Validity of the expected date has been over for the following purchase order. \n ") 
                                             
                          mail_ids.append(mail_mail.create({
                              'email_to': email_to,
                              'subject': subject,
                                
                              'body_html':'<pre><span class="inner-pre" style="font-size:15px">%s<br/>%s</span></pre>'%(body,body_html),
                                
                           }))
                      for i in range(len(mail_ids)):                                  
                          mail_ids[i].send(self)     
                  except Exception,z :
                      print "Exception", z ,'****************************'  
              return None
    
    @api.model        
    def send_purchase_order_reminder_mail_purchaseamend(self):
        partner_obj = self.env['purchase.order'].browse(self.ids)
        mail_mail = self.env['mail.mail']
        mail_ids=[]
        template_obj = self.env['mail.template']
        dt = datetime.now()
        today_month_day = dt.strftime('%m')+ '/' + dt.strftime('%d') + '/' + dt.strftime('%Y')
        purs = partner_obj.search([('state','=','purchase_amend')]) 
        purchase_line_ids = partner_obj.search([]) 
        for a in purchase_line_ids:
          if a.state == 'purchase_amend':
              par_id = partner_obj.search(['&',('expected_closing','=',today_month_day),('state','=','purchase_amend'),('check','=',True)])
              group_model_id = self.env['ir.model'].search([('model', 'like', 'purchase.order')])[0]
              a = partner_obj.browse(par_id.ids)
              body_html = ' '
              for val in partner_obj.browse(par_id.ids):
                body_html += str(val.name) + '           ' +str(val.expected_closing)+"<br/>"
              s=[]
              self.env.cr.execute("""SELECT DISTINCT
                      res_users.login
                      FROM res_groups_users_rel
                      JOIN res_groups
                      ON res_groups.id = res_groups_users_rel.gid
                      JOIN public.res_users
                      ON res_groups_users_rel.uid = res_users.id
                      JOIN ir_module_category 
                      ON res_groups.category_id = ir_module_category.id
                      WHERE res_groups.name='Manager' and ir_module_category.name='Purchases'""")
              d = self.env.cr.fetchall()
              for val in partner_obj.browse(par_id.ids):
                  s.append(val.name)
              if par_id.ids:
                  try:
                      for i in range(len(d)):
                          email_to = d[i][0]
                          name = val.name                
                          subject = "Purchase Amendment order Reminder"
                          body = _("Dear Manager, \n")
                                            
                          body += _("\t The expected date for the following purchase order has been extended. \n ") 
                                             
                          mail_ids.append(mail_mail.create({
                              'email_to': email_to,
                              'subject': subject,
                                
                              'body_html':'<pre><span class="inner-pre" style="font-size:15px">%s<br/>%s</span></pre>'%(body,body_html),
                                
                           }))
                      for i in range(len(mail_ids)):                                  
                                mail_ids[i].send(self)
                  except Exception,z :
                      print "Exception", z ,'****************************'  
              return None

           
