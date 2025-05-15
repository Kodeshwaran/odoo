from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class account_invoice_inher(models.Model):
    _inherit = "account.invoice"
    

    @api.model
    def create(self, values):
        so_val = self.env['sale.order'].search([('name','=',values['origin'])])
        values['lead_name'] = so_val.enquiry_id.name
        val = super(account_invoice_inher, self).create(values)
        return val



    lead_name = fields.Char(string='Lead')
    
    ### Fields for reports   
    bank_name = fields.Many2one("res.partner.bank", string="Bank Name")
    po_date = fields.Date(string="PO date")
    po_number = fields.Char('PO Number')
    omega_trn_no = fields.Char("Omega TRN No.", related='company_id.tin_number',store=True,readonly=True)             
    customer_trn_no = fields.Char("Customer TRN No.",related='partner_id.trn_number')             
    aed_amount = fields.Float("AED Amount") 
    exchange_rate= fields.Float("Exchange Rate")          

    @api.onchange('currency_id')
    def onchange_state(self):
        result={}
        banks = self.env['res.partner.bank'].search([])
        for bank in banks:
            if bank.currency_id == self.currency_id:
                self.bank_name = bank
                self.update({'exchange_rate':self.currency_id.rate})             
                # ~ self.exchange_rate = self.currency_id.rate            
        # ~ if self.currency_id:
            # ~ result['value'] = {
                 # ~ 'exchange_rate': self.currency_id.rate,
                        # ~ }
            # ~ return result
        # ~ return {}   

    #~ shipment_type = fields.Char("Shipment Type")  
    #~ shipment_date = fields.Date("Shipment Date")  
