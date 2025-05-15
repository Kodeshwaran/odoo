from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64
from io import StringIO
import xlsxwriter
import html2text
import re



class ProjectTask(models.Model):
    _inherit = 'project.task'

    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    source_document = fields.Char(string="Source Document")
    project_value = fields.Float("Project Value")
    date_start = fields.Date("Start Date")
    date_end = fields.Date("End Date")
    number = fields.Char(string='Number', readonly=True, default=lambda self: self._generate_task_name())
    responsibility = fields.Selection([('futurenet', 'Futurenet'), ('customer', 'Customer'), ('futurenet/customer', 'Futurenet/Customer')], string='Responsibility', default='futurenet')


    @api.model
    def _generate_task_name(self):
        sequence = self.env['ir.sequence'].next_by_code('project.task')
        return sequence if sequence else 'New Task'

    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        res.update({
            'source_document': res.project_id.source_document,
            'project_value': res.project_id.project_value,
            'start_date': res.project_id.start_date,
            'end_date': res.project_id.end_date,
            'partner_id': res.project_id.partner_id.id,
            # 'name': res.name
        })
        return res

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date:
            get_hours = self.env.company.resource_calendar_id.get_work_hours_count(self.start_date, self.end_date)
            self.planned_hours = get_hours
        if self.end_date:
            self.date_deadline = self.end_date

    def _cron_task_deadline_alert(self):
        companies = self.env['res.company'].search([('enable_task_alert', '=', True)])
        for company in companies:
            tasks = self.env['project.task'].search(
                [('stage_id.enable_deadline_alert', '=', True), ('company_id', '=', company.id),
                 ('date_deadline', '!=', False)])
            filtered_tasks = []
            if company.task_deadline_alert_type == 'single':
                filtered_tasks = tasks.filtered(lambda x: x.date_deadline == fields.Date.today())
            elif company.task_deadline_alert_type == 'multi':
                due_date = fields.Date.today() + timedelta(days=company.task_deadline_alert_day)
                filtered_tasks = tasks.filtered(lambda x: x.date_deadline == due_date)
            elif company.task_deadline_alert_type == 'everyday':
                filtered_tasks = tasks.filtered(lambda x: x.date_deadline >= fields.Date.today())
            elif company.task_deadline_alert_type == 'everyday_after':
                filtered_tasks = tasks.filtered(lambda x: x.date_deadline <= fields.Date.today())
            for task in filtered_tasks:
                for user in task.user_ids:
                    url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
                    url += '/web#id=%d&view_type=form&model=%s' % (task.id, task._name)
                    values = {
                        'object': task,
                        'access_link': url,
                        'email': user.email,
                        'assignee_name': user.name,
                    }
                    template_id = self.env.ref('project_extended.project_task_deadline_alert').id
                    self.env['mail.template'].browse(template_id).with_context(values).send_mail(task.id,
                                                                                                 force_send=True)


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    enable_deadline_alert = fields.Boolean("Sent Deadline Alert")

