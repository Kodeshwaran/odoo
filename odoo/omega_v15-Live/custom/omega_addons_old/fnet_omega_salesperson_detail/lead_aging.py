from odoo import tools
from odoo import api, fields, models, _


class AgingDetailReport(models.Model):
    
    _name = "aging.report.detail"
    _description = "Lead Aging Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Date('Date')
    user_id = fields.Many2one('res.users','Salesperson')
    partner_id  = fields.Many2one('res.partner','Customer')
    team_id     = fields.Many2one('crm.team','Sales Team')
    enquiry     = fields.Char('Enquiry')
    oppor_val   = fields.Integer('To Opportunity')
    quote_val   = fields.Integer('To Quotation')
    so_val      = fields.Integer('To Sale Order')
    cl_name     = fields.Char('Lead Description')
    
        
    @api.model_cr
    def init(self):        
        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s AS (
                                   SELECT distinct on (cl.id) cl.id,cl.user_id,cl.date_order::date as date,
                                       cl.oppor_order as enquiry,cl.partner_id,cl.team_id,cl.name as cl_name,
                                       (cl.date_conversion::date-cl.create_date::date)+1 as oppor_val,
                                       (so.create_date::date-cl.date_conversion::date)+1 as quote_val,
                                       (so.confirmation_date::date-so.create_date::date)+1 as so_val
                                   FROM crm_lead AS cl

                                   LEFT JOIN sale_order AS so ON (cl.id = so.opportunity_id)
                                   
                                   WHERE cl.date_order < now() and cl.type='opportunity' and cl.date_conversion is not null and so.confirmation_date is not null
                                   )""" %(self._table))
