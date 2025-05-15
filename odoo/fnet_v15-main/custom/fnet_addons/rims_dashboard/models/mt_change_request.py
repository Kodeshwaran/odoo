from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class MtChangeRequest(models.Model):
    _name='mt.change.request'
    _description = 'Mt Change Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    customer_id = fields.Many2one('rims.customer.master',string='Customer',required=True,tracking=True)
    state = fields.Selection([('draft','Draft'),('submit','Verification'),('verify','Waiting For Approval'),('approve','Approved'),('cancel','Refuse'),('refuse','Cancel')],default='draft',tracking=True)
    mt_details_change_add_ids = fields.One2many('mt.detail.change','mt_detail_id')
    # epo_details_change_remove_ids=fields.One2many('epo.detail.change','epo_detail_id', 'epo_remove_rel')
    requested_by = fields.Many2one('res.users',string="Requested By",default=lambda self: self.env.user)
    is_admin = fields.Boolean(compute='_is_manager')
    is_manager = fields.Boolean(compute='_is_admin')
    requested_date = fields.Date('Requested Date',default=fields.Date.context_today,readonly=True)
    approved_date = fields.Date('Approved Date',compute='_compute_date',store=True,readonly=True)
    reason = fields.Text('Reason For Refuse')
    ticket_no = fields.Char('Ticket No', required=True)







    @api.constrains('state','reason')
    def refuse_reason(self):
        for rec in self:
            if rec.state == 'cancel' and not rec.reason:
                raise ValidationError("Reason For Refuse the Monitoring Thresholds Change Request ")

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
            name = "Monitoring Thresholds Change Request -" + rec.customer_id.name
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
        url += '/web#id=%s&model=mt.change.request&view_type=form' % (self.id)
        return url

    def soc_approve(self):
        if not self.mt_details_change_add_ids:
            raise ValidationError(_('Please fill in the mt Details Tab'))

        users_login = ''
        admin_users = self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('rims_dashboard.group_rims_administrator').id)])
        soc_users = self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('rims_dashboard.group_rims_soc').id)])

        filtered_admin_users = admin_users - soc_users

        for user in filtered_admin_users:
            users_login += user.login
            users_login += ', '

        subject = "%s's Monitoring Thresholds Change Request" % (str(self.customer_id.name))
        rows = ""
        for index, detail in enumerate(self.mt_details_change_add_ids, start=1):
            rows += f"""
            <tr>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{index}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.request_action}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.host_id.device_name}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.ip_address}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.service}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.criticality}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.cpu_capacity}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.cpu_warn_percentage}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.cpu_crit_percentage}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.memory_capacity}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.memory_warn_percentage}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.memory_crit_percentage}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.disk_capacity}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.disk_warn_percentage}</td>
                <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.disk_crit_percentage}</td>
            </tr>
            """

        body = f"""
        <table border="0" cellpadding="0" cellspacing="0" width="1000" style="background-color: white; border-collapse: collapse; margin-left: 5px;">
            <tr>
                <td valign="top" style="padding: 0px 10px;">
                    <div style="font-size: 13px; margin: 0px; padding: 0px;">
                        Dear Admin,
                        <br/><br/>
                        I would like to request your assistance in verifying the {self.customer_id.name} Customer's Monitoring Thresholds change request. Please refer to the details below,
                        <br/><br/>
                        Ticket No : {self.ticket_no}<br/>
                        Customer Name : {self.customer_id.name}<br/>
                        <br/><br/>
                        <table style="width:100%;">
                            <tr>
                                <td style="width: 200px; border: 1px solid #000;">S.no</td>
                                <td style="width: 200px; border: 1px solid #000;">Request Action</td>
                                <td style="width: 200px; border: 1px solid #000;">Host Name</td>
                                <td style="width: 200px; border: 1px solid #000;">IP Address</td>
                                <td style="width: 200px; border: 1px solid #000;">Service</td>
                                <td style="width: 200px; border: 1px solid #000;">Criticality</td>
                                <td style="width: 200px; border: 1px solid #000;">CPU Capacity</td>
                                <td style="width: 200px; border: 1px solid #000;">CPU Warn (%)</td>
                                <td style="width: 200px; border: 1px solid #000;">CPU Crit (%)</td>
                                <td style="width: 200px; border: 1px solid #000;">Memory Capacity</td>
                                <td style="width: 200px; border: 1px solid #000;">Memory Warn (%)</td>
                                <td style="width: 200px; border: 1px solid #000;">Memory Crit (%)</td>
                                <td style="width: 200px; border: 1px solid #000;">Disk Capacity</td>
                                <td style="width: 200px; border: 1px solid #000;">Disk Warn (%)</td>
                                <td style="width: 200px; border: 1px solid #000;">Disk Crit (%)</td>
                            </tr>
                            {rows}
                        </table><br/>
                        <div style="padding: 16px 8px 16px 8px;">
                                <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;"
                                href={self.get_mail_url()}>
                                      View Monitoring Thresholds Change Request
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
        subject = "%s's Monitoring Thresholds Change Request" % (str(self.customer_id.name))
        rows = ""
        for index, detail in enumerate(self.mt_details_change_add_ids, start=1):
            rows += f"""
                    <tr>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{index}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.request_action}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.host_id.device_name}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.ip_address}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.service}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.criticality}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.cpu_capacity}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.cpu_warn_percentage}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.cpu_crit_percentage}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.memory_capacity}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.memory_warn_percentage}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.memory_crit_percentage}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.disk_capacity}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.disk_warn_percentage}</td>
                        <td style="width: 125px;padding-left: 5px; border: 1px solid #000;">{detail.disk_crit_percentage}</td>
                     </tr>
                    """

        body = f"""
                <table border="0" cellpadding="0" cellspacing="0" width="1000" style="background-color: white; border-collapse: collapse; margin-left: 5px;">
                    <tr>
                        <td valign="top" style="padding: 0px 10px;">
                            <div style="font-size: 13px; margin: 0px; padding: 0px;">
                                Dear Sir/Madam,
                                <br/><br/>
                                I would like to request your approval for the {self.customer_id.name} Customer's  Monitoring Thresholds change request. Please refer to the details below,
                                <br/><br/>
                                Ticket No : {self.ticket_no}<br/>
                                Customer Name : {self.customer_id.name}<br/>
                                <br/><br/>
                                <table style="width:100%;">
                                    <tr>
                                        <td style="width: 200px; border: 1px solid #000;">S.no</td>
                                        <td style="width: 200px; border: 1px solid #000;">Request Action</td>
                                        <td style="width: 200px; border: 1px solid #000;">Host Name</td>
                                        <td style="width: 200px; border: 1px solid #000;">IP Address</td>
                                        <td style="width: 200px; border: 1px solid #000;">Service</td>
                                        <td style="width: 200px; border: 1px solid #000;">Criticality</td>
                                        <td style="width: 200px; border: 1px solid #000;">CPU Capacity</td>
                                        <td style="width: 200px; border: 1px solid #000;">CPU Warn (%)</td>
                                        <td style="width: 200px; border: 1px solid #000;">CPU Crit (%)</td>
                                        <td style="width: 200px; border: 1px solid #000;">Memory Capacity</td>
                                        <td style="width: 200px; border: 1px solid #000;">Memory Warn (%)</td>
                                        <td style="width: 200px; border: 1px solid #000;">Memory Crit (%)</td>
                                        <td style="width: 200px; border: 1px solid #000;">Disk Capacity</td>
                                        <td style="width: 200px; border: 1px solid #000;">Disk Warn (%)</td>
                                        <td style="width: 200px; border: 1px solid #000;">Disk Crit (%)</td>
                                    </tr>
                                    {rows}
                                </table><br/>
                                <div style="padding: 16px 8px 16px 8px;">
                                    <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;"
                                     href={self.get_mail_url()}>
                                      View Monitoring Thresholds Change Request
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
        for line in self.mt_details_change_add_ids:
            if line.request_action == 'add':
                vals = {
                'host_id' : line.host_id.id,
                'ip_address' : line.ip_address,
                'service' : line.service,
                'criticality' : line.criticality,
                'memory_capacity' : line.memory_capacity,
                'memory_warn_percentage' : line.memory_warn_percentage,
                'memory_crit_percentage' : line.memory_crit_percentage,
                'cpu_capacity':line.cpu_capacity,
                'cpu_warn_percentage':line.cpu_warn_percentage,
                'cpu_crit_percentage':line.cpu_crit_percentage,
                'disk_capacity':line.disk_capacity,
                'disk_warn_percentage':line.disk_warn_percentage,
                'disk_crit_percentage':line.disk_crit_percentage,
                }
                self.customer_id.write({'monitoring_thresholds_ids': [(0, 0, vals)]})
            elif line.request_action == 'remove':
                self.customer_id.write({'monitoring_thresholds_ids': [(2, line.mt_details_id.id, 0)]})
            elif line.request_action == 'edit':
                vals = {
                'host_id' : line.host_id.id,
                'ip_address' : line.ip_address,
                'service' : line.service,
                'criticality' : line.criticality,
                'memory_capacity' : line.memory_capacity,
                'memory_warn_percentage' : line.memory_warn_percentage,
                'memory_crit_percentage' : line.memory_crit_percentage,
                'cpu_capacity':line.cpu_capacity,
                'cpu_warn_percentage':line.cpu_warn_percentage,
                'cpu_crit_percentage':line.cpu_crit_percentage,
                'disk_capacity':line.disk_capacity,
                'disk_warn_percentage':line.disk_warn_percentage,
                'disk_crit_percentage':line.disk_crit_percentage,
                }
                self.customer_id.write({'monitoring_thresholds_ids':[(1, line.mt_details_id.id, vals)]})
        subject = "%s's Monitoring Thresholds Change Approved" % (str(self.customer_id.name))
        body = """<p>Dear <strong>SDM</strong>,</p>
                                      <p></br>
                                      Requested Monitoring Thresholds Change Was Approved</br></br>
                                      Thank You.</br>
                                      </p>
                                      <div style="padding: 16px 8px 16px 8px;">
                                      <a style="background-color:#875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px;"
                                      href="%s">
                                            View Monitoring Thresholds Change Request
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
        self.write({
            'state': 'approve',
        })

    # def action_epo_change_submit(self):
    #         for rec in self:
    #             rec.state='submit'

    def action_cancel(self):
        for rec in self:
            rec.state='cancel'
    
    
class MtDetailChange(models.Model):
    _name='mt.detail.change'

    mt_detail_id=fields.Many2one('mt.change.request')
    mt_details_id=fields.Many2one('monitoring.thresholds', string="MT Details")
    name=fields.Char(related='mt_detail_id.customer_id.name')
    request_action=fields.Selection([('add','Add'),('edit','Edit'),('remove','Remove')], required=True)
    s_no_change = fields.Char(string="S.NO", store=True, readonly=True)
    customer_id = fields.Many2one('rims.customer.master', string="Customer")
    cust_id = fields.Many2one('rims.customer.master', string="Customer")
    host_name = fields.Char(string="Host Name")

    host_id = fields.Many2one('epo.details', string="Host Name")
    ip_address = fields.Char(string="IP Address")
    service = fields.Char(string="Service")
    criticality = fields.Char(string="Criticality")
    memory_capacity = fields.Char()
    memory_warn_percentage = fields.Float()
    memory_crit_percentage = fields.Float()
    cpu_capacity = fields.Char()
    cpu_warn_percentage = fields.Float()
    cpu_crit_percentage = fields.Float()
    disk_capacity = fields.Char()
    disk_warn_percentage = fields.Float()
    disk_crit_percentage = fields.Float()
    s_no = fields.Char(string="S.NO", compute="_compute_s_no", store=True, readonly=True)


    @api.onchange('mt_details_id')
    def change_request(self):
        if self.request_action in ['edit', 'remove']:
            if self.mt_details_id:
                self.host_id = self.mt_details_id.host_id.id
                self.ip_address = self.mt_details_id.ip_address
                self.service = self.mt_details_id.service
                self.criticality = self.mt_details_id.criticality
                self.memory_capacity = self.mt_details_id.memory_capacity
                self.memory_warn_percentage = self.mt_details_id.memory_warn_percentage
                self.memory_crit_percentage = self.mt_details_id.memory_crit_percentage
                self.cpu_capacity=self.mt_details_id.cpu_capacity
                self.cpu_warn_percentage=self.mt_details_id.cpu_warn_percentage
                self.cpu_crit_percentage=self.mt_details_id.cpu_crit_percentage
                self.disk_capacity=self.mt_details_id.disk_capacity
                self.disk_warn_percentage=self.mt_details_id.disk_warn_percentage
                self.disk_crit_percentage=self.mt_details_id.disk_crit_percentage
            else:
                self.host_id = False
                self.ip_address = False
                self.service = False
                self.criticality = False
                self.memory_capacity = False
                self.memory_warn_percentage = False
                self.memory_crit_percentage = False
                self.cpu_capacity = False
                self.cpu_warn_percentage = False
                self.cpu_crit_percentage = False
                self.disk_capacity = False
                self.disk_warn_percentage = False
                self.disk_crit_percentage = False

    @api.onchange('host_id')
    def change_request_host(self):
        if self.request_action == 'add':
            self.ip_address = self.host_id.ip_address

    @api.depends('mt_detail_id.mt_details_change_add_ids')
    def _compute_s_no(self):
        for record in self:
            if record.id and record.mt_detail_id:
                record.s_no = str(record.mt_detail_id.mt_details_change_add_ids.ids.index(record.id) + 1)
            else:
                record.s_no = False

    @api.constrains('ip_address')
    def _check_ip_address(self):
        ipv4_pattern = r'^\d{1,3}(\.\d{1,3}){3}$'

        for record in self:
            if record.ip_address:
                if not re.match(ipv4_pattern, record.ip_address):
                    raise ValidationError("Invalid IP address format. Please enter a valid IPv4 address.")
