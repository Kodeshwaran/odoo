from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from datetime import time

class saleorder(models.Model):
    _inherit='sale.order'
    
    contact_person = fields.Many2one('res.partner')
    ctp_designation = fields.Char(related="contact_person.function",readonly=True)
    quotation_reference = fields.Char("Quotation reference",readonly=True)
    validity = fields.Integer("Validity(Days)")
    shipment_mode = fields.Many2one('shipment.mode', string = 'Shipment Mode')
    omega_trn_no = fields.Char("Omega TRN No.", related='company_id.tin_number',store=True,readonly=True)
    customer_trn_no = fields.Char("Customer TRN No.", related='partner_id.trn_number',store=True)
    delivery_term = fields.Char('Delivery Term')
    po_number = fields.Char('PO Number')
    po_date = fields.Date('PO Date')
    
    @api.multi
    def action_confirm(self):
        
        #~ ret_val=self.env['ir.attachment'].search(['|',('res_id','=',self.id),('res_name','=',self.name)])
        #~ if ret_val:
        self.quotation_reference = self.name
        self.write({'quotation_reference':self.name})
        self.confirm_sale_sequence()
        return super(saleorder, self).action_confirm()
        #~ else:
            #~ raise UserError(_('Please add the files in attachment.')) 
            
    @api.multi
    def action_quote_won(self):
        #~ ret_val=self.env['ir.attachment'].search(['|',('res_id','=',self.id),('res_name','=',self.name)])
        #~ if ret_val:
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id',[])
        if data['state'] == 'sent':  
            # self.env.cr.execute("""update crm_lead  set active = 'False' where id= '%s' """%(self.enquiry_id.id))
            self.write({'state': 'approved'})
        #~ else:
            #~ raise UserError(_('Please add the files in attachment.'))
    

    @api.multi
    def action_quote_drop(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id',[])
        if data['state'] == 'sent':
            # self.env.cr.execute("""update crm_lead  set active = 'False' where id= '%s' """%(self.enquiry_id.id))
            self.write({'state': 'drop'})
            
    @api.multi
    def action_quote_lost(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id',[])
        if data['state'] == 'sent':
            # self.env.cr.execute("""update crm_lead  set active = 'False' where id= '%s' """%(self.enquiry_id.id))
            self.write({'state': 'lost'})

    @api.multi
    def action_quote_hold(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id',[])
        if data['state'] == 'sent':
            # self.env.cr.execute("""update crm_lead  set active = 'False' where id= '%s' """%(self.enquiry_id.id))
            self.write({'state': 'hold'})
        
            

            
class BusinessVerticalCat(models.Model):
    _name="business.vertical.cat"

    name = fields.Char("Name")
    business_vertical_cate = fields.Many2one('business.vertical','Business Vertical')
    
class BusinessVertical(models.Model):
    _name="business.vertical"
       
    name=fields.Char()        
    
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    business_vertical = fields.Many2one('business.vertical.cat','Business Vertical')
    
    sale_customer = fields.Boolean('Sale Customer')
    
    tin_number      = fields.Char('TIN Number' , size=14)
    cst_number      = fields.Char('CST Number' , size=20)
    pan_number      = fields.Char('PAN Number' , size=12)
    cin_number      = fields.Char('CIN Number' , size=25)
    


    
class crm_lead(models.Model):
    _inherit ='crm.lead'
    
    phone = fields.Char('Phone')
    email_from = fields.Char('Email', size=128, help="Email address of the contact", select=1)
    is_opportunity=fields.Boolean('is_opportunity', default=False) 
  

class purchase_requisition(models.Model):
    _inherit='purchase.requisition'
    
    oppor_id = fields.Many2one('crm.lead','Enquiry Reference',required=False)


  
class purchase(models.Model):
    _inherit='purchase.order'
    
    email_bool = fields.Boolean('Email with Customer name and address')
    
    customer_id = fields.Many2one('res.partner',string='Customer Name')
    
    
    
    
    #~ @api.onchange('requisition_id')
    #~ def _onchange_requisition_id(self):
        #~ self.customer_id = self.requisition_id.customer_id.id
        
    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return
        
        requisition = self.requisition_id
        
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id
        currency = partner.property_purchase_currency_id or requisition.company_id.currency_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.company_id = requisition.company_id.id
        self.currency_id = currency.id
        self.origin = requisition.name
        self.partner_ref = requisition.name # to control vendor bill based on agreement reference
        self.notes = requisition.description
        self.date_order = requisition.date_end or fields.Datetime.now()
        self.picking_type_id = requisition.picking_type_id.id
        self.customer_id = requisition.customer_id.id

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'partner_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            if fpos:
                taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id))
            else:
                taxes_ids = line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Compute price_unit in appropriate currency
            if requisition.company_id.currency_id != currency:
                price_unit = requisition.company_id.currency_id.compute(price_unit, currency)

            # Create PO line
            order_lines.append((0, 0, {
                'name': name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_po_id.id,
                'product_qty': product_qty,
                'price_unit': price_unit,
                'taxes_id': [(6, 0, taxes_ids)],
                'date_planned': requisition.schedule_date or fields.Date.today(),
                'procurement_ids': [(6, 0, [requisition.procurement_id.id])] if requisition.procurement_id else False,
                'account_analytic_id': line.account_analytic_id.id,
            }))
        self.order_line = order_lines
        
        
#~ Oppourtunity smart button 

class lead_opportunity(models.Model):
    _inherit='crm.lead'
    
    
    @api.multi
    def redirect_opportunity_view(self):
        self.ensure_one()
        # Get opportunity views
        form_view = self.env.ref('crm.crm_case_form_view_oppor')
        tree_view = self.env.ref('crm.crm_case_tree_view_oppor')
        return {
            'name': _('Opportunity'),
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'crm.lead',
            'domain': [('type', '=', 'opportunity')],
            'res_id': self.id,
            'view_id': False,
            'views': [
                (form_view.id, 'form'),
                (tree_view.id, 'tree'),
                (False, 'kanban'),
                (False, 'calendar'),
                (False, 'graph')
            ],
            'type': 'ir.actions.act_window',
            'context': {'default_type': 'opportunity'}
        }
        
class shipment_mode(models.Model):
    _name = 'shipment.mode'
    _rec_name = 'name'
    name = fields.Char("Name")
    code = fields.Char("Code")
    active = fields.Boolean("Active", default = True)
    
    
class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    iban_number = fields.Char("IBAN No.")    
