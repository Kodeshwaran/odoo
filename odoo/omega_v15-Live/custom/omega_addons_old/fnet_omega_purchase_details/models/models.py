# -*- coding: utf-8 -*-

from odoo import api, fields, models


class purchase_detail(models.Model):
    _inherit = 'purchase.order'
    qty = fields.Float('Total Qty')
    rec_qty = fields.Float('Received Qty')
    billed_qty = fields.Float('Billed Qty')
    
class purchase_details_inherit(models.Model):
    _inherit = 'purchase.order.line'
    
    @api.depends('product_qty', 'qty_received','qty_invoiced')
    def _get_details(self):
        for rec in self:
           # self.env.cr.execute("""select pol.product_qty, pol.qty_received,pol.order_id,po.name,pol.qty_invoiced from purchase_order_line as pol
           #                        join purchase_order as po on pol.order_id = po.id
           #                        where pol.id = %d"""%(self.ids[0]))
           # s = self.env.cr.fetchall()
           # print("\n---",s,"--s--\n")
           # self.env.cr.execute(""" select sum(product_qty),sum(qty_received),sum(qty_invoiced) from purchase_order_line
           #                         where order_id =%d"""%(s[0][2]))
           # z =self.env.cr.fetchall()
           d = sum(rec.order_id.mapped('order_line').mapped('product_qty'))
           e = sum(rec.order_id.mapped('order_line').mapped('qty_received'))
           f = sum(rec.order_id.mapped('order_line').mapped('qty_invoiced'))
           g = rec.order_id.name
           if f == None:
               self.env.cr.execute(""" update purchase_order
                                       set qty= %d,
                                       rec_qty = %d,
                                       billed_qty = 0.00
                                       where name = '%s'"""%(d,e,g))
           else:
               self.env.cr.execute(""" update purchase_order
                                       set qty= %d,
                                       rec_qty = %d,
                                       billed_qty = %d
                                       where name = '%s'"""%(d,e,f,g))

        
    pay_sub = fields.Float(compute='_get_details', store=True)
