from odoo import api, fields, models, _
from odoo.exceptions import UserError,except_orm
from odoo.tools.float_utils import float_is_zero, float_compare

class CustomerPartner(models.Model):
    _inherit = 'res.partner'

    type_name=fields.Char('Type')
    s_no=fields.Char('Serial No')
    # ~ trn_number=fields.Char('TRN Number')



class saleorder(models.Model):
    _inherit='sale.order'

    @api.depends('amount_total', 'currency_id')
    def _convert_to_company_amount(self):
        for rec in self:
            currency_id = rec.company_id.currency_id
            rec.base_currency_amount = currency_id.with_context(date=rec.date_order).compute(rec.amount_total, rec.currency_id)

    is_covering_letter = fields.Boolean('Is Covering Letter Needed')
    tender_id     = fields.Many2one('purchase.requisition','Tender Reference')
    enquiry_id    = fields.Many2one('crm.lead','Enquiry Reference')
    amendment_notes=fields.Text('Manager notes', track_visibility="always")
    tax_notes=fields.Text(string='Tax notes', default="Quoted prices are exclusive of VAT")
    covering_notes=fields.Text(string='Tax notes')
    quotation_notes=fields.Html('Notes')
    state         = fields.Selection([('draft', 'Draft'),('submit', 'Submit'),
                                      ('to approve','Waiting For Approve'),
                                      ('approved','Approved'),  
                                      ('sent', 'Quotation Sent'),
                                      ('won', 'Quotation Won'),
                                      ('drop', 'Quotation Drop'),
                                      ('lost', 'Quotation Lost'),
                                      ('hold', 'Quotation Hold'),
                                      ('amendmend','Amendmend'),
                                      ('sale', 'Sale Order'),
                                      ('done', 'Done'),
                                      ('cancel', 'Cancelled'),
                                      ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    base_currency_amount = fields.Monetary("Amount", compute='_convert_to_company_amount')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor", domain="[('supplier','=',True)]")
   
                    
    @api.multi
    def return_draft(self):
        self.write({'state':'draft'}) 
        return True
    
    @api.multi
    def return_submit(self):
        self.write({'state':'submit'}) 
        return True
      
        
                         
    @api.model
    def get_salesman_url(self):
        self.ensure_one()
        val=self.user_id.partner_id.with_context(signup_valid=True)._get_signup_url_for_action(
            action='/mail/view',
            model=self._name,
            res_id=self.id)[self.user_id.partner_id.id]
            
        return val              
    @api.multi
    def quote_reject(self):
        url_val=self.get_salesman_url()
        resl_id=self.env['res.partner'].search([('id','=',self.user_id.partner_id.id)])
        body = _("Dear " + self.user_id.name + "\n")
                                            
        body += _("\t This (%s) Sale Quotation has been Rejected by %s. \n "%(self.name,self.env.user.name))
        body += _("\n Regards, \n %s."%(self.env.user.name)) 
        values={
            'subject': "Sale Quote Rejected",
            'email_to' :resl_id.email,
            'body_html':'<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>'%(body,url_val),
            'body' :'<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>'%(body),
            'res_id': False
           }    
        
        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)
        
        if msg_id:
           res=msg_id.send(self) 
        val = self.env['ir.sequence'].next_by_code('salequote.amend')
        pre_name=self.name
        saleorder_name=val+' ('+pre_name+')'
        self.write({'name':saleorder_name})
        self.write({'state':'amendmend'})              
    
    
        
    @api.multi
    def approve_quote(self):
        values={}
        url_val=self.get_salesman_url()
        resl_id=self.env['res.partner'].search([('id','=',self.user_id.partner_id.id)])
        body = _("Dear " + self.user_id.name + "\n")
                                            
        body += _("\t This (%s) Sale Quotation has been Approved by %s. \n "%(self.name,self.env.user.name))
        
        body += _("\n Regards, \n %s."%(self.env.user.name)) 
        values={
            'subject': "Sale Quote Approved",
            'email_to' :resl_id.email,
            'body_html':'<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>'%(body,url_val),
            'body' :'<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>'%(body),
            'res_id': False
           }    
        
        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)
        
        if msg_id:
           res=msg_id.send(self) 
         
        self.write({'state':'approved'})
               
    @api.multi
    def action_quotation_send(self):
        if self.state=='draft':
           self.state = 'submit'
           ret=self.validate_profit_percentage()
        
           if ret ==1:
              return False  
        return super(saleorder, self).action_quotation_send()
        
    @api.multi
    def validate_profit_percentage(self):
        tot=0.0
        val=1
        #~ conf_obj=self.env['sale.config.settings'].search([('company_id','=',self.env.user.company_id.id)],order='id desc',limit=1)
        
        if self.user_has_groups('sales_team.group_sale_manager') is False:
           if self.tender_id:
              
              #~ bid_line=self.env['bid.received.line'].search([('tender_id','=',self.tender_id.id)])
              
              for line in self.order_line:
                 
                 tot +=line.purchase_total_price
                               
              profit=self.amount_untaxed-tot
              profit_per=(profit/tot)*100
              if self.team_id.limit_id:
                 if profit_per < self.team_id.limit_id.values:
                    self.write({'state':'to approve'}) 
                    
                    rt=self.approve_quote_by_team_leader()
                    
                    return val
              #~ elif conf_obj.limit_id:
                 #~ if profit_per < sconf_obj.limit_id.values:
                    #~ self.write({'state':'to approve'}) 
               
                    #~ return val      
       
        return False
        
    @api.model
    def get_url(self):
        self.ensure_one()
        val=self.team_id.user_id.partner_id.with_context(signup_valid=True)._get_signup_url_for_action(
            action='/mail/view',
            model=self._name,
            res_id=self.id)[self.team_id.user_id.partner_id.id]
        return val
    
             
    @api.model
    def approve_quote_by_team_leader(self):
        values = {}
        url_val = self.get_url()
        if self.team_id.user_id:
           resl_id = self.env['res.partner'].search([('id','=',self.team_id.user_id.partner_id.id)])
           try:
              body = _("Dear " + resl_id.name + "\n")
              body += _("\t This (%s) Sale Quotation is waiting for your Approval. \n "%(self.name))
              body += _("\n Regards, \n %s."%(self.env.user.name)) 
              values = {
                 'subject': "Sale Quote Wait for Approval",
                 'email_to': resl_id.email,
                 'body_html': '<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>'%(body,url_val),
                 'body': '<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>'%(body),
                 'res_id': False
                }
              mail_mail_obj = self.env['mail.mail']
              msg_id = mail_mail_obj.create(values)
              if msg_id:
                 res = msg_id.send(self)
                 return res
           except Exception as z:
              print(z)
        return False  
    
    # @api.multi
    def action_quote_won(self):
        self.write({'state': 'approved'})
        # ret_val=self.env['ir.attachment'].search(['|',('res_id','=',self.id),('res_name','=',self.name)])
        # print(ret_val, 'retvalllll')
        # if ret_val:
        #     data = self.read()[0]
        #     data['partner_id'] = self._context.get('active_id',[])
        #     if data['state'] == 'sent':
        #         self.env.cr.execute("""update crm_lead  set active = 'False'""")

        # else:
        #     raise UserError(_('Please add the files in attachment.'))

    # @api.multi
    def action_quote_drop(self):
        # data = self.read()[0]
        # data['partner_id'] = self._context.get('active_id',[])
        # if data['state'] == 'sent':
        #     self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'drop'})

    # @api.multi
    def action_quote_lost(self):
        # data = self.read()[0]
        # data['partner_id'] = self._context.get('active_id',[])
        # if data['state'] == 'sent':
        #     self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'lost'})

    # @api.multi
    def action_quote_hold(self):
        # data = self.read()[0]
        # data['partner_id'] = self._context.get('active_id',[])
        # if data['state'] == 'sent':
        #     self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'hold'})
    
    @api.multi
    def action_draft(self):
        
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent', 'hold', 'drop', 'lost'])
        orders.write({
            'state': 'draft',
            'procurement_group_id': False,
        })
        orders.mapped('order_line').mapped('procurement_ids').write({'sale_line_id': False})


    @api.multi
    def action_confirm_quote(self):
        if self.state=='draft':
           # self.state = "to approve"
           ret=self.validate_profit_percentage()
           if ret:
              return True  
        
        self.write({'state':'sent'})
    
    @api.multi
    def action_confirm(self):
        #~ ret_val=self.env['ir.attachment'].search(['|',('res_id','=',self.id),('res_name','=',self.name)])
        #~ if ret_val:
       self.confirm_sale_sequence()
       return super(saleorder, self).action_confirm()
        #~ else:
           #~ raise UserError(_('Please add the files in attachment.')) 
        
        
    @api.multi
    def confirm_sale_sequence(self):
        val = self.env['ir.sequence'].next_by_code('sale.confirm')
        self.write({'name':val})
        
    @api.multi
    def print_quotation(self):
       
        
        if self.state=='draft':
           ret=self.validate_profit_percentage()
           if ret:
              return True
           else:
              return super(saleorder, self).print_quotation()
        return super(saleorder, self).print_quotation()

    def action_final_approval(self):
        for rec in self:
            rec.state ='to approve'

class saleorder_approve(models.Model):
    _name='approve.limit'
    
    name=fields.Char('Name',size=15)
    active=fields.Boolean('Active',default=True)
    values=fields.Float('Value')


class saleorder_line(models.Model):
    _inherit='sale.order.line'

    purchase_unit_price=fields.Float('Purchase Unit Price',readonly=True)
    purchase_total_price=fields.Float('Purchase Total Price',readonly=True)
    item_no = fields.Char('Item No')
    note = fields.Html("Notes")

    @api.onchange('product_id')
    def onchange_product_id_1(self):
        if self.product_id:
            self.note = self.product_id.name

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'item_no':self.item_no,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.project_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).

        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                self.env['account.invoice.line'].create(vals)
                
class account_invoice_line(models.Model):
    _inherit='account.invoice.line'

    item_no = fields.Char('Item No')
