from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CondApprove(models.TransientModel):
    _name = 'cond.approve'


    reason = fields.Text("Reason")
    cond_id = fields.Many2one('lab.handling',string="Cond ID")

    def action_confirm(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model and active_id:
            record = self.env[active_model].browse(active_id)
            record.write({'reason_cond': self.reason,
                          'state': 'cond_approve'})
        groups = self.env.ref('lab_handling.lab_user_group_user').users
        lab_incharge = self.env.ref('lab_handling.lab_incharge_group_user').users
        users_email = []
        for user in groups:
            if user not in lab_incharge:
                if user.email:
                    users_email.append(f'{user.email}')
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)

        for users in users_email:
            name = self.env['res.users'].search([('login', '=', users)], limit=1)
            mail_body = f"""
                            <table border="0" cellpadding="0" cellspacing="0" width="1000"
                                   style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                                <tr>
                                    <td valign="top" style="padding: 0px 10px;">
                                        <div style="font-family: Helvetica, Arial, sans-serif; font-size: 12px; margin: 0px; padding: 0px;">
                                            Dear {name.name},
                                            <br/>
                                            <br/>
                                            Request your Review/approval of the {self.cond_id.name} Lab Handling. 
                                                Kindly take a moment to review/approve the form at your earliest convenience. 
                                            <br/>
                                            <br/>
                                            <a href="{base_url}" style="
                                                display: inline-block;
                                                font-size: 14px;
                                                font-weight: bold;
                                                color: white;
                                                background-color: #007BFF;
                                                padding: 10px 20px;
                                                text-decoration: none;
                                                border-radius: 5px;">
                                                View Form
                                            </a>
                                            <br/>
                                            <br/>
                                            Thanks,
                                            <br/>
                                            
                                            <br/>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            """
            mail_values = {
                'subject': "Conditional Approve",
                'body_html': mail_body,
                'email_to': users,
                'email_from': self.env.user.email,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.sudo().send()
        return {'type': 'ir.actions.act_window_close'}

class RejectReason(models.TransientModel):
    _name = 'reject.reason'

    reject_reason = fields.Text("Reason")
    reject_id = fields.Many2one('lab.handling',string="Reject ID")

    def action_confirm(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model and active_id:
            # Get the main model record
            record = self.env[active_model].browse(active_id)
            # Update the reason_cond field
            record.write({'reject_reason': self.reject_reason,
                          'state': 'reject'})

        groups = self.env.ref('lab_handling.lab_user_group_user').users
        lab_incharge = self.env.ref('lab_handling.lab_incharge_group_user').users
        users_email = []
        for user in groups:
            if user not in lab_incharge:
                if user.email:
                    users_email.append(f'{user.email}')
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)

        for users in users_email:
            name = self.env['res.users'].search([('login', '=', users)], limit=1)
            mail_body = f"""
                        <table border="0" cellpadding="0" cellspacing="0" width="1000"
                               style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                            <tr>
                                <td valign="top" style="padding: 0px 10px;">
                                    <div style="font-family: Helvetica, Arial, sans-serif; font-size: 12px; margin: 0px; padding: 0px;">
                                        Dear {name.name},
                                        <br/>
                                        <br/>
                                       The Record {self.reject_id.name} Lab Handling 
                                                is Rejected by {self.env.user.name}. 
                                        <br/>
                                        <br/>
                                        <a href="{base_url}" style="
                                            display: inline-block;
                                            font-size: 14px;
                                            font-weight: bold;
                                            color: white;
                                            background-color: #007BFF;
                                            padding: 10px 20px;
                                            text-decoration: none;
                                            border-radius: 5px;">
                                            View Form
                                        </a>
                                        <br/>
                                        <br/>
                                        Thanks,
                                        <br/>

                                        <br/>
                                    </div>
                                </td>
                            </tr>
                        </table>
                        """
            mail_values = {
                'subject': "Reject",
                'body_html': mail_body,
                'email_to': users,
                'email_from': self.env.user.email,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.sudo().send()

        return {'type': 'ir.actions.act_window_close'}