import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, tools, _
import math
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta as rdelta
from odoo.exceptions import UserError,ValidationError
from openerp.tools.float_utils import float_is_zero, float_compare,float_round
import xlsxwriter
from io import StringIO
import base64
import json
import os

        
class QuotationReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.quotation_order_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select sol.name as name, sol.item_no, sol.product_uom_qty as product_uom_qty, 
                                    sol.price_unit as price_unit, sol.price_subtotal as price_subtotal from sale_order as so
                                    join sale_order_line as sol on(so.id=sol.order_id) where so.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['sale.order'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.quotation_order_report', docargs)   
                            
class OrderConfirmationReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.order_confirmation_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select sol.name as name, sol.item_no, sol.product_uom_qty as product_uom_qty, 
                                    sol.price_unit as price_unit, sol.price_subtotal as price_subtotal from sale_order as so
                                    join sale_order_line as sol on(so.id=sol.order_id) where so.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['sale.order'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.order_confirmation_report', docargs)  
                             
class PurchaseOrderReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.purchase_order_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select pol.name as name, pol.item_no, pol.product_uom as product_uom_qty, 
                                    pol.price_unit as price_unit, pol.price_subtotal as price_subtotal from purchase_order as po
                                    join purchase_order_line as pol on(po.id=pol.order_id) where po.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['purchase.order'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'purchase.order',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.purchase_order_report', docargs) 
           
class PurchaseRFQReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.purchase_rfq_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select pol.name as name, pol.item_no, pol.product_uom as product_uom_qty, 
                                    pol.price_unit as price_unit, pol.price_subtotal as price_subtotal from purchase_order as po
                                    join purchase_order_line as pol on(po.id=pol.order_id) where po.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['purchase.order'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'purchase.order',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.purchase_rfq_report', docargs)    
                           
class AccountInvoiceReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.account_invoice_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select ail.name as name, ail.item_no, ail.quantity as product_uom_qty, 
                                    ail.price_unit as price_unit, ail.price_subtotal as price_subtotal from account_invoice as ai
                                    join account_invoice_line as ail on(ai.id=ail.invoice_id) where ai.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['account.invoice'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.account_invoice_report', docargs)  
        
class AccountRCMInvoiceReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.account_rcm_invoice_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select ail.name as name, ail.item_no, ail.quantity as product_uom_qty, 
                                    ail.price_unit as price_unit, ail.price_subtotal as price_subtotal from account_invoice as ai
                                    join account_invoice_line as ail on(ai.id=ail.invoice_id) where ai.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['account.invoice'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.account_rcm_invoice_report', docargs)  
        
class AccountProformaInvoiceReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.account_proforma_invoice_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select ail.name as name, ail.item_no, ail.quantity as product_uom_qty, 
                                    ail.price_unit as price_unit, ail.price_subtotal as price_subtotal from account_invoice as ai
                                    join account_invoice_line as ail on(ai.id=ail.invoice_id) where ai.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['account.invoice'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.account_proforma_invoice_report', docargs)  
                             
class ShipmentOrderReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.shipment_order_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select ail.name as name, ail.item_no, ail.quantity as product_uom_qty, 
                                    ail.price_unit as price_unit, ail.price_subtotal as price_subtotal from account_invoice as ai
                                    join account_invoice_line as ail on(ai.id=ail.invoice_id) where ai.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['stock.picking'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.shipment_order_report', docargs)  
                             
class ShipmentOrderPackReport(models.AbstractModel):
   
    _name = 'report.fnet_omega_reportz.shipment_order_pack_report'
    
    def get_order_line(self,data):
        if data:
            line_list = []
            line_val = []
            self.env.cr.execute(""" select ail.name as name, ail.item_no, ail.quantity as product_uom_qty, 
                                    ail.price_unit as price_unit, ail.price_subtotal as price_subtotal from account_invoice as ai
                                    join account_invoice_line as ail on(ai.id=ail.invoice_id) where ai.id='%s' """ %(data.id))
                                    
            line_list = self.env.cr.dictfetchall()
            for i in line_list:
                line_val.append({
                    'name': i['name'],
                    'item_no': i['item_no'],
                    'product_uom_qty': i['product_uom_qty'],
                    'price_unit': i['price_unit'],
                    'price_subtotal': i['price_subtotal'],
                })  
            return line_val    
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj=self.env['stock.picking'].browse(docids)
        emp=report_obj.name
        docargs = {'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs':report_obj,
            'get_order_line':self.get_order_line,
            }
        return self.env['report'].render('fnet_omega_reportz.shipment_order_pack_report', docargs)                       
