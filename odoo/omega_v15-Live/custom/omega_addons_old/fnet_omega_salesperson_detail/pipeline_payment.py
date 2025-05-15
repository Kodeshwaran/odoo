from odoo import tools
from odoo import api, fields, models, _


class PipelinePaymentReport(models.Model):
    
    _name = "pipeline.payment.detail"
    _description = "Pipeline Payment Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Date('Date')
    user_id = fields.Many2one('res.users','Salesperson')
    partner_id  = fields.Many2one('res.partner','Customer')
    quote_amt   = fields.Float('Pipeline')
    so_amt      = fields.Float('Saleorder')
    inv_amt     = fields.Float('Invoice')
    payment     = fields.Float('Payment')
    enquiry     = fields.Char('Enquiry')
    
    
    @api.model_cr
    def init(self):                      
        
        tools.drop_view_if_exists(self._cr, "sp_quotess_value")
        self.env.cr.execute(""" CREATE or REPLACE VIEW sp_quotess_value AS 
                                    (SELECT distinct on (cl.id) cl.id,cl.user_id,cl.oppor_order as enquiry,cl.partner_id,
                                        (CASE WHEN so.state in ('draft','sent') THEN so.amount_untaxed ELSE 0 END) AS quote_amt                                    
                                        FROM crm_lead AS cl
                                        LEFT JOIN sale_order AS so ON (cl.id=so.opportunity_id)
                                        WHERE so.state in ('draft','sent') and cl.type='opportunity'
                                        ORDER BY cl.id desc)""")
        
        
        tools.drop_view_if_exists(self._cr, "sp_saleorders_value")               
        self.env.cr.execute(""" CREATE or REPLACE VIEW sp_saleorders_value AS (
                                    SELECT distinct ON (so.id) so.id,cl.user_id,so.amount_untaxed AS so_amt,cl.oppor_order as enquiry,cl.partner_id
                                    FROM sale_order AS so
                                    LEFT JOIN sale_order_line sol ON (sol.order_id=so.id)
                                    LEFT JOIN crm_lead AS cl ON (cl.id = so.opportunity_id)
                                    
                                    WHERE so.state in ('done','sale') and sol.qty_invoiced=0 --and cl.date_order between date_trunc('month', now())- interval '3 month' and now()
                                    GROUP BY so.id,cl.user_id,so.amount_untaxed,cl.oppor_order,cl.partner_id )""")
        
        
        tools.drop_view_if_exists(self._cr, "sp_invoices_value")                     
        self.env.cr.execute("""CREATE or REPLACE VIEW sp_invoices_value AS (
                                   SELECT distinct ON (ai.id) ai.id,cl.user_id,cl.oppor_order as enquiry,cl.partner_id,ai.date_invoice,
                                   CASE WHEN ai.state!='paid' and ai.residual=ai.amount_total THEN ai.amount_total
                                        WHEN ai.state!='paid' and ai.residual!=ai.amount_total THEN ai.residual ELSE 0 END AS inv_amt,
                                   CASE WHEN ai.state='paid' and ai.residual=0 THEN (ai.amount_total)
                                        WHEN ai.state!='paid' and ai.residual!=ai.amount_total THEN ai.amount_total-ai.residual ELSE 0 end AS payment
                                   FROM account_invoice AS ai
                                   LEFT JOIN sale_order AS so ON (so.name = ai.origin)
                                   LEFT JOIN crm_lead AS cl ON (cl.id = so.opportunity_id)
                                   
                                   WHERE ai.state not in ('cancel') and ai.type='out_invoice' --and cl.date_order between date_trunc('month', now())- interval '3 month' and now()
                                   GROUP BY ai.id,cl.user_id,ai.amount_untaxed,cl.oppor_order,cl.partner_id,ai.date_invoice )""")
        
        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s AS (
                                   SELECT distinct on (cl.id) cl.id,cl.user_id,siv.date_invoice as date,cl.oppor_order as enquiry,cl.partner_id,
                                   sqv.quote_amt,ssv.so_amt,siv.inv_amt,siv.payment
                                   FROM crm_lead AS cl
                                   LEFT JOIN sale_order AS so ON (so.opportunity_id = cl.id)
                                   LEFT JOIN account_invoice AS ai ON (ai.origin = so.name)
                                   LEFT JOIN sp_quotess_value AS sqv ON (sqv.id = cl.id)
                                   LEFT JOIN sp_saleorders_value AS ssv ON (ssv.id = so.id)
                                   LEFT JOIN sp_invoices_value AS siv ON (siv.id = ai.id)
                                   WHERE siv.date_invoice < now() and siv.date_invoice is not null
                                   GROUP BY cl.id,sqv.quote_amt,ssv.so_amt,siv.inv_amt,siv.payment,siv.date_invoice )""" %(self._table))
