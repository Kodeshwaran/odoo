import time
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class CustomerPartner(models.Model):
    _inherit = 'res.partner'

    type_name=fields.Char('Type')
    s_no=fields.Char('Serial No')
    principal_value = fields.Boolean('Principal')
    type_acc        = fields.Selection([('new', 'New'), ('developing', 'Developing'), ('developed', 'Developed')], string='Account Type')
    line_ids        = fields.One2many('fnet.budget.info', 'partner_id', string='Principal Budget')
    lineitem_ids    = fields.One2many('fnet.budget.info.customer', 'partner_id', string='Customer Budget')
    budget_it_ids   = fields.One2many('fnet.it.budget.info.customer', 'partner_id', string='IT Annual Budget')
    is_company      = fields.Boolean(string='Is a Company',default= True,
                               help="Check if the contact is a company, otherwise it is a person")
    custom_street=fields.Char('Street')
    custom_street2= fields.Char('Street2')
    custom_zip= fields.Char('Zip', size=24)
    custom_city= fields.Char('City')
    custom_state_id= fields.Many2one("res.country.state", 'State', ondelete='restrict')
    custom_country_id= fields.Many2one('res.country', 'Country', ondelete='restrict')  
    trn_number = fields.Char('TRN Number')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            partner = self.env['res.partner'].search([('name', '=', vals.get('name')), ('id', '!=', self.id)])
            if partner:
                raise UserError(_("The partner already exist!"))
        return super(CustomerPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            partner = self.env['res.partner'].search([('name', '=', vals.get('name')), ('id', '!=', self.id)])
            if partner:
                raise UserError(_("The partner already exist!"))
        return super(CustomerPartner, self).write(vals)

class ITBudgetInfoCustomer(models.Model):
    _name = "fnet.it.budget.info.customer"
    
    partner_id      = fields.Many2one('res.partner',string='Partner')
    from_date       = fields.Date(string='From date',required=True,default=lambda *a: time.strftime('%Y-04-01'))
    to_date         = fields.Date(string='To date',required=True,default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+11, day=1, days=-1))[:10])
    value_budget    = fields.Float(string='Annual IT Budget')

    @api.model
    def create(self,vals):
        partner = super(ITBudgetInfoCustomer, self).create(vals)
        obj = self.env['fnet.it.budget.info.customer'].search([('partner_id','=',vals['partner_id'])])
        if len(obj) > 1:
            n = 0
            j = []
            k = []
            for i in obj:           
                j.append(i.from_date)
                k.append(i.to_date)

                if n>0:
                    if vals['from_date'] >= j[n-1]:
                        if vals['from_date'] <= k[n-1]:
                            raise ValidationError("Budget Year was already selected. Please check that")
                    else:
                        if vals['to_date'] >= j[n-1]:
                            raise ValidationError("Budget Year was already selected. Please check that")
                
                n = n+1

    @api.onchange('from_date','to_date')
    def check_date(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise ValidationError("To Date Should Be Greater Than From Date")

    
class BudgetInfoCustomer(models.Model):
    _name = "fnet.budget.info.customer"
    
    partner_id      = fields.Many2one('res.partner',string='Partner')
    principal_val   = fields.Many2one('res.partner',string="Principal")
    from_date       = fields.Date(string='From date',required=True,default=lambda *a: time.strftime('%Y-%m-01'))
    to_date         = fields.Date(string='To date',required=True,default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    value_budget    = fields.Float(string='Budget Value')
    value_actual    = fields.Float(compute='_amount_check_actual', string='Actual Value')

    @api.model
    def create(self,vals):
        partner = super(BudgetInfoCustomer, self).create(vals)
        obj = self.env['fnet.budget.info.customer'].search([('partner_id','=',vals['partner_id'])])

        if len(obj) > 1:
            n = 0
            j = []
            k = []
            for i in obj:           
                j.append(i.from_date)
                k.append(i.to_date)

                if n>0:
                    if vals['from_date'] >= j[n-1]:
                        if vals['from_date'] <= k[n-1]:
                            raise ValidationError("Date was already selected. Please check that")
                    else:
                        if vals['to_date'] >= j[n-1]:
                            raise ValidationError("Date was already selected. Please check that")
                
                n = n+1

    @api.onchange('from_date','to_date')
    def check_date(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise ValidationError("To Date Should Be Greater Than From Date")
    
    def _amount_check_actual(self):

        for line in self:
            where = ""
            if line.partner_id:
                part = tuple(line.partner_id.ids)
                where += " and ai.partner_id = %s " % (part)

                if line.from_date and line.to_date:
                    where += " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s' " % (line.from_date,line.to_date)

                    if line.principal_val:
                        part = tuple(line.principal_val.ids)
                        where += " and pt.principal_val = %s " % (part)

                    self.env.cr.execute('''select ail.price_subtotal,
                                               (select rate from res_currency_rate where currency_id=ai.currency_id and name <=ai.date_invoice order by name desc limit 1) as currency_rate,
                                               (select rate from res_currency_rate where currency_id=ai.currency_id and name >=ai.date_invoice order by name asc limit 1) as curr_rate,
                                               rc.name as currency_name
                                               from account_invoice as ai

                                               left join account_invoice_line as ail on ail.invoice_id = ai.id
                                               left join res_currency as rc on rc.id = ai.currency_id
                                               left join product_product as pp on pp.id = ail.product_id
                                               left join product_template as pt on pt.id = pp.product_tmpl_id
                                               left join product_category as pc on pc.id = pt.categ_id
                                               left join res_partner as rp on rp.id = ai.partner_id

                                               where ai.state in ('open','paid') and ai.type='out_invoice' %s''' %(where))
                    line_list = [i for i in self.env.cr.fetchall()]

                    line_val = 0       
                    for invoice in line_list:
                        if invoice[3] != 'INR':
                            if invoice[1]:
                                line_val += invoice[0]/invoice[1]
                            if invoice[1] == None:
                                line_val += invoice[0]/invoice[2]
                        else:
                            line_val += invoice[0]

                    line.update({'value_actual':line_val})

                                                        
class BudgetInfo(models.Model):
    _name = "fnet.budget.info"

    partner_id      = fields.Many2one('res.partner',string='Partner')
    #~ part_name       = fields.Char(related='partner_id.name', string='Customer',store=True)
    categ_id        = fields.Many2one('product.category', string='Product Category')
    from_date       = fields.Date(string='From date',required=True,default=lambda *a: time.strftime('%Y-%m-01'))
    to_date         = fields.Date(string='To date',required=True,default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    budget_value    = fields.Float(string='Budget Value')
    actual_value    = fields.Float(compute='_actual_amount_check', string='Actual Value')

    @api.model
    def create(self,vals):
        partner = super(BudgetInfo, self).create(vals)
        obj = self.env['fnet.budget.info'].search([('partner_id','=',vals['partner_id'])])
        
        if len(obj) > 1:
            n = 0
            j = []
            k = []
            for i in obj:
                j.append(i.from_date)
                k.append(i.to_date)
               
                if n>0:
                    if vals['from_date'] >= j[n-1]:
                        if vals['from_date'] <= k[n-1]:
                            raise ValidationError("Date was already selected. Please check that")
                    else:
                        if vals['to_date'] >= j[n-1]:
                            raise ValidationError("Date was already selected. Please check that")
                
                n = n+1

    @api.onchange('from_date','to_date')
    def date_check(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise ValidationError("To Date Should Be Greater Than From Date")

    def _actual_amount_check(self):

        for line in self:
            where = ""

            if line.partner_id:
                part = tuple(line.partner_id.ids)
                where += " and pt.principal_val = %s " % (part)

                if line.from_date and line.to_date:
                    where += " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s' " % (line.from_date,line.to_date)

                    if line.categ_id:
                        categ = tuple(line.categ_id.ids)
                        where += " and pc.id =%s" % (categ)

                    self.env.cr.execute('''select ail.price_subtotal,
                                               (select rate from res_currency_rate where currency_id=ai.currency_id and name <=ai.date_invoice order by name desc limit 1) as currency_rate,
                                               (select rate from res_currency_rate where currency_id=ai.currency_id and name >=ai.date_invoice order by name asc limit 1) as curr_rate,
                                               rc.name as currency_name
                                               from account_invoice as ai

                                               left join account_invoice_line as ail on ail.invoice_id = ai.id
                                               left join res_currency as rc on rc.id = ai.currency_id
                                               left join product_product as pp on pp.id = ail.product_id
                                               left join product_template as pt on pt.id = pp.product_tmpl_id
                                               left join product_category as pc on pc.id = pt.categ_id
                                               left join res_partner as rp on rp.id = ai.partner_id
                                               left join product_template as pte on pte.principal_val = rp.id

                                               where ai.state in ('open','paid') and ai.type='in_invoice' %s''' %(where))
                    line_list = [i for i in self.env.cr.fetchall()]

                    line_val = 0       
                    for invoice in line_list:
                        if invoice[3] != 'INR':
                            if invoice[1]:
                                line_val += invoice[0]/invoice[1]
                            if invoice[1] == None:
                                line_val += invoice[0]/invoice[2]
                        else:
                            line_val += invoice[0]

                    line.update({'actual_value':line_val})
                    
class ProductPrincipal(models.Model):
    _inherit = 'product.template'

    principal_val  = fields.Many2one('res.partner',string="Principal")
    
    
class ResCompany(models.Model):
    _inherit = 'res.company'

    tin_number=fields.Char('TIN No', size=14, required=True)
