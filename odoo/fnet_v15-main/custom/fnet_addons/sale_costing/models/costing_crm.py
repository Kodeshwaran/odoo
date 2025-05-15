from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import xlrd
import xlsxwriter


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # sub_code = fields.Char(string='Code', related='sale_type_id.code')
    sale_costing_id = fields.Char('sale.costing')
    is_create_costing = fields.Boolean('Is Create Costing')
    is_proposal_submitted = fields.Boolean(related='stage_id.is_proposal_submitted')
    crm_lead_count = fields.Boolean('Crm Lead', compute='_compute_crm_lead_view')
    epo_type_id = fields.Many2one('epo.type', string='epo_type')
    service_type_ids = fields.Many2many('crm.service', 'crm_lead_id', string="Service type")
    code = fields.Char(string='Code', related='sale_type_id.code')
    stage_boolean = fields.Boolean(related='stage_id.req_stage', string="stage boolean")
    # for_costing = fields.Boolean('create costing visible')
    for_costing = fields.Boolean('create costing visible')

    def send_quest(self):
        self.for_costing = True
        url = '/tmp/'
        report_name = 'Questionnaire'
        workbook = xlsxwriter.Workbook(url + report_name + '.xlsx')
        for service in self.service_type_ids:
            sheet = workbook.add_worksheet(service.code)
            format1 = workbook.add_format({'font_name': 'Arial'})
            format = workbook.add_format(
                {'font_name': 'Arial', 'bold': True, 'bg_color': '#486646', 'font_color': 'white', 'bottom': 2})
            sheet.set_row(0, 20)
            sheet.set_column('B:B', 20)
            sheet.set_column('D:D', 15)

            sheet.write('A1', 'S.No', format)
            sheet.write('B1', 'EPO type', format)
            sheet.write('C1', 'QTY', format)
            n = 2
            s_no = 1
            epos = self.env['epo.type'].search([('service_type_id', '=', service.id)])
            for rec in epos:
                sheet.write('A' + str(n), s_no, format1)
                sheet.write('B' + str(n), rec.name if rec.name else '', format1)
                sheet.write('C' + str(n), 0, format1)
                n += 1
                s_no += 1
        workbook.close()
        fo = open(url + 'Questionnaire' + '.xlsx', "rb+")
        values = {
            'name': 'Questionnaire.xlsx',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'datas': base64.encodestring(fo.read()),
        }
        attachment_id = self.env['ir.attachment'].sudo().create(values)
        template_id = self.env.ref('sale_costing.send_questionnaire_template')
        template_id.attachment_ids = False
        template_id.attachment_ids = attachment_id
        template_id.send_mail(self.id, force_send=True)

    def sale_person(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
        user_email = employee.work_email
        return user_email

    def _compute_crm_lead_view(self):
        for rec in self:
            rec.sale_order_count = self.env['crm.lead'].search_count([
                ('sale_costing_id', '=', rec.id)
            ])

    def get_salecost_count(self):
        for rec in self:
            rec.salecost_count = self.env['sale.costing'].search_count([('opportunity_id', '=', rec.id)])

    salecost_count = fields.Integer("Sale Costing", compute='get_salecost_count')

    def create_sale_costing(self):
        # selected_lines = self.bid_received_line.filtered(lambda x: x.valid_qoute)
        # if len(selected_lines.mapped('purchase_order_id').mapped('currency_id').ids) > 1:
        #     raise UserError(_("Please select bids with same currency."))
        # # exist = []
        # # for rec in selected_lines:
        # #     if rec.requisition_line_id.id in exist:
        # #         raise UserError(_("You have selected same products more than one time."))
        # #     exist.append(rec.requisition_line_id.id)
        # if not selected_lines:
        #     return {
        #             'name': _('Warning'),
        #             'view_type': 'form',
        #             'view_mode': 'form',
        #             'res_model': 'sale.costing.warning',
        #             'type': 'ir.actions.act_window',
        #             'target': 'new',
        #             'context': {'default_requisition_id': self.id}
        #             }
        costing_id = self.env['sale.costing'].create({
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'sale_type_id': self.sale_type_id.id,
            'sale_sub_type_id': self.sale_sub_type_id.id,
            # 'currency_id': self.currency_id.id,
            # 'pricelist_id': self.currency_id.id,
        })
        # for line in self.line_ids:
        #     self.env['sale.cost.line'].create({
        #         'costing_id': costing_id.id,
        #         'product_id': line.product_id.id,
        #         'product_uom_qty': line.product_qty,
        #         'product_uom': line.product_uom_id.id,
        #         'price_unit': line.price_unit,
        #     })
        action = self.env.ref('sale_costing.action_sale_costing').read()[0]
        action['domain'] = [('id', '=', costing_id.id)]
        # self.is_create_costing= True
        self.is_proposal_submitted = self.stage_id
        return action

    def action_view_costing(self):
        action = self.env.ref('sale_costing.action_sale_costing').read()[0]
        costing_ids = self.env['sale.costing'].search([('opportunity_id', '=', self.id)])
        if len(costing_ids) > 1:
            action['domain'] = [('opportunity_id', '=', self.id)]
        else:
            action['views'] = [(self.env.ref('sale_costing.sale_costing_form').id, 'form')]
            action['res_id'] = costing_ids.id
        return action

        # self.ensure_one()
        # costing_ids = self.env['sale.costing'].search([
        #     ('sale_costing_id', '=', self.id)
        # ])
        # result = {
        #     "type": "ir.actions.act_window",
        #     "res_model": "sale.costing",
        #     "domain": [['id', 'in', costing_ids.ids]],
        #     "name": "crm Lead",
        #     'view_mode': 'tree,form',
        # }
        # if len(costing_ids) == 1:
        #     result['view_mode'] = 'form'
        #     result['res_id'] = costing_ids.id
        # return result

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_proposal_submitted = fields.Boolean('Is Proposal Submitted')
    req_stage = fields.Boolean("Is requirement validation")


class ResourceServiceType(models.Model):
    _name = "resource.service.type"

    service_id = fields.Many2one('crm.service', string="service")
    resource = fields.Selection([
        ('l1', 'L1'),
        ('l2', 'L2'),
        ('l3', 'L3')
    ], string='Resource')
    resource_qty = fields.Integer(string='Qty', default=1.0)
    service_type_id = fields.Many2one('crm.service', string='Service type')
    ctc = fields.Float(string='CTC')

class CrmService(models.Model):
    _name = 'crm.service'
    _inherit = 'mail.thread'
    _rec_name = "crm_service_type"

    crm_service_type = fields.Char(string="Name", tracking=True)
    code = fields.Char(string="Code", tracking=True)
    crm_lead_id = fields.Many2one('crm.lead')
    product_id = fields.Many2one('product.product', string='Product')
    service_margin = fields.Float('Margin')
    resource_service_ids = fields.One2many('resource.service.type', 'service_id', string="Resource")
    epo_type_id = fields.Many2one('epo.type')
    description = fields.Html('Description', translate=True)
