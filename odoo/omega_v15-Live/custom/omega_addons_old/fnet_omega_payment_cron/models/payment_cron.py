import logging
from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource
import datetime
import time
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import calendar
from calendar import monthrange


class payment_remainder(models.Model):
    _inherit = 'account.invoice'
    
    @api.multi
    def payment_remainder_cron(self):
        payment_info = self.env['account.invoice']      
        send_mail = self.env['mail.mail']
        mail_ids=[]
        mail_template = self.env['mail.template']       
        payment_id= payment_info.search([])
        now=datetime.datetime.strptime(time.strftime("%Y-%m-%d"), '%Y-%m-%d').date()
        no_of_days = 5
        dt = str(now + timedelta(days = no_of_days))              
        invoice_obj = self.env['account.invoice'].search([('date_due','=', dt), ('state', 'in', ('draft','open'))])
        for rec in invoice_obj:
            var = 0
            var = var+1
            payment_details = ''' <table width = 100% style ="border-collapse: collapse; border:1px solid black"> <tr>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> S.No. </th>            
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Customer </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Invoice Date </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Invoice No. </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Lead </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Salesperson </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Due Date </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Total </th>
            <th style ="border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;text-align:left"> Amount Due </th>
            <th style ="border-collapse: collapse; border-bottom:1px solid black;border-bottom:1px solid black;text-align:left"> Status </th> </tr>
            '''                                    
            payment_details += ''' <tr>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>                
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "border-collapse: collapse; border-right:1px solid black;border-bottom:1px solid black;padding: 5px;"> %s </td>
                    <td style = "padding: 5px;border-bottom:1px solid black;"> %s </td> </tr>
                    ''' %(var,rec.partner_id.name,rec.date_invoice,rec.number,rec.lead_name,rec.user_id.login, rec.date_due,rec.amount_total,rec.residual,rec.state)
            payment_details+= "</table>"
            self.env.cr.execute('''SELECT DISTINCT
                      res_users.login
                      FROM res_groups_users_rel
                      JOIN res_groups
                      ON res_groups.id = res_groups_users_rel.gid
                      JOIN public.res_users
                      ON res_groups_users_rel.uid = res_users.id
                      JOIN ir_module_category
                      ON res_groups.category_id = ir_module_category.id
                      WHERE res_groups.name='Adviser' and ir_module_category.name='Accounting & Finance'  ''')
            obj = self.env.cr.dictfetchall()
            for res in obj:
                email_to = res['login']
                subject = "Remainder regarding Payment!"
                body = _("Dear Manager,")
                body += _("<br/> <br/>The following invoices are reaching their due date in 5day's. <br/> Due date: %s  %s: <br/>" %(rec.date_due,payment_details))
                footer="With Regards,<br/>ADMIN"
                mail_ids.append(send_mail.create({
                            'email_to': email_to,
                            'subject': subject,
                            'body_html':'''<span  style="font-size:14px"><br/>
                                <br/>%s<br/>
                                <br/>%s</span>''' %(body,footer),
                        }))
                for i in range(len(mail_ids)):
                    mail_ids[i].send(self)

    

