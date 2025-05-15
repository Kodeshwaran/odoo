# See LICENSE file for full copyright and licensing details.
from lxml import etree
from odoo import api, fields, models
import json
import base64
from io import StringIO
import xlsxwriter
import html2text
import re

class ProjectProject(models.Model):
    _inherit = 'project.project'

    members_ids = fields.Many2many('res.users', 'project_user_rel', 'project_id',
                                   'user_id', 'Project Members', help="""Project's
                               members are users who can have an access to
                               the tasks related to this project."""
                                   )
    team_id = fields.Many2one('crm.team', "Project Team",
                              domain=[('type_team', '=', 'project')], compute='_compute_project_team', store=True, readonly=False)
    # team_lead_id = fields.Many2one('res.users', string='Sales Person', related='team_id.user_id')
    # type_project = fields.Selection([('project', 'Project'), ('odoo', 'Odoo')], "Project Type", required=True)


    @api.depends('user_id')
    def _compute_project_team(self):
        for record in self:
            project_team_lead = self.env['crm.team'].search(
                [('user_id', '=', record.user_id.id), ('type_team', '=', 'project')], limit=1)
            if project_team_lead:
                record.team_id = project_team_lead
            else:
                project_team_user = self.env['crm.team'].search(
                    [('type_team', '=', 'project')])
                for rec in project_team_user:
                    for member in rec.team_members_ids:
                        if member.id == record.user_id.id:
                            record.team_id = rec.id
                            break
                if not record.team_id:
                    record.team_id = self.env['crm.team'].search([('type_team', '=', 'project')], limit=1)

    @api.onchange('team_id')
    def _get_team_members(self):
        self.update({"members_ids": [(6, 0,
                                     self.team_id.team_members_ids.ids)]})

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
        tasks = self.env['project.task'].search([('project_id', '=', self.id), ('parent_id', '=', False)], order='create_date')

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
                sheet.write('D' + str(n), s_task.start_date.strftime('%d-%m-%Y') if s_task.start_date else '', format1)
                sheet.write('E' + str(n), s_task.end_date.strftime('%d-%m-%Y') if s_task.end_date else '', format1)
                sheet.write('F' + str(n), s_task.date_start.strftime('%d-%m-%Y') if s_task.date_start else '', format1)
                sheet.write('G' + str(n), s_task.date_end.strftime('%d-%m-%Y') if s_task.date_end else '', format1)
                sheet.write('H' + str(n), s_task.stage_id.name, format1)
                sheet.write('I' + str(n), plain_text, format1)
                n += 1

        workbook.close()

        fo = open(url + 'Task Sheet' + '.xlsx', "rb+")
        values = {
            'name': 'Task sheet.xlsx',
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


class ProjectTask(models.Model):
    _inherit = 'project.task'

    user_ids_readonly = fields.Boolean(compute='_compute_user_ids_readonly', store=False)

    @api.depends('user_ids')
    def _compute_user_ids_readonly(self):
        for record in self:
            if self.env.user.has_group('project.group_project_user') and not self.env.user.has_group(
                    'project_team.group_project_team_leader'):
                record.user_ids_readonly = True
            else:
                record.user_ids_readonly = False

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(ProjectTask, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            if self.env.user.has_group('project.group_project_user') and not self.env.user.has_group('project_team.group_project_team_leader'):
                doc = etree.XML(result['arch'])
                for node in doc.xpath("//field[@name='user_ids']"):
                    node.set("readonly", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))
                result['arch'] = etree.tostring(doc)
        return result

