from odoo import models,fields,_
from odoo import api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError,except_orm
#~ class purchase_requisition(models.Model):
    #~ _inherit='purchase.requisition'
#~ 
    #~ def select_all(self):
        #~ pur_req = self.env['purchase.requisition'].browse(self.ids)
        #~ for line in pur_req.bid_received_line:
            #~ self.env.cr.execute(" update bid_received_line  set valid_qoute = 't' ")


class opportunity_orderline(models.Model):
    _inherit = 'opportunity.order.line'

    name = fields.Text(string='Description')
    product_category_id=fields.Many2one('product.category','Product Category')

    @api.multi
    def write(self, vals):
#~ 
        res = super(opportunity_orderline, self).write(vals)
#~ 
        return res
#~ 
#~ 
    @api.multi
    def create(self, vals):
#~ 
        res = super(opportunity_orderline, self).create(vals)
#~ 
        return res

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.ids !=[]:
            self.env.cr.execute("""select product_tmpl_id from product_product as pp
                                    left join product_template as pt on pt.id = pp.product_tmpl_id
                                    where pp.id = %d"""%(self.product_id.ids[0]))
            tmpl = self.env.cr.fetchall()
            self.env.cr.execute("""select name,description_sale from product_product as pp
                        left join product_template as pt on pt.id = pp.product_tmpl_id
                        where pt.id = %d"""  %(tmpl[0][0]))
            d = self.env.cr.fetchall()
            if d[0][1] != None:
                self.name = d[0][0] + '\n'+ d[0][1]
            else:
                pass


#~ class bid_received_Line(models.Model):
    #~ _inherit = 'bid.received.line'
#~ 
    #~ name=fields.Text('Description')
    #~ margin_percentage = fields.Float('Margin Percentage')
    #~ revised_margin = fields.Float('Revised Margin Percentage')
    #~ revised_quoted=fields.Boolean('Sale Quote',compute='tender_quote')
#~ 
    #~ @api.multi
    #~ @api.depends('tender_id.revised_quote')
    #~ def tender_quote(self):
        #~ for move in self:
            #~ move.revised_quoted = move.tender_id.revised_quote
#~ 
#~ class purchase_requisition(models.Model):
    #~ _inherit='purchase.requisition'
#~ 
    #~ revised_quote = fields.Boolean('Revised Quote',compute='lin_count')
#~ 
    #~ def lin_count(self):
        #~ if self.quote_count >= 1:
            #~ self.revised_quote = True
#~ 
    #~ @api.multi
    #~ def set_margin_price_compute(self):
        #~ """
        #~ This function is calculate the margin price for product
        #~ margin=(unit price/100)*percent
        #~ transfort+margin
        #~ then the above value is added to unit price
        #~ """
        #~ res={}
        #~ product=[]
        #~ cnt=[]
        #~ self.env.cr.execute("""select id from purchase_order where requisition_id = %d """%(self.id))
        #~ m = self.env.cr.fetchall()
        #~ for ids in m:
            #~ requisition_id = self.env['purchase.order'].browse(ids)
            #~ requisition_ids = self.env['purchase.order'].browse(ids)
            #~ history_obj=self.env['costing.history.line']
            #~ for line in self.bid_received_line:
                #~ if line.revised_margin:
                   #~ if line.purchase_unit_price != 0:
                      #~ add_trans=line.purchase_unit_price
                      #~ margin=line.purchase_unit_price*(line.revised_margin/100)
                      #~ margin_price=margin+add_trans
                      #~ total_price=margin_price*line.quantity
                      #~ res={
                         #~ 'unit_price':margin_price,
                         #~ 'sub_total':total_price,
                      #~ }
                      #~ line.write(res)
            #~ if requisition_id.history_line:
               #~ for i in requisition_id.history_line:
                   #~ string_val=i.offer
                   #~ val=string_val.split(" ")
                   #~ cnt.append(val[1])
               #~ x = [int(n) for n in cnt]
               #~ next_off=max(x)
               #~ offer=next_off+1
               #~ vals={
                  #~ 'offer':'OFFER ' + str(int(offer)),
                  #~ 'order_id':ids[0],
                #~ }
            #~ if requisition_id.state != 'cancel':
                #~ off_id=requisition_id.history_line.create(vals)
                #~ for line in self.bid_received_line:
                    #~ history_value={
                      #~ 'offer_id':off_id.id,
                      #~ 'product_id':line.product_id.id,
                      #~ 'quantity':line.quantity,
                      #~ 'purchase_unit_price':line.purchase_unit_price,
                      #~ 'margin_percentagess':line.revised_margin,
                      #~ 'unit_measure':line.unit_measure.id,
                      #~ 'margin_unit_price':line.unit_price,
                      #~ 'customer_price':line.sub_total,
                    #~ }
                    #~ self.env['costing.history.line'].create(history_value)


class crm_lead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def make_tender(self):
        """
        This is used to create the tender against the enquiry
        """
        tenders = self.env['purchase.requisition']
        tender_count = tenders.search([('oppor_id', '=', self.id)])
        if tender_count:
            raise UserError(_('You can create only one Tender !'))
        user = self.env['res.users'].search([('id', '=', self._uid)])
        if not self.partner_id:
            raise UserError(_('Please Select raleted customer !'))
        values = {
            'user_id': self.user_id.id,
            'oppor_id': self.id,
            'company_id': user.company_id.id,
            'origin': self.oppor_order,
            'customer_id': self.partner_id.id,
        }

        quotation = tenders.create(values)

        if quotation:
            value_line = self.env['opportunity.order.line'].search([('lead_id', '=', self.id)])
            for len_val in value_line:
                ret_value = {
                    'requisition_id': quotation.id,
                    'product_id': len_val.product_id.id or False,
                    'product_category_id':len_val.product_category_id.id or False,
                    'description':len_val.name or False,
                    'product_qty': len_val.quantity,
                    'product_uom_id': len_val.unit_measure.id,
                    'item_no':len_val.item_no,

                }

                line = tenders.env['purchase.requisition.line'].create(ret_value)
