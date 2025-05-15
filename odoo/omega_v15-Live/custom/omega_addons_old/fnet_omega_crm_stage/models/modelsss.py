from odoo import api, fields, models, tools, SUPERUSER_ID
class res_partner(models.Model):
      _inherit = 'res.partner'
      test=fields.Integer(related='parent_id.id',string='Test',store=True)
      crm_id=fields.Integer(string='CRM ID',store=True,readonly=True)
       
      @api.model
      def create(self, vals):
           if vals.get('crm_id'):
               self.env.cr.execute('''select partner_id from crm_lead where id=%d''' %(vals.get('crm_id')))
               a=self.env.cr.fetchall()
               self.env.cr.execute('''select id from crm_lead where id=%d''' %(vals.get('crm_id')))
               b=self.env.cr.fetchall()
               vals.update({'parent_id':a[0][0] })
               vals.update({'crm_id':b[0][0] })
           return super(res_partner, self).create(vals)
           
      
