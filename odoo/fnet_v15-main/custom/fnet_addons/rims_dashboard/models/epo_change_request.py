from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class EpoChangeRequest(models.Model):
    _name='epo.change.request'
    _description = 'Epo Change Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    customer_id = fields.Many2one('rims.customer.master',string='Customer',required=True,tracking=True)
    state = fields.Selection([('draft','Draft'),('submit','Verification'),('verify','Waiting For Approval'),('approve','Approved'),('cancel','Refuse'),('refuse','Cancel')],default='draft',tracking=True)
    epo_details_change_add_ids = fields.One2many('epo.detail.change','epo_detail_id')
    # epo_details_change_remove_ids=fields.One2many('epo.detail.change','epo_detail_id', 'epo_remove_rel')
    requested_by = fields.Many2one('res.users',string="Requested By",default=lambda self: self.env.user)
    is_admin = fields.Boolean(compute='_is_manager')
    is_manager = fields.Boolean(compute='_is_admin')
    requested_date = fields.Date('Requested Date',default=fields.Date.context_today,readonly=True)
    approved_date = fields.Date('Approved Date',compute='_compute_date',store=True,readonly=True)
    reason = fields.Text('Reason For Refuse')
    ticket_no = fields.Char('Ticket No', required=True)

    epo_count = fields.Integer(string="Current EPO's Count")
    first_epo_count = fields.Integer(string="EPO's Count as per the Contract", related='customer_id.first_epo_count')
    last_epo_count = fields.Integer(string="EPO's Count After the Change Request.")


    @api.onchange('customer_id')
    def onchange_for_first_epo_count(self):
        self.epo_count = self.customer_id.epo_count

    @api.onchange('epo_details_change_add_ids')
    def onchange_for_epo_details_change_add_ids(self):
        for rec in self:
            if rec.state == 'draft':
                epo_count = rec.customer_id.epo_count

                add_count = len(rec.epo_details_change_add_ids.filtered(lambda x: x.request_action == 'add'))
                remove_count = len(rec.epo_details_change_add_ids.filtered(lambda x: x.request_action == 'remove'))

                rec.last_epo_count = epo_count + add_count - remove_count



    @api.constrains('state','reason')
    def refuse_reason(self):
        for rec in self:
            if rec.state == 'cancel' and not rec.reason:
                raise ValidationError("Reason For Refuse the EPO Change Request ")

    @api.depends('state')
    def _compute_date(self):
        for rec in self:
            if rec.state == 'approve':
                rec.approved_date = fields.Date.context_today(self)
            else:
                rec.approved_date =False

    def action_draft(self):
        for rec in self:
            rec.state='draft'


    def action_refuse(self):
        for rec in self:
            rec.state='refuse'

    def name_get(self):
        result = []
        for rec in self:
            name = "EPO Change Request -" + rec.customer_id.name
            result.append((rec.id, name))
        return result

    def _is_manager(self):
        for rec in self:
            if self.env.user.has_group('rims_dashboard.group_rims_administrator'):
                rec.is_admin = True
            else:
                rec.is_admin = False

    def _is_admin(self):
        for rec in self:
            if self.env.user.has_group('rims_dashboard.group_rims_soc'):
                rec.is_manager = True
            else:
                rec.is_manager = False



    def get_mail_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        url += '/web#id=%s&model=epo.change.request&view_type=form' % (self.id)
        return url

    def soc_approve(self):
        if not self.epo_details_change_add_ids:
            raise ValidationError(_('Please fill in the EPO Details Tab'))

        users_login = ''
        admin_users = self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('rims_dashboard.group_rims_administrator').id)])
        soc_users = self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('rims_dashboard.group_rims_soc').id)])

        filtered_admin_users = admin_users - soc_users

        for user in filtered_admin_users:
            users_login += user.login
            users_login += ', '

        subject = "%s's EPO Change Request" % (str(self.customer_id.name))
        rows = ""
        for index, detail in enumerate(self.epo_details_change_add_ids, start=1):
            rows += f"""
            <tr>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{index}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.request_action}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.device_name_change}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.ip_address_epo}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.epo_type_change_id.name}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.device_category_change_id.name}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.platform_change_id.name}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.technology_change_id.name}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.folder_change}</td>
            </tr>
            """

        body = f"""
        <table border="0" cellpadding="0" cellspacing="0" width="1000" style="background-color: white; border-collapse: collapse; margin-left: 5px;">
            <tr>
                <td valign="top" style="padding: 0px 10px;">
                    <div style="font-size: 13px; margin: 0px; padding: 0px;">
                        Dear Admin,
                        <br/><br/>
                        I would like to request your assistance in verifying the {self.customer_id.name} Customer's EPO change request. Please refer to the details below,
                        <br/><br/>
                        Ticket No : {self.ticket_no}<br/>
                        Customer Name : {self.customer_id.name}<br/>
                        <br/><br/>
                        EPO count as per the contract: {self.first_epo_count}<br/>
                        Current EPO count: {self.epo_count}<br/>
                        EPO count post-change request: {self.last_epo_count}<br/>
                        <table style="width:100%;">
                            <tr>
                                <td style="width: 200px; border: 1px solid #000;">S.no</td>
                                <td style="width: 200px; border: 1px solid #000;">Request Action</td>
                                <td style="width: 200px; border: 1px solid #000;">Device Name</td>
                                <td style="width: 200px; border: 1px solid #000;">IP Address</td>
                                <td style="width: 200px; border: 1px solid #000;">EPO Type</td>
                                <td style="width: 200px; border: 1px solid #000;">Device Category</td>
                                <td style="width: 200px; border: 1px solid #000;">Platform</td>
                                <td style="width: 200px; border: 1px solid #000;">Technology</td>
                                <td style="width: 200px; border: 1px solid #000;">Folder</td>
                            </tr>
                            {rows}
                        </table><br/>
                        <div style="padding: 16px 8px 16px 8px;">
                                <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;"
                                href={self.get_mail_url()}>
                                      View EPO Change Request
                                </a>
                                </div><br/>
                        <p>Thanks & Regards,<br/>
                                   {self.env.user.name}</p>
                    </div>
                </td>
            </tr>
        </table>
        """

        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': self.env.user.login,
            'email_to': users_login,
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()

        self.write({
            'state': 'submit',
        })

    def action_verify(self):
        users_login = ''
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('rims_dashboard.group_rims_soc'):
                users_login += user.login
                users_login += ', '
        subject = "%s's EPO Change Request" % (str(self.customer_id.name))
        rows = ""
        for index, detail in enumerate(self.epo_details_change_add_ids, start=1):
            rows += f"""
                    <tr>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{index}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.request_action}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.device_name_change}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.ip_address_epo}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.epo_type_change_id.name}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.device_category_change_id.name}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.platform_change_id.name}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.technology_change_id.name}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.folder_change}</td>
                    </tr>
                    """

        body = f"""
                <table border="0" cellpadding="0" cellspacing="0" width="1000" style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                    <tr>
                        <td valign="top" style="padding: 0px 10px;">
                            <div style="font-size: 13px; margin: 0px; padding: 0px;">
                                Dear Sir/Madam,
                                <br/><br/>
                                I would like to request your approval for the {self.customer_id.name} Customer's EPO change request. Please refer to the details below,
                                <br/><br/>
                                Ticket No : {self.ticket_no}<br/>
                                Customer Name : {self.customer_id.name}<br/>
                                <br/><br/>
                                EPO count as per the contract: {self.first_epo_count}<br/>
                                Current EPO count: {self.epo_count}<br/>
                                EPO count post-change request: {self.last_epo_count}<br/>
                                <table style="width:100%;">
                                    <tr>
                                        <td style="width: 200px; border: 1px solid #000;">S.no</td>
                                        <td style="width: 200px; border: 1px solid #000;">Request Action</td>
                                        <td style="width: 200px; border: 1px solid #000;">Device Name</td>
                                        <td style="width: 200px; border: 1px solid #000;">IP Address</td>
                                        <td style="width: 200px; border: 1px solid #000;">EPO Type</td>
                                        <td style="width: 200px; border: 1px solid #000;">Device Category</td>
                                        <td style="width: 200px; border: 1px solid #000;">Platform</td>
                                        <td style="width: 200px; border: 1px solid #000;">Technology</td>
                                        <td style="width: 200px; border: 1px solid #000;">Folder</td>
                                    </tr>
                                    {rows}
                                </table><br/>
                                <div style="padding: 16px 8px 16px 8px;">
                                    <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;"
                                     href={self.get_mail_url()}>
                                      View EPO Change Request
                                     </a>
                                </div><br/>
                                <br/>
                                Thanks & Regards<br/>
                                {self.env.user.name}
                            </div>
                        </td>
                    </tr>
                </table>"""
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': self.env.user.login,
            'email_to': users_login,
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        self.write({
            'state': 'verify',
        })


    def soc_approved(self):

        users_login = ''
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('rims_dashboard.group_rims_soc'):
                users_login += user.login
                users_login += ', '
        for line in self.epo_details_change_add_ids:
            if line.request_action == 'add':
                vals = {
                    'device_name': line.device_name_change,
                    'ip_address': line.ip_address_epo,
                    'epo_type_id': line.epo_type_change_id.id,
                    'device_category_id': line.device_category_change_id.id,
                    'platform_id': line.platform_change_id.id,
                    'technology_id': line.technology_change_id.id,
                    'service_id': line.service_change_id.ids,
                    'folder': line.folder_change,
                }
                self.customer_id.write({'epo_details': [(0, 0, vals)]})
            elif line.request_action == 'remove':
                self.customer_id.write({'epo_details': [(2, line.epo_details_id.id, 0)]})
            elif line.request_action == 'edit':
                vals = {
                    'device_name': line.device_name_change,
                    'ip_address': line.ip_address_epo,
                    'epo_type_id': line.epo_type_change_id.id,
                    'device_category_id': line.device_category_change_id.id,
                    'platform_id': line.platform_change_id.id,
                    'technology_id': line.technology_change_id.id,
                    'service_id': line.service_change_id.ids,
                    'folder': line.folder_change,
                }
                self.customer_id.write({'epo_details':[(1, line.epo_details_id.id, vals)]})
        subject = "%s's EPO Change Approved" % (str(self.customer_id.name))
        body = """<p>Dear <strong>SDM</strong>,</p>
                                      <p></br>
                                      Requested Epo Change Was Approved</br></br>
                                      Thank You.</br>
                                      </p>
                                      <div style="padding: 16px 8px 16px 8px;">
                                      <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;"
                                      href="%s">
                                            View EPO Change Request
                                      </a>
                                      </div>
                                      <p>Sincerely,<br/>
                                         %s</p>""" % (
            self.get_mail_url(), self.env.user.name)
        template_data = {
            'subject': subject,
            'body_html': body,
            'email_from': users_login,
            'email_to':self.requested_by.login,
        }
        template_id = self.env['mail.mail'].sudo().create(template_data)
        template_id.sudo().send()
        self.last_epo_count = self.customer_id.epo_count
        self.write({
            'state': 'approve',
        })

    # def action_epo_change_submit(self):
    #         for rec in self:
    #             rec.state='submit'

    def action_cancel(self):
        for rec in self:
            rec.state='cancel'
    
    
