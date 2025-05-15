from odoo import api, fields, models,_
import datetime
from odoo.exceptions import UserError


class CoveringLetter(models.AbstractModel):
    _name='report.fnet_omega_reportz.report_covering_letter'
    
    
    #~ @api.multi 
    #~ def serial_no(self,line_id,obj):
        #~ 
        #~ if obj :
            #~ li = []         
            #~ for rec in obj.pack_operation_product_ids:
                #~ if line_id.product_id.id == rec.product_id.id:
                    #~ for lot in rec.pack_lot_ids:
                        #~ li.append(lot.lot_id.name)
            #~ return li                  
    #~ @api.multi                        
    #~ def dated(self,obj):
        #~ if obj:
            #~ sale_order=self.env['sale.order'].search([('name','=',obj.origin)])        
            #~ for rek in sale_order:
                #~ date_time = datetime.datetime.strptime((rek.date_order), '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
                #~ return date_time
    #~ @api.multi         
    #~ def Terms_of_Payment(self,obj):
        #~ if obj:
            #~ sale_order=self.env['sale.order'].search([('name','=',obj.origin)])
            #~ for res in sale_order:
                #~ return res.payment_term_id.name
    #~ @api.multi
    #~ def order_no(self,obj):
        #~ if obj:
            #~ sale_order=self.env['sale.order'].search([('name','=',obj.origin)])        
            #~ for rec in sale_order:
                #~ 
                #~ return rec.incoterm.name
    #~ @api.multi           
    #~ def client_order_refs(self,obj):
        #~ if obj:
            #~ 
            #~ sale_order=self.env['sale.order'].search([('name','=',obj.origin)])
            #~ if sale_order.client_order_ref:        
               #~ return sale_order.client_order_ref
                #~ 
                #~ 
    #~ @api.multi
    #~ def order_date(self,obj):
        #~ if obj:
                       #~ 
           #~ sale_order=self.env['sale.order'].search([('name','=',obj.origin)])        
           #~ for rek in sale_order:
                #~ if rek.order_date:
                   #~ date_time =datetime.datetime.strptime((rek.order_date), '%Y-%m-%d').strftime('%d-%m-%Y')
                   #~ return date_time
                #~ return
    #~ @api.multi               
    #~ def date(self,obj):    
        #~ if obj:         
            #~ date_time = datetime.datetime.strptime((obj.date_done), '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
            #~ return date_time 
            
   
         
    @api.model
    def render_html(self, docids, data=None):   
        report_obj=self.env['sale.order'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': report_obj ,
            'data':data,
            #~ 'serial_no':self.serial_no,
            #~ 'dated':self.dated,
            #~ 'Terms_of_Payment':self.Terms_of_Payment,
            #~ 'order_no':self.order_no,
            #~ 'client_order_refs':self.client_order_refs,
            #~ 'order_date':self.order_date,
            #~ 'date':self.date,
          }
        
        return self.env['report'].render('fnet_omega_reportz.report_covering_letter', docargs)
        
    
    
    