class SaleTypeLine(models.Model):
    _inherit = 'sale.type.line'

    is_project_mail = fields.Boolean(string="Is Project")



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # technical_file = fields.Binary("Technical Document", attachment=False)
    # technical_file_name = fields.Char("Technical Document")
    technical_file = fields.Many2many('ir.attachment', 'technical_other_rel', string="Technical Document",
                                      store=True)
    scope_file_id = fields.Many2many('ir.attachment', 'scope_other_rel', string="Scope Document",
                                      store=True)
    scope_file = fields.Binary("Scope Document", attachment=False)
    scope_file_name = fields.Char("Scope Document")
    commitment_date = fields.Datetime('Delivery Date', copy=False,
                                      states={'draft': [('readonly', True)],'sent': [('readonly', True)]},
                                      help="This is the delivery date promised to the customer. "
                                           "If set, the delivery order will be scheduled based on "
                                           "this date rather than product lead times.")
    account_manager = fields.Char("Account Manager")
    solution_architect = fields.Char("Solution Architect")
    nlc_person = fields.Char("First Level Contact Person")
    nlc_mail = fields.Char("First Level Contact Person Mail Id")
    nlc_no = fields.Char("First Level Contact Person Contact Number")
    slc_person = fields.Char("Second Level Contact Person")
    slc_mail = fields.Char("Second Level Contact Person Mail Id")
    slc_no = fields.Char("Second Level Contact Person Contact Number")
    is_project_mail = fields.Boolean(string="Is Project", compute='_compute_project')
    contact_name_id = fields.Many2one('res.partner', 'Contact Name')
    team_id = fields.Many2one('crm.team', "Project Team", domain=[('type_team', '=', 'project')])
    # is_project_bool =  fields.Boolean(related="order_line.is_project_mail" ,string='Is project')
    #
    # def is_project(self):
    #     is_project_bool = ''
    #     if self.order_line.is_project_mail:
    #         self.order_line.is_project_mail = is_project_bool


    def action_confirm(self):
        if any(line.product_id.detailed_type == 'product' for line in self.order_line) and not self.commitment_date:
            raise ValidationError(_('Please Enter the Delivery Date'))
        if any(line.is_project_mail for line in self.order_line):
            # if not self.account_manager:
            #     raise ValidationError(_('Please Enter the Account Manager'))
            if not self.nlc_person:
                raise ValidationError(_('Please Enter the Next Level Contact Person'))
            if not self.nlc_no:
                raise ValidationError(_('Please Enter the Next Level Contact Person Contact Number'))
            # if not self.solution_architect:
            #     raise ValidationError(_('Please Enter the Solution Architect'))
            if not self.nlc_mail:
                raise ValidationError(_('Please Enter the Next Level Contact Person Mail Id'))
            if not self.slc_person:
                raise ValidationError(_('Please Enter the Next Level Contact Person'))
            if not self.slc_no:
                raise ValidationError(_('Please Enter the Next Level Contact Person Contact Number'))
            if not self.slc_mail:
                raise ValidationError(_('Please Enter the Next Level Contact Person Mail Id'))
            if not self.technical_file:
                raise ValidationError(_('Please Upload Technical Document'))
            if not self.scope_file_id:
                raise ValidationError(_('Please Upload Scope Document'))
        return super(SaleOrder, self).action_confirm()


    @api.onchange('partner_id')
    def onchange_partner_contact(self):
        self.contact_name_id = False
        if self.partner_id:
            contacts = self.partner_id.child_ids
            if contacts:
                self.contact_name_id = contacts[0].id
                return ({'domain': {'contact_name_id': [('id', 'in', contacts.ids)]}})

    def _compute_project(self):
        for record in self:
            is_project_mail = any(rec.is_project_mail for rec in record.order_line.product_id)
            record.is_project_mail = is_project_mail



    # def _compute_project(self):
    #     if any(line.is_project_mail for line in self.order_line):
    #         self.is_project_mail = True
    #     else:
    #         self.is_project_mail = False


    def action_update_commitment_date(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Update Delivery Date'),
            'res_model': 'commitment.date.wizard',
            'view_mode': 'form',
            'context': {
                'default_sale_id': self.id,
            },
            'target': 'new'
        }

    @api.constrains('state')
    def _new_onchange_state(self):
        # print("\n---", "Test", "--""Test""--\n")
        for rec in self.filtered(lambda r: r.state == 'sale'):
            if any(line.product_id.is_project_mail for line in rec.order_line):
                if not rec.technical_file:
                    raise ValidationError('Please attach the technical file')
                total_cost = sum(
                    request.price_subtotal for request in rec.order_line if request.product_id.is_project_mail)

                project_vals = {
                    'name': rec.opportunity_id.name,
                    'source_document': rec.name,
                    'partner_id': rec.partner_id.id,
                    'project_seq': 'New',
                    'project_value': total_cost,
                    'date_start': fields.Date.today(),
                    'technical_file': rec.technical_file,
                    'scope_file_name': rec.scope_file_name,
                    'scope_file': rec.scope_file,
                    'scope_file_id': rec.scope_file_id,
                    'team_id': rec.team_id.id,
                }

                project = self.env['project.project'].sudo().create(project_vals)
                project.sudo().update({"members_ids": [(6, 0,
                                              project.team_id.team_members_ids.ids)]})

                mail_template = self.env.ref('project_extended.email_template_project_create_alert')

                mail_template.attachment_ids = [(6, 0, rec.technical_file.ids + rec.scope_file_id.ids)]

                # mail_template.attachment_ids = [(6, 0, rec.technical_file.ids)]
                # mail_template.attachment_ids = [(6, 0, rec.scope_file_id.ids)]
                if rec.vendor_attachment:
                    mail_template.attachment_ids = [(4, attachment.id) for attachment in rec.vendor_attachment]
                ctx = {
                    'project_id': project.project_code
                }
                mail_template.with_context(ctx).sudo().send_mail(rec.id, force_send=True)

    def action_user_email(self):
        user_email = self.env.user.email
        return user_email

    def action_user_name(self):
        user_name = self.env.user.name
        return user_name

    def action_project_email(self):
        company_id = self.env.user.company_id
        return company_id.project_email if company_id else None


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_project_mail = fields.Boolean(string="Is Project", related='product_id.is_project_mail')