class EpoDetailChange(models.Model):
    _name='epo.detail.change'

    epo_detail_id=fields.Many2one('epo.change.request')
    epo_details_id=fields.Many2one('epo.details')
    name=fields.Char(related='epo_detail_id.customer_id.name')
    request_action=fields.Selection([('add','Add'),('edit','Edit'),('remove','Remove')], required=True)
    s_no_change = fields.Char(string="S.NO", store=True, readonly=True)
    device_name_change = fields.Char(string="Device Name", store=True, required=True)
    ip_address_epo = fields.Char(string="IP Address", store=True, required=True)
    epo_type_change_id = fields.Many2one('epo.type', string="EPO Type", store=True, required=True)
    device_category_change_id = fields.Many2one('device.category', string="Device Category", store=True, required=True)
    platform_change_id = fields.Many2one('service.type', string="Platform", store=True, required=True)
    technology_change_id = fields.Many2one('service.type', string="Technology", store=True, required=True)
    service_change_id = fields.Many2many('rims.service.category.line', string="Service", store=True)
    folder_change = fields.Char("Folder", required=True)
    s_no = fields.Char(string="S.NO", compute="_compute_s_no", store=True, readonly=True)

    @api.depends('epo_detail_id.epo_details_change_add_ids')
    def _compute_s_no(self):
        for record in self:
            if record.id and record.epo_detail_id:
                record.s_no = str(record.epo_detail_id.epo_details_change_add_ids.ids.index(record.id) + 1)
            else:
                record.s_no = False

    @api.constrains('ip_address_epo')
    def _check_ip_address(self):
        ipv4_pattern = r'^\d{1,3}(\.\d{1,3}){3}$'

        for record in self:
            if record.ip_address_epo:
                if not re.match(ipv4_pattern, record.ip_address_epo):
                    raise ValidationError("Invalid IP address format. Please enter a valid IPv4 address.")


    @api.onchange('epo_details_id')
    def change_request(self):
        if self.request_action in ['edit', 'remove']:
            if self.epo_details_id:
                self.device_name_change = self.epo_details_id.device_name
                self.ip_address_epo = self.epo_details_id.ip_address
                self.epo_type_change_id = self.epo_details_id.epo_type_id.id
                self.device_category_change_id = self.epo_details_id.device_category_id.id
                self.platform_change_id = self.epo_details_id.platform_id.id
                self.technology_change_id = self.epo_details_id.technology_id.id
                self.folder_change=self.epo_details_id.folder
            else:
                self.device_name_change = False
                self.ip_address_epo = False
                self.epo_type_change_id = False
                self.device_category_change_id = False
                self.platform_change_id = False
                self.technology_change_id = False
                self.folder_change = True







































