from odoo import tools
from odoo import api, fields, models, _


class SalepersonReport(models.Model):
    _name = "saleperson.detail.report"
    _description = "Salesperson Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Date('Date')
    user_id = fields.Many2one('res.users','Salesperson')
    lead = fields.Integer('No Of Lead')
    opportunity = fields.Integer('No Of Opportunity')
    expected_revenue=fields.Float('Funnel')
    partner_id = fields.Many2one('res.partner','Customer')
    enquiry = fields.Char('Enquiry')
    cl_name = fields.Char('Lead Description')
    exp_close  = fields.Date('Expected Closing')
    conv_ratio = fields.Float('Conversion Ratio')
    
    @api.model_cr
    def init(self):
        
        tools.drop_view_if_exists(self._cr, "sp_lead_value")                    
        self.env.cr.execute(""" CREATE or REPLACE VIEW sp_lead_value AS (                            
                                    SELECT distinct ON (cl.id) cl.id,cl.user_id,cl.name as cl_name,count(*) AS lead
                                    FROM crm_lead AS cl
                                    
                                    WHERE cl.date_order <now() and (cl.type='lead' or date_conversion is not null)
                                    GROUP BY cl.id )""")              
        
        
        tools.drop_view_if_exists(self._cr, "sp_quote_value")
        self.env.cr.execute(""" CREATE or REPLACE VIEW sp_quote_value AS (SELECT DISTINCT ON (cl.id) cl.id,cl.user_id,cl.planned_revenue as expected_revenue,
                                    count(*) AS opportunity,cl.partner_id,cl.oppor_order as enquiry,cl.date_deadline::date as exp_close,cl.name as cl_name
                                    FROM crm_lead AS cl
                                        LEFT JOIN sale_order AS so ON (cl.id=so.opportunity_id)
                                        WHERE cl.date_order < now() and cl.date_conversion is not null --cl.date_order between date_trunc('month', now())- interval '3 month' and now()
                                        and (so.state in ('draft','sent') or cl.type='opportunity')
                                    GROUP BY cl.id,cl.user_id,so.amount_untaxed,so.state,cl.partner_id,cl.oppor_order )""")                                        
                                    
                        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s AS (
                                   SELECT distinct on (slv.id) slv.id,cl.user_id,cl.date_order::date as date,slv.lead,sqv.opportunity,sqv.expected_revenue,
                                       sqv.partner_id,cl.oppor_order AS enquiry,cl.name as cl_name,sqv.exp_close,
                                       
                                       (sqv.opportunity::float/slv.lead::float) AS conv_ratio
                                       
                                       --(SELECT (a2.oppor::float/a1.lead::float) AS conv_ratio FROM 
                                           --(SELECT count(*) AS lead FROM crm_lead cl WHERE cl.date_order < now() and cl.create_date is not null)a1,
                                           --(SELECT count(*) AS oppor FROM crm_lead cl WHERE cl.date_order < now() and cl.type='opportunity' and cl.date_conversion is not null)a2)                                                                      
                                                                          
                                       FROM crm_lead AS cl
                                       LEFT JOIN sale_order AS so ON (so.opportunity_id = cl.id)
                                       LEFT JOIN account_invoice AS ai ON (ai.origin = so.name)
                                       LEFT JOIN sp_lead_value AS slv ON (slv.id = cl.id)
                                       LEFT JOIN sp_quote_value AS sqv ON (sqv.id = cl.id)
                                       
                                       WHERE cl.date_order < now()
                                       --GROUP BY slv.id,slv.lead,sqv.opportunity,sqv.expected_revenue,sqv.partner_id,sqv.exp_close,
                                       --cl.user_id,cl.date_order,cl.oppor_order,cl.name
                                       )""" %(self._table))