class ProjectProject(models.Model):
    _inherit = "project.project"

    source_document = fields.Char("Source Document")
    project_seq = fields.Char(string="Project ID", copy=False, default=lambda self: _('New'))
    project_code = fields.Char(string="Project ID", copy=False, default=lambda self: _('New'))
    project_value = fields.Float("Project Value")
    start_date = fields.Date("Start Date", default=fields.Date.today)
    end_date = fields.Date("End Date")
    # vendor_attachment = fields.Many2many('ir.attachment','vendor_attachment_rel', string="Vendor PO Attachment")
    # vendor_attachment_file = fields.Char('Vendor PO Attachment')
    # technical_file = fields.Binary("Technical Document")
    # technical_file_name = fields.Char("Technical Document")
    technical_file = fields.Many2many('ir.attachment', string="Technical Document",
                                      store=True)
    scope_file_id = fields.Many2many('ir.attachment', 'scope_file_id_rel', string="scope Document",
                                      store=True)
    scope_file = fields.Binary("Scope Document", attachment=False)
    scope_file_name = fields.Char("Scope Document")
    is_done = fields.Boolean(string="Is Done")
    sign_off_date = fields.Date("Sign Off Date")
    invoice_requested_date = fields.Date("Invoice Requested Date")
    account_manager = fields.Char("Account Manager")
    is_closure = fields.Boolean("Is closure")
    # privacy_visibility = fields.Selection([
    #     ('followers', 'Invited employees'),
    #     ('employees', 'All employees'),
    #     ('portal', 'Invited portal users and all employees'),
    # ],
    #     string='Visibility', required=True,
    #     default='followers',
    #     help="Defines the visibility of the tasks of the project:\n"
    #          "- Invited employees: employees may only see the followed project and tasks.\n"
    #          "- All employees: employees may see all project and tasks.\n"
    #          "- Invited portal users and all employees: employees may see everything."
    #          "   Invited portal users may see project and tasks followed by.\n"
    #          "   them or by someone of their company.")



    def action_project_report(self):
        output = StringIO()
        url = '/tmp/'
        report_name = "Task Sheet"
        workbook = xlsxwriter.Workbook(url + report_name + '.xlsx')
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_name': 'Arial'})
        format = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center', 'bg_color':'072B70', 'font_color': 'white'})
        project = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center', 'bg_color':'404040', 'font_color': 'white'})
        taskf = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center', 'bg_color':'BDD7EE'})

        sheet.set_column('A:A', 5)
        sheet.set_column('C:I', 20)
        sheet.set_column('B:B', 40)

        sheet.write('A1', 'S.No', format)
        sheet.write('B1', 'Task', format)
        sheet.write('C1', 'Responsibility', format)
        sheet.write('D1', 'Scheduled Start date', format)
        sheet.write('E1', 'Scheduled End date', format)
        sheet.write('F1', 'Actual Start date', format)
        sheet.write('G1', 'Actual End date', format)
        sheet.write('H1', 'Status', format)
        sheet.write('I1', 'Remarks', format)
        sheet.merge_range('A2:B2', self.name, project)

        n = 2
        a = 0
        s_no = 0
        tasks = self.env['project.task'].search([('project_id', '=', self.id), ('parent_id', '=', False)])

        def number_to_alphabet(n):
            string = ""
            while n > 0:
                n -= 1
                string = chr(n % 26 + 65) + string
                n //= 26
            return string


        for task in tasks:
            n += 1
            a += 1
            sheet.write('A' + str(n), number_to_alphabet(a), taskf)
            sheet.write('B' + str(n), task.name, taskf)

            n += 1
            s_tasks = self.env['project.task'].search([('parent_id', '=', task.id)])
            s_no = 0
            for s_task in s_tasks:
                html_content = s_task.description
                if html_content:
                    plain_text = html2text.html2text(html_content)
                    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
                else:
                    plain_text = ""




                s_no += 1
                sheet.write('A' + str(n), s_no, format1)
                sheet.write('B' + str(n), s_task.name, format1)
                sheet.write('C' + str(n), s_task.responsibility if s_task.responsibility else '', format1)
                sheet.write('D' + str(n), s_task.start_date.strftime('%Y-%m-%d') if s_task.start_date else '', format1)
                sheet.write('E' + str(n), s_task.end_date.strftime('%Y-%m-%d') if s_task.end_date else '', format1)
                sheet.write('F' + str(n), s_task.date_start.strftime('%Y-%m-%d') if s_task.date_start else '', format1)
                sheet.write('G' + str(n), s_task.date_end.strftime('%Y-%m-%d') if s_task.date_end else '', format1)
                sheet.write('H' + str(n), s_task.stage_id.name, format1)
                sheet.write('I' + str(n), plain_text, format1)
                n += 1

        workbook.close()

        fo = open(url + 'Task Sheet' + '.xlsx', "rb+")
        values = {
            'name': 'EPO_Details.xlsx',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'datas': base64.encodestring(fo.read()),
        }
        attachment_id = self.env['ir.attachment'].sudo().create(values)
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }

    @api.constrains('stage_id')
    def _new_onchange_project_stage(self):
        for rec in self:
            if rec.stage_id.name == "Done":
                rec.is_done = True
            else:
                rec.is_done = False

    def action_project_closure(self):
        for rec in self:
            rec.is_closure = True
            template = self.env.ref('project_extended.email_template_closure_project')
            attachment_list = []
            if rec.technical_file:
                attachment_list.append((0, 0, {
                    'name': 'TechnicalDocument',
                    'type': 'binary',
                    'datas': rec.technical_file,
                }))
            if rec.scope_file_id:
                attachment_list.append((4, 0, {
                    'name': 'Scope Document',
                    'type': 'binary',
                    'datas': rec.scope_file_id,
                }))
            if rec.scope_file:
                attachment_list.append((0, 0, {
                    'name': 'ScopeDocument',
                    'type': 'binary',
                    'datas': rec.scope_file,
                }))
            template.attachment_ids = False
            template.attachment_ids = attachment_list
            template.send_mail(self.id, force_send=True)


    # @api.model
    # def create(self, values):
    #     if values.get('project_seq') == _('New'):
    #         values['project_seq'] = self.env['ir.sequence'].next_by_code('project.proj') or _('New')
    #     return super(ProjectProject, self).create(values)

    @api.model
    def create(self, vals):
        vals['project_code'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code('project.proj')
        return super(ProjectProject, self).create(vals)

    def action_project_email(self):
        company_id = self.env.user.company_id
        return company_id.project_email if company_id else None

    def action_assign_manager(self):
        return {
            'name': _('Assign Manager'),
            'type': 'ir.actions.act_window',
            'res_model': 'assign.manager.wizard',
            'view_mode': 'form',
            'context': {
                'default_project_id': self.id
            },
            'target': 'new'
        }


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    approval_check = fields.Boolean(compute='_compute_approval_change')
    project_approved = fields.Boolean(string="Project Approved")
    solution_architect = fields.Many2one('res.users', string="Solution Architect")
    scope_file_id = fields.Many2many('ir.attachment', 'scopee_other_rel', string="Scope Document",
                                      store=True)
    def action_update_scope_file(self):
        return {
            'name': 'Scope Document',
            'type': 'ir.actions.act_window',
            'res_model': 'scope.document.wizard',
            'view_mode': 'form',
            'context': {
                'default_opportunity_id': self.id,
            },
            'target': 'new',
        }

    def _compute_approval_change(self):
            if self.env.user == self.stage_id.project_responsible:
                if not self.project_approved:
                    self.approval_check = True
                else:
                    self.approval_check = False
            else:
                self.approval_check = False

    # def action_project_approved(self):
    #     if self.env.user.id in self.stage_id.reponsible_user.ids:
    #         if self.stage_id.project_approved:
    def action_project_approved(self):
        if not self.project_approved:
            if self.env.user == self.stage_id.project_responsible:
                subject = "Project Approval Done for %s" % self.name
                body = """
                      <p></br>
                      The Project Approval has been done for the Opportunity %s.</br></br>
                      </p>
                      <p>Thank You,<br/>
                         %s</p>""" % (self.name, self.env.user.name)
                template_data = {
                    'subject': subject,
                    'body_html': body,
                    'email_from': self.env.user.login,
                    'email_to': self.user_id.login,
                }
                template_id = self.env['mail.mail'].sudo().create(template_data)
                template_id.sudo().send()
                project_approval_stage = self.env['crm.stage'].sudo().search([('is_project_approved', '=', True)], limit=1)
                self.write({'project_approved': True})
                if project_approval_stage:
                    self.write({'stage_id': project_approval_stage.id})
            else:
                raise UserError("You are not allowed to do project approval")
        else:
            raise ValidationError("Project approval is already done")

    def action_project_rejected(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reason for Reject'),
            'res_model': 'reason.wizard',
            'view_mode': 'form',
            'context': {
                'default_opportunity_id': self.id,
            },
            'target': 'new',

        }

    def pre_sale_person_mail(self):
        assigner_mail = []
        users = self.sale_type_id.pre_sale_users
        for user in users:
            assigner_mail.append(user.login)
        assigner_mail = str(assigner_mail).replace("[", "").replace("]", "").replace("'", "")
        return assigner_mail

    def action_sale_quotations_new(self):
        if self.partner_type == 'new' and not self.partner_id:
            raise UserError(_('Request a new Customer through the Customer Creation Request button'))
        return super(CrmLead, self).action_sale_quotations_new()
        # default_context = {
        #     'default_technical_file_name': self.technical_file_name,
        #     'default_technical_file': self.technical_file,
        #     'default_scope_file': self.scope_file,
        #     'default_scope_file_name': self.scope_file_name,
        #     'default_partner_id': self.partner_id.id,
        #     'default_sale_type_id': self.sale_type_id.id,
        # }
        # if not self.partner_id:
        #     action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
        #     action['context'] = default_context
        #     return action
        # else:
        #     action = self.action_new_quotation()
        #     action['context'] = default_context
        #     return action

    def action_new_quotation(self):
        res = super(CrmLead, self).action_new_quotation()
        res['context']['default_tech_file'] = self.tech_file
        res['context']['default_technical_file_name'] = self.technical_file_name
        res['context']['default_technical_file'] = self.technical_file.ids
        res['context']['default_scope_file_id'] = self.scope_file_id.ids
        res['context']['default_scope_file'] = self.scope_file
        res['context']['default_scope_file_name'] = self.scope_file_name
        return res

    @api.onchange('stage_id')
    def onchange_stage_field(self):
        if self.stage_id.is_pre_sale:
            self.solution_architect = self.env.user.id
            self.project_approved = False
        if self.pre_sale and self.stage_id.project_approval and self.expected_revenue >= self.stage_id.project_revenue_limit:
            subject = "Presale Submitted for %s" % self.name
            body = """<p>Dear <strong>%s</strong>,</p>
                                          <p></br>
                                          Pre-Sale Submitted for the Opportunity %s. Kindly proceed with your approval.</br></br>
                                          Thank You.</br>
                                          </p>
                                          <p>Sincerely,<br/>
                                             %s</p>""" % (self.stage_id.project_responsible.name, self.name, self.env.user.name)
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_from': self.env.user.login,
                'email_to': self.stage_id.project_responsible.login,
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
        elif self.stage_id.is_pre_sale:
            subject = "Presale Submitted for %s" % self.name
            body = """<p>Dear <strong>%s</strong>,</p>
                                                      <p></br>
                                                      Pre-Sale Submitted for the Opportunity %s.</br></br>
                                                      Thank You.</br>
                                                      </p>
                                                      <p>Sincerely,<br/>
                                                         %s</p>""" % (self.user_id.name, self.name, self.env.user.name)
            template_data = {
                'subject': subject,
                'body_html': body,
                'email_from': self.env.user.login,
                'email_to': self.user_id.login,
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_project_mail = fields.Boolean(string="Is Project")

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    pre_sale_requested = fields.Boolean(string="Pre Sale Requested")
    reponsible_user = fields.Many2many('res.users',string='Responsible',)
    project_approval = fields.Boolean(string='Project Approval')
    project_revenue_limit = fields.Float()
    project_responsible = fields.Many2one('res.users', string='Project Responsible')
    is_project_approved = fields.Boolean(string='Is Project Approved')



