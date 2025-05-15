# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import namedtuple
import json
import time

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.addons.procurement.models import procurement
from odoo.exceptions import UserError

import logging
from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource
import datetime
import time
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import calendar
from calendar import monthrange

class stock_picking_inherit(models.Model):
    _inherit = 'stock.picking'
    
    @api.multi
    def product_delivery_cron(self):
        send_mail = self.env['mail.mail']
        mail_ids=[]
        mail_template = self.env['mail.template']       
        now=datetime.datetime.strptime(time.strftime("%Y-%m-%d"), '%Y-%m-%d').date()
        no_of_days = 5
        dt = str(now + timedelta(days = no_of_days))
        dte = str(now + timedelta(days = no_of_days))
        dt = dt + ' 00:00:00'
        dts = dte + ' 23:59:59'
        print 'dddddddddddd', dt,now        
        type_id = self.env['stock.picking.type'].search([('code','=','outgoing')],limit = 1)
        pro_id = self.env['stock.picking'].search([('min_date','>=', dt),('min_date','<=', dts), ('state', 'not in', ('done',)),('picking_type_id','=',type_id.id)])
        for rec in pro_id:
            var = 0
            var = var+1
            self.env.cr.execute('''SELECT DISTINCT sol.name,sol.product_uom_qty, sol.qty_delivered,(sol.product_uom_qty-sol.qty_delivered) as rem_qty, sp.min_date
                                        FROM stock_picking sp
                                        LEFT JOIN stock_move sm
                                        ON sp.id = sm.picking_id
                                        LEFT JOIN procurement_order po
                                        ON sm.procurement_id = po.id
                                        LEFT JOIN sale_order_line sol
                                        ON po.sale_line_id = sol.id
                                        LEFT JOIN sale_order so
                                        ON sol.order_id = so.id where sp.id = %d''' %(rec.id))
                                        
            obj = self.env.cr.dictfetchall()
            for res in obj:
                product_details = ''' <table width = 100% style ="border-collapse: collapse; border:1px solid black"> <tr>
                <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> S.No. </th>            
                <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Product </th>
                <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Ordered Quantity </th>
                <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Delivered Quantity </th>
                <th style ="border-collapse: collapse; border-bottom:1px solid black;border-bottom:1px solid black;text-align:left"> Remaining Quantity </th> </tr>
                '''                                    
                product_details += ''' <tr>
                        <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>                
                        <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                        <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                        <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                        <td style = "padding: 5px;border-bottom:1px solid black;"> %s </td> </tr>
                        ''' %(var, res['name'], res['product_uom_qty'], res['qty_delivered'], res['rem_qty'])
                product_details+= "</table>"
                email_to = 'sivakumar.k.g@247c.in'
                subject = "Remainder regarding Delivery of Products!"
                body = _("Dear Manager,")
                body += _("<br/> <br/>The following products are reaching their delivery date in 5day's. <br/> Delivery Date date: %s  %s: <br/>" %(res['min_date'],product_details))
                footer="With Regards,<br/>ADMIN"
                mail_ids.append(send_mail.create({
                            'email_to': email_to,
                            'subject': subject,
                            'body_html':'''<span  style="font-size:14px"><br/>
                                <br/>%s<br/>
                                <br/>%s</span>''' %(body,footer),
                        }))
            for i in range(len(mail_ids)):
                mail_ids[i].send(self)  
