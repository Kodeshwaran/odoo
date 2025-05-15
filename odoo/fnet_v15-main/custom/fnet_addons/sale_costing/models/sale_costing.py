from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import base64
import xlrd



STATES = [('draft', 'Draft'),
          ('confirm', 'Confirmed'),
          ('done', 'Done'),
          ('reject', 'Rejected'),
          ('cancel', 'Cancelled')]


class SaleCosting(models.Model):
    _name = "sale.costing"
    _description = 'Sale Costing'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'date desc, id desc'
    _check_company_auto = True

    # @api.depends('line_ids.price_total')
    # def _amount_total(self):
    #     """
    #     Compute the total amounts of the SC.
    #     """
    #     for order in self:
    #         price_subtotal = 0.0
    #         for line in order.line_ids:
    #             price_subtotal += line.price_total
    #         order.update({
    #             'price_subtotal': price_subtotal,
    #         })
    # #
    # @api.depends('other_lines.price_total', 'price_subtotal', 'line_ids.sale_price', 'line_ids.price_total')
    # def _amount_all(self):
    #     for order in self:
    #         other_charge_total = sale_amount_total = margin_total = finance_total = 0.0
    #         for line in order.other_lines:
    #             other_charge_total += line.price_total
    #         for line in order.line_ids:
    #             sale_amount_total += line.sale_price
    #         for line in order.line_ids:
    #             margin_total += line.margin_total
    #             finance_total += line.finance_total
    #         for line in order.other_lines:
    #             margin_total += line.margin_total
    #             finance_total += line.finance_total
    #         order.update({
    #             'additional_subtotal': other_charge_total,
    #             'amount_total': order.price_subtotal + other_charge_total,
    #             'sale_amount_total': sale_amount_total,
    #             'margin_price_total': margin_total,
    #             'finance_price_total': finance_total,
    #         })

    # def get_sale_count(self):
    #     for rec in self:
    #         order_lines = self.env['sale.order.line'].search([('sale_costing_id', '=', rec.id)])
    #         if order_lines:
    #             rec.sale_count = len(order_lines.mapped('order_id').ids)
    #         else:
    #             rec.sale_count = 0
    state = fields.Selection(STATES, string='Status', copy=False, index=True, tracking=3, default='draft')
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    date = fields.Datetime(string='Costing Date', required=True, readonly=True, index=True,
                           states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False,
                           default=fields.Datetime.now)
    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    # opportunity_id = fields.Many2one('purchase.requisition', string="Enquiry", required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)]}, required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    # company_name = fields.Selection([('di', 'Dome International'), ('does', 'Dome Oilfield Engineering & Services LLC'),
    #                                  ('daew', 'Dome Advanced Electromechanical Works LLC'),
    #                                  ('hse', 'Dome International Safety & Environment Consultants')], string="Company",
    #                                 related='company_id.company_name', store=True)
    line_ids = fields.One2many('sale.cost.line', 'costing_id', string='Costing Lines', readonly=True,
                               states={'draft': [('readonly', False)]}, auto_join=True, ondelete='cascade', copy=True)
    optional_line_ids = fields.One2many('optional.cost.line', 'costing_id', string='Costing Lines', readonly=True,
                                        states={'draft': [('readonly', False)]}, auto_join=True, ondelete='cascade', copy=True)
    other_lines = fields.One2many('other.cost.line', 'costing_id', string='Additional Charges', readonly=True,
                                  states={'draft': [('readonly', False)]}, auto_join=True, ondelete='cascade',
                                  copy=True)
    # other_cost_template_id = fields.Many2one('other.salecost.template', string="Charges Template")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id, string="Base Currency", required=True)
    note = fields.Text('Notes')
    # price_subtotal = fields.Monetary( string='Direct Cost With F&M', readonly=True, store=True)
    # additional_subtotal = fields.Monetary(compute='_amount_other_total', string='InDirect Cost With F&M', readonly=True, store=True)
    # amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    margin_percentage = fields.Float("Overall Margin(%)")
    finance_percentage = fields.Float("Finance(%)")
    margin_price_total = fields.Monetary(string='Margin', store=True, readonly=True, compute='_amount_all', tracking=4)
    # finance_price_total = fields.Monetary(string='Finance', store=True, readonly=True, compute='_amount_all', tracking=4)
    # Converison Fields
    # to_currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id, string="Selling Currency", related='pricelist_id.currency_id')
    # conversion_rate = fields.Float("Conversion Rate", default=1.0)
    sale_amount_total = fields.Monetary(string='Sale Total', store=True, readonly=True, compute='_amount_all', tracking=4)
    revision_count = fields.Integer("Revision Count")
    # pricelist_id = fields.Many2one('product.pricelist', string='Selling Currency', check_company=True,  # Unrequired company
    #                                readonly=True, states={'draft': [('readonly', False)]},
    #                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    #                                help="If you change the pricelist, only newly added lines will be affected.")
    # sale_count = fields.Integer("Sales Count", compute='get_sale_count')
    # Revision Fields
    current_revision_id = fields.Many2one('sale.costing', 'Current revision', readonly=True, copy=True)
    old_revision_ids = fields.One2many('sale.costing.summery', 'current_revision_id', 'Old revisions', readonly=True, compute='compute_summary')
    revision_number = fields.Integer('Revision', copy=False)
    unrevisioned_name = fields.Char('Order Reference', copy=False, readonly=True)
    active = fields.Boolean('Active', default=True, copy=True)
    revised_date = fields.Date(string='Revised On', index=True, copy=False)
    revised_user_id = fields.Many2one('res.users', string='Revised By', readonly=True, tracking=1,
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    parent_id = fields.Many2one('sale.costing', string='Revised From', index=True)
    cancel_reason = fields.Char("Cancel Reason")
    user_id = fields.Many2one('res.users', string='Responsible', required=False, default=lambda self: self.env.user)
    # partner_id = fields.Many2one('res.partner', string='Vendor',domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    # trade_term = fields.Char(string='Basis')
    customer_reference = fields.Char(string="Reference")
    markup_percentage = fields.Float('Markup Percentage(%)')
    overhead_percentage = fields.Float('Overhead Percentage(%)')
    is_create_quotation = fields.Boolean('Is Create Quotation')
    sale_order_count = fields.Integer('Order Count', compute='_compute_sale_quotation')
    sale_lead_count = fields.Integer('Opportunity', compute='_compute_crm_lead')
    stage_id = fields.Many2one('crm.stage')
    total_sale_cost = fields.Monetary('Total Sale Cost', compute='_compute_total_sale_cost')
    sale_type_id = fields.Many2one('sale.type', string='Sale type')
    sale_sub_type_id = fields.Many2one('sale.type.line', string='Sale sub type')
    costing_template_id = fields.Many2one('costing.template', string="Template")
    upload_file = fields.Binary(string="Upload file", tracking=True)
    file_name = fields.Char('File Name', tracking=True)
    is_generate_epo = fields.Boolean('Is generate?')
    sale_order_line_id = fields.Many2one('sale.order.line')

    @api.onchange('other_lines')
    def ctc_onchange(self):
        for record in self:
            for rec in record.other_lines:
                if rec.service_type_id and rec.service_type_id.resource_service_ids and rec.resource:
                    for line in rec.service_type_id.resource_service_ids:
                        if rec.service_type_id == line.service_type_id and rec.resource == line.resource:
                            rec.ctc = line.ctc


    @api.onchange('costing_template_id')
    def template_map(self):
        if self.costing_template_id:
            self.line_ids = False
            lines = []
            for rec in self.costing_template_id.template_ids:
                # self.env['sale.cost.line'].create({
                lines.append((0,0, {
                    'epo_type_id': rec.temp_epo_id.id,
                    # 'costing_id': self._origin.id,
                    'service_type_id': rec.temp_service_type_id.id,
                    'cost': rec.temp_epo_id.amount
                }))
            self.line_ids = lines

    @api.depends('upload_file')
    def action_generate_epo(self):
        sale_cost_line = ''
        if not self.upload_file:
            raise ValidationError('The uploaded file is empty. Please upload a valid file.')
        if self.upload_file:
            upload_file = base64.b64decode(self.upload_file)
            try:
                wb = xlrd.open_workbook(file_contents=upload_file)
            except xlrd.biffh.XLRDError:
                raise UserError(
                    _('The uploaded file is not a valid Excel file. Please upload a valid .xls or .xlsx file.'))
            self.line_ids.unlink()
            for sheet_index in range(wb.nsheets):
                sheet = wb.sheet_by_index(sheet_index)
                sheet_name = sheet.name
                for row in range(1, sheet.nrows):
                    row_values = sheet.row_values(row)
                    if row_values[2] >= 1:
                        costing_upload_file = self.env['epo.type'].search([('name', '=', str(row_values[1]))], limit=1)
                        if not costing_upload_file:
                            raise UserError(
                                _('"%s" is not in the Application type list in sheet "%s".' % (row_values[1], sheet_name)))
                        sale_cost_line = self.env['sale.cost.line'].create({
                            'costing_id': self.id,
                            'epo_type_id': costing_upload_file.id,
                            'epo_type_qty': row_values[2],
                        })
        if sale_cost_line:
            values = self._get_data_sale_cost_approval_rule_ids()
            if values:
                for v in values:
                    v.update({'state': 'draft'})
                    self.env['sale.cost.approval.rules'].create(v)
        # self.is_generate_epo = True


    @api.depends('other_lines', 'line_ids')
    def _compute_total_sale_cost(self):
        for rec in self:
            total1 = 0
            total2 = 0
            for line in rec.line_ids:
                total1 += line.last_total_price
            for line1 in rec.other_lines:
                total2 += line1.customer_price
            rec.total_sale_cost = total1 + total2

    def _compute_crm_lead(self):
        for rec in self:
            rec.sale_lead_count = self.env['crm.lead'].search_count([('id', '=', self.opportunity_id.id)])


    def action_view_lead(self):
        self.ensure_one()
        sale_lead = self.env['crm.lead'].search([('id', '=', self.opportunity_id.id)])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "crm.lead",
            "domain": [['id', 'in', sale_lead.ids]],
            "name": "crm lead",
            'view_mode': 'tree,form',
        }
        if len(sale_lead) == 1:
            result['view_mode'] = 'form'
            result['res_id'] = sale_lead.id
        return result

        # # action = self.env.ref('sale_costing.action_sale_costing_count').read()[0]
        # costing_ids = self.env['sale.costing'].search([('opportunity_id', '=', self.id)])
        # if len(costing_ids) > 1:
        #     costing_ids['domain'] = [('opportunity_id', '=', self.id)]
        # else:
        #     costing_ids['views'] = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
        #     # costing_ids['res_id'] = costing_ids.id
        # return costing_ids

    def _compute_sale_quotation(self):
        for rec in self:
            rec.sale_order_count = self.env['sale.order'].search_count([
                ('sale_costing_id', '=', rec.id)
            ])


    @api.depends('other_lines', 'opportunity_id', 'line_ids')
    def compute_summary(self):
        for rec in self:
            ol_total_cost = 0
            ol_customer_price = 0
            ol_margin = 0
            ol_margin_p = 0
            if rec.other_lines:
                for line in rec.other_lines:
                    ol_total_cost += line.res_total_cost
                    ol_customer_price += line.customer_price
                ol_margin = ol_customer_price - ol_total_cost
                if ol_margin > 0:
                    percentage = (ol_margin / ol_customer_price) * 100
                    ol_margin_p = f"{percentage:.2f}%"
            li_total_cost = 0
            li_customer_price = 0
            li_margin = 0
            li_margin_p = 0
            if rec.line_ids:
                for line in rec.line_ids:
                    li_total_cost += line.total_cost
                    li_customer_price += line.last_total_price
                li_margin = li_customer_price - li_total_cost
                if li_margin > 0 :
                    percentage = (li_margin / li_customer_price) * 100
                    li_margin_p = f"{percentage:.2f}%"
            if not rec.old_revision_ids:
                if rec.line_ids:
                    rec.old_revision_ids.create({
                        'description': "EPO",
                        'total_cost_summary': li_total_cost,
                        'total_price_summary': li_customer_price,
                        'margin_summary': li_margin,
                        'margin_percentage_summary': li_margin_p,
                        'current_revision_id': rec.id
                    })
                if rec.other_lines:
                    rec.old_revision_ids.create({
                        'description': "Resources",
                        'total_cost_summary': ol_total_cost,
                        'total_price_summary': ol_customer_price,
                        'margin_summary': ol_margin,
                        'margin_percentage_summary': ol_margin_p,
                        'current_revision_id': rec.id
                    })
            if rec.old_revision_ids:
                if rec.line_ids:
                    for line in rec.old_revision_ids:
                        if line.description == "EPO":
                            line.write({
                                'total_cost_summary': li_total_cost,
                                'total_price_summary': li_customer_price,
                                'margin_summary': li_margin,
                                'margin_percentage_summary': li_margin_p
                            })
                        if line.description == "Resources":
                            line.write({
                                'total_cost_summary': ol_total_cost,
                                'total_price_summary': ol_customer_price,
                                'margin_summary': ol_margin,
                                'margin_percentage_summary': ol_margin_p
                            })




    def action_cancel(self):
        view_id = self.env.ref('sale_costing.view_cost_cancel_request_form').id,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancellation Reason'),
            'res_model': 'cost.cancel.request',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
        }

    def action_confirm(self):
        self.write({'state': 'confirm'})

    @api.model
    def create(self, vals):
        if 'unrevisioned_name' not in vals:
            if vals.get('name', 'New') == 'New':
                seq = self.env['ir.sequence']
                vals['name'] = seq.next_by_code('sale.costing') or '/'
            vals['unrevisioned_name'] = vals['name']
        return super(SaleCosting, self).create(vals)

    def action_revision(self):
        self.ensure_one()
        sale_id = self.env['sale.order.line'].search([('sale_costing_id', '=', self.id), ('state', 'in', ('done', 'sale'))])
        if sale_id:
            raise UserError(_("You cannot create the revision. Sale order already has been done for this costing!"))
        view_id = self.env.ref('sale_costing.sale_costing_form').id
        # view_id = view_ref and view_ref[1] or False,
        old_costing_id = self.with_context(sale_revision_history=True).copy()
        self.write({
            'state': 'draft',
            'revised_date': fields.Date.today(),
            'revised_user_id': self.env.user.id,
            'parent_id': old_costing_id.id
        })
        sale_order = self.env['sale.order'].search([('sale_costing_id', '=', self.id), ('state', '!=', 'cancel')], limit=1)
        if sale_order.state in ['sale', 'done']:
            raise ValidationError('You cannot revise the costing as Sale Order is already confirmed')
        sale_order.state = 'cancel'
        self.is_create_quotation = False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Costing'),
            'res_model': 'sale.costing',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

    @api.returns('self', lambda value: value.id)
    def copy(self, defaults=None):
        if not defaults:
            defaults = {}
        if not self.unrevisioned_name:
            self.unrevisioned_name = self.name
        if self.env.context.get('sale_revision_history'):
            prev_name = self.name
            revno = self.revision_number
            self.write({'revision_number': revno + 1, 'name': '%s-%02d' % (self.unrevisioned_name, revno + 1)})
            defaults.update({'name': prev_name, 'revision_number': revno, 'active': True, 'state': 'cancel',
                             'current_revision_id': self.id, 'unrevisioned_name': self.unrevisioned_name, })
        return super(SaleCosting, self).copy(defaults)

    def action_sale_costing_count(self):
        self.ensure_one()
        sale_order = self.env['sale.order'].search([
            ('sale_costing_id', '=', self.id)
        ])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "domain": [('id', 'in', sale_order.ids)],
            "name": "Sale Orders",
            "view_mode": "tree,form",
        }
        if len(sale_order) == 1:
            result['view_mode'] = 'form'
            result['res_id'] = sale_order.id  # Use a single ID
        return result


    # def action_view_sale(self):
    #     action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
    #     line_ids = self.env['sale.order.line'].search([('sale_costing_id', '=', self.id)])
    #     order_ids = line_ids.mapped('order_id')
    #     if len(order_ids) > 1:
    #         action['domain'] = [('id', 'in', order_ids.ids)]
    #     else:
    #         action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
    #         action['res_id'] = order_ids.id
    #     return action


    # @api.onchange('to_currency_id')
    # def get_currency_rate(self):
    #     if self.to_currency_id:
    #         self.update({'conversion_rate': self.to_currency_id.rate})

    @api.onchange('margin_percentage')
    def onchange_margin(self):
        for line in self.line_ids:
            line.update({'margin_percentage': self.margin_percentage})

    # @api.onchange('other_cost_template_id')
    # def onchange_template_id(self):
    #     if not self.other_cost_template_id:
    #         return
    #     vals = []
    #     for line in self.other_cost_template_id.charge_ids:
    #         vals.append((0, 0, {'name': line.id, 'type': line.type, 'amount': line.amount}))
    #     self.update({'other_lines': vals})

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'sale.costing', sequence_date=seq_date) or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.costing', sequence_date=seq_date) or _('New')
        return super(SaleCosting, self).create(vals)

    def action_create_quotation(self):
        epo_count = sum(self.line_ids.mapped('epo_type_qty')) if self.line_ids else 0
        resource_count = len(self.other_lines.mapped('resource_qty')) if self.other_lines else 0
        view_id = self.env.ref('sale.view_order_form').id
        sale_id = self.env['sale.order'].create({
            'sale_costing_id': self.id,
            'partner_id': self.partner_id.id,
            'sale_type_id': self.sale_type_id.id,
            'sale_sub_type_id': self.sale_sub_type_id.id,
            'epo_count': epo_count,
            'resource_count': resource_count,
            'is_costing_order_line': True,
        })
        for service in self.line_ids.mapped('service_type_id'):
            price_unit = 0
            if self.line_ids:
                price_unit += sum(self.line_ids.filtered(lambda x: x.service_type_id.id == service.id).mapped('last_total_price'))
            if self.other_lines:
                price_unit += sum(self.other_lines.filtered(lambda x: x.service_type_id.id == service.id).mapped('customer_price'))
            order_line = self.env['sale.order.line'].create({
                    'order_id': sale_id.id,
                    'product_id': service.product_id.id,
                    'name': service.product_id.name,
                    'product_uom': service.product_id.uom_id.id,
                    'price_unit': price_unit,
                    'tax_id': False,
                })

        if self.opportunity_id:
            sale_id.write({'opportunity_id': self.opportunity_id.id})

        self.is_create_quotation = True
        # is_proposal_submitted_stage = self.env['crm.stage'].search([('is_proposal_submitted', '=', True)], limit=1)
        # if is_proposal_submitted_stage:
        #     self.opportunity_id.stage_id = is_proposal_submitted_stage.id
        # for rec in self.line_ids:
        #     rims_total = 0
        #     db_total = 0
        #     rec.filtered(lambda r: r.service_type_id == 'RIMS')
        #     print('\n------------', self.line_ids, '-------line--------')
        #     if rec.service_type_id and rec.service_type_id == 'RIMS':
        #         rims_total = rec.last_total_price
        #     print('\n------------', rims_total, '-------rims_total--------')
        #     if rec.service_type_id and rec.service_type_id == 'DB':
        #         db_total += rec.last_total_price
        #     print('\n------------', db_total, '-------db_total--------')
        # rims_product = ''
        # if self.line_ids:
        #     for rec in self.line_ids:
        #         if rec.service_type_id:
        #             if rec.service_type_id.code and rec.service_type_id.code == 'RIMS':
        #                 rims_product = rec.service_type_id.product_id
        # if rims_product and rims_product.default_code:
        #     description = rims_product.default_code + rims_product.name
        # else:
        #     description = rims_product.name
        # if rims_product:
        #     order_line = self.env['sale.order.line'].create({
        #         'order_id': sale_id.id,
        #         'product_id': rims_product.id,
        #         'name': description,
        #         'product_uom': rims_product.uom_id.id,
        #         'price_unit': rims_total,
        #         'tax_id': False
        #     })
        #
        # db_product = ''
        # if self.line_ids:
        #     for rec in self.line_ids:
        #         if rec.service_type_id:
        #             if rec.service_type_id.code and rec.service_type_id.code == 'DB':
        #                 db_product = rec.service_type_id.product_id
        # if db_product and db_product.default_code:
        #     description = db_product.default_code + db_product.name
        # elif db_product and db_product.name:
        #     description = db_product.name
        # if db_product:
        #     order_line = self.env['sale.order.line'].create({
        #         'order_id': sale_id.id,
        #         'product_id': db_product.id,
        #         'name': description,
        #         'product_uom': db_product.uom_id.id,
        #         'price_unit': db_total,
        #         'tax_id': False
        #     })

        no = 1
        for rec in self.line_ids:
            epo_costing_id = self.env['sale.order.line.epo'].create({
                'sale_order_id': sale_id.id,
                's_no': no,
                'sale_epo_id': rec.epo_type_id.id,
                'sale_service_type_id': rec.service_type_id.id,
                'sale_epo_qty': rec.epo_type_qty,
            })
            no += 1
        no = 1
        for rec in self.other_lines:
            resource_costing_id = self.env['sale.order.line.resource'].create({
                'sale_order_id': sale_id.id,
                's_no': no,
                'sale_resource': rec.resource,
                'sale_resource_qty': rec.resource_qty,
            })
            no = no+1
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': sale_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

    def action_sale_revision(self):
        sale_order = self.env['sale.order'].search([
            ('sale_costing_id', '=', self.id), ('state', '!=', 'cancel')
        ], limit=1)
        sale_order.state = 'cancel'
        epo_count = len(self.line_ids) if self.line_ids else 0
        resource_count = len(self.other_lines) if self.other_lines else 0
        view_id = self.env.ref('sale.view_order_form').id
        sale_id = self.env['sale.order'].create({
            'sale_costing_id': self.id,
            'partner_id': self.partner_id.id,
            'sale_type_id': self.sale_type_id.id,
            'sale_sub_type_id': self.sale_sub_type_id.id,
            'epo_count': epo_count,
            'resource_count': resource_count,
        })
        for service in self.line_ids.mapped('service_type_id'):
            price_unit = 0
            if self.line_ids:
                price_unit += sum(self.line_ids.filtered(lambda x: x.service_type_id.id == service.id).mapped('last_total_price'))
            if self.other_lines:
                price_unit += sum(self.other_lines.filtered(lambda x: x.service_type_id.id == service.id).mapped('customer_price'))
            order_line = self.env['sale.order.line'].create({
                    'order_id': sale_id.id,
                    'product_id': service.product_id.id,
                    'name': service.product_id.name,
                    'product_uom': service.product_id.uom_id.id,
                    'price_unit': price_unit,
                    'tax_id': False
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': sale_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

    def action_create_sale_quotes(self):
        # if len(self.mapped('pricelist_id').mapped('currency_id')) > 1:
        #     raise UserError(_("Please select same selling currency in all costing."))
        for rec in self:
            if rec.state != 'confirm':
                raise UserError(_("Please confirm all the costing sheet to create quotations."))
        view_id = self.env.ref('sale.view_order_form').id
        sale_id = self.env['sale.order'].create({
            'sale_costing_id': self[0].id,
            'partner_id': self[0].partner_id.id,
            # 'sale_type_id': self.sale_type_id.id
            # 'tender_id': self[0].opportunity_id.id,
            # 'enquiry_id': self[0].opportunity_id.oppor_id.id,
            # 'currency_id': self[0].to_currency_id.id,
            # 'pricelist_id': self[0].pricelist_id.id,
            # 'po_number': self[0].opportunity_id.oppor_id.po_number or False,
            # 'po_date': self[0].opportunity_id.oppor_id.po_date or False,
        })
        for rec in self:
            for line in rec.line_ids.filtered(lambda x: not x.parent_id):
                order_line = self.env['sale.order.line'].create({
                    'order_id': sale_id.id,
                    'product_id': line.epo_type_id.id,
                    'name': line.epo_type_id.name,
                    'product_uom_qty': line.epo_type_qty,
                    # 'product_uom': line.product_uom.id,
                    'sale_costing_id': line.costing_id.id,
                    # 'price_unit': line.unit_sale_price,
                })
                parent_ids = self.env['sale.cost.line'].search([('parent_id', '=', line.id)])
                for parent in parent_ids:
                    self.env['sale.order.option'].create({
                        'sale_order_line_id': order_line.id,
                        'order_id': sale_id.id,
                        'product_id': parent.epo_type_id.id,
                        'name': parent.epo_type_id.name,
                        'quantity': parent.epo_type_qty,
                        'uom_id': parent.product_uom.id,
                        # 'price_unit': parent.unit_sale_price,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': sale_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }


class SaleCostLine(models.Model):
    _name = 'sale.cost.line'
    _description = 'Sale Costing Line'
    #
    # @api.depends('product_uom_qty', 'price_unit', 'margin_percentage', 'costing_id.finance_percentage')
    # def _compute_amount(self):
    #     for line in self:
    #         price = line.price_unit * line.product_uom_qty
    #         margin_total = price * (line.margin_percentage / 100.0)
    #         finance_total = price * (line.costing_id.finance_percentage / 100.0)
    #         line.update({
    #             'price_subtotal': price,
    #             'margin_total': margin_total,
    #             'finance_total': finance_total,
    #             'price_total': price + margin_total + finance_total,
    #         })

    # @api.depends('price_subtotal', 'price_total', 'costing_id.other_lines.price_total', 'costing_id.conversion_rate',
    #              'costing_id.to_currency_id')
    # # def get_selling_price(self):
    #     for line in self:
    #         other_charges = 0
    #         percentage = (line.price_total/sum(line.costing_id.line_ids.filtered(lambda x: x.price_total > 0).mapped('price_total')))*100 if line.price_total > 0 else 0
    #         other_charges += sum(line.costing_id.other_lines.mapped('price_total')) * (percentage/100)
    #         # for charge in line.costing_id.other_lines.mapped('price_total'):
    #         #     price = charge.price_total * (percentage / 100) if percentage > 0 else 0
    #         #     other_charges += price
    #         line.amount_other_charge = other_charges
    #         line.amount_charge_selling = other_charges * line.costing_id.conversion_rate
    #         line.base_sale_price = line.price_total + other_charges
    #         # line.sale_price = line.base_sale_price * line.costing_id.conversion_rate
    #         line.unit_sale_price = ((line.base_sale_price * line.costing_id.conversion_rate) / (line.product_uom_qty or 1))

    def _get_domain(self):
        for rec in self:
            return [('id', 'in', rec.costing_id.line_ids.ids),('id', '!=', rec.id)]

    costing_id = fields.Many2one('sale.costing', string='Costing Reference', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='costing_id.company_id', string='Company', store=True, readonly=True, index=True)
    # product_id = fields.Many2one('product.product', string='Product',
    #                              domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    #                              ondelete='restrict', check_company=True)
    # product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    # product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    # product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    # price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    currency_id = fields.Many2one(related='costing_id.currency_id', store=True, string='Currency')

    # margin_percentage = fields.Float("Margin(%)")
    state = fields.Selection(STATES, related='costing_id.state', string='Status', readonly=True, copy=False, store=True, default='draft')
    # Currency and Conversion
    # to_currency_id = fields.Many2one("res.currency", related='costing_id.to_currency_id', string="Selling Currency")
    # conversion_rate = fields.Float("Conversion Rate", related='costing_id.conversion_rate')
    # amount_other_charge = fields.Monetary(compute='get_selling_price', string='Other Charges', store=True)
    # amount_charge_selling = fields.Monetary(compute='get_selling_price', string='Other Charges', store=True)
    # base_sale_price = fields.Monetary(compute='get_selling_price', string='Base Sale Price', store=True)
    # sale_price = fields.Monetary(compute='compute_sale_price', string='Sale Price', store=True)
    # unit_sale_price = fields.Monetary(compute='get_selling_price', string='Sale Price/Unit', store=True)
    # parent_id = fields.Many2one('sale.cost.line', string='Optional For', domain=_get_domain, ondelete='cascade', index=True)
    # price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal Price', readonly=True, store=True)
    # price_total = fields.Monetary(compute='_compute_amount', string='Total Price', readonly=True, store=True)
    # margin_total = fields.Monetary(compute='_compute_amount', string='Margin Total', readonly=True, store=True)
    # finance_total = fields.Monetary(compute='_compute_amount', string='Finance Total', readonly=True, store=True)
    sequence_no = fields.Char(string='SN', compute='_compute_sequence_no')
    epo_type_id = fields.Many2one('epo.type', string="EPO", ondelete='restrict')
    service_type_id = fields.Many2one(related='epo_type_id.service_type_id', string="Service Type")
    epo_type_qty = fields.Float(string='Qty')
    cost = fields.Float(string='Cost EPO Month', related='epo_type_id.amount')
    price = fields.Float(string='Price EPO Month', compute='compute_function')
    total_cost = fields.Float(string='Total Cost', compute='compute_function', readonly=True)
    total_price = fields.Float(string='Total Price', compute='compute_function', readonly=True)
    discount = fields.Float(string='Discount%')
    last_total_price = fields.Float(string='Total price to customer', compute='compute_function', readonly=True)
    margin = fields.Float(string='Margin%', compute='compute_function', readonly=True)
    margin_amount = fields.Float(string='Margin Amount', compute='compute_function', readonly=True)
    overhead_percentage = fields.Float(related='costing_id.overhead_percentage')
    markup_percentage = fields.Float(related='costing_id.markup_percentage')


    @api.depends('overhead_percentage','markup_percentage','epo_type_qty','cost','price','total_cost','total_price','discount','last_total_price','margin','margin_amount')
    def compute_function(self):
        for line in self:
            line.margin = 0
            line.price = line.cost + (line.cost * line.markup_percentage)
            line.total_cost = line.epo_type_qty * line.cost
            line.total_price = line.epo_type_qty * line.price
            if line.discount > 0:
                line.last_total_price = line.total_price - line.total_price * line.discount
            else:
                line.last_total_price = line.total_price
            if (line.total_price - line.total_cost) > 0:
                line.margin = (line.total_price - line.total_cost) / line.total_price
            line.margin_amount = line.last_total_price - line.total_cost


    # @api.depends('unit_sale_price', 'product_uom_qty')
    # def compute_sale_price(self):
    #     for line in self:
    #         line.sale_price = round(line.base_sale_price * line.costing_id.conversion_rate, 2)
    #
    @api.depends('costing_id.line_ids')
    def _compute_sequence_no(self):
        for line in self:
            no = 0
            line.sequence_no = no
            for l in line.costing_id.line_ids:
                no += 1
                l.sequence_no = no
    #
    # @api.onchange('product_id')
    # def product_id_change(self):
    #     if not self.product_id:
    #         return
    #     vals = {}
    #     if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
    #         vals['product_uom'] = self.product_id.uom_id
    #         vals['product_uom_qty'] = self.product_uom_qty or 1.0
    #     self.update(vals)
    #
    # @api.depends('product_id', 'costing_id')
    # def name_get(self):
    #     result = []
    #     for line in self:
    #         name = line.costing_id.name or ''
    #         if line.product_id:
    #             name += " - (%s)" % line.product_id.display_name
    #         result.append((line.id, name))
    #     return result


class OtherCostLine(models.Model):
    _name = 'other.cost.line'
    _description = 'Sale Costing Other Lines'

    # @api.depends('type', 'amount', 'costing_id.line_ids.price_total', 'include_margin', 'include_finance', 'costing_id.finance_percentage')
    # def _compute_amount(self):
    #     for line in self:
    #         price = 0.0
    #         margin_cost = 0
    #         if line.type == 'fixed':
    #             # if line.include_margin:
    #             #     price += (line.amount + (line.amount * (line.costing_id.margin_percentage / 100)))
    #             # else:
    #                 price += line.amount
    #         else:
    #             # if line.include_margin:
    #             #     tot = sum(line.costing_id.line_ids.mapped('price_subtotal'))
    #             #     base_price_tot = tot+(tot*(line.costing_id.margin_percentage/100))
    #             # else:
    #             base_price_tot = sum(line.costing_id.line_ids.mapped('price_subtotal'))
    #             price += base_price_tot * (line.amount / 100.0)
    #
    #         if line.include_margin and line.costing_id.margin_percentage:
    #             margin_cost += (line.amount * (line.costing_id.margin_percentage / 100))
    #         line.update({
    #             'price_total': (price + margin_cost),
    #             'margin_total': margin_cost,
    #             'selling_price_total': (price + margin_cost) * line.costing_id.conversion_rate,
    #         })

    costing_id = fields.Many2one('sale.costing', string='Costing Reference', required=True, ondelete='cascade',
                                 index=True)
    name = fields.Many2one('other.salecost', string="Name")
    type = fields.Selection([('fixed', 'Amount'), ('percentage', 'Percentage')], string="Amount in",
                            default='fixed')
    amount = fields.Float("Value", default=1.0)
    currency_id = fields.Many2one(related='costing_id.currency_id', depends=['costing_id'], store=True,
                                  string='Currency',
                                  readonly=True)
    # to_currency_id = fields.Many2one(related='costing_id.to_currency_id')
    state = fields.Selection(STATES, related='costing_id.state', string='Status', readonly=True, copy=False, store=True,
                             default='draft')
    include_margin = fields.Boolean("Apply Margin", default=True)
    include_finance = fields.Boolean("Apply Finance", default=True)
    cost_type = fields.Selection([('work', 'EX-Work'), ('landed', 'Landed'), ('other', 'Other')], string="Cost Type",
                                 related='name.cost_type', store=True)
    show_in_report = fields.Boolean()
    # price_total = fields.Monetary(compute='_compute_amount', string='Base Price', readonly=True, store=True)
    selling_price_total = fields.Monetary(string='Selling Price', readonly=True, store=True)
    # margin_total = fields.Monetary(compute='_compute_amount', string='Margin Total', readonly=True, store=True)
    # finance_total = fields.Monetary(compute='_compute_amount', string='Finance Total', readonly=True, store=True)
    sequence_no = fields.Char(string='SN', compute='_compute_sequence_no')
    company_currency = fields.Many2one('res.currency', 'Company Currency', related="costing_id.company_id.currency_id")
    amount_in_company_currency = fields.Monetary("Amount in Company Currency", store=True)
    price_total = fields.Monetary(string='Total Price', readonly=True, store=True)
    margin_total = fields.Monetary(string='Margin Total Price', readonly=True, store=True)

    resource = fields.Selection([
        ('l1', 'L1'),
        ('l2', 'L2'),
        ('l3', 'L3')
    ], string='Resource')
    service_type_id = fields.Many2one('crm.service', string='Service type')
    resource_qty = fields.Integer(string='Qty', default=1.0)
    ctc = fields.Float(string='CTC')
    crm = fields.Float(string='Cost/Resource/Month', compute='compute_resource')
    prm = fields.Float(string='Price/Resource/Month', compute='compute_resource')
    res_total_cost = fields.Monetary(string='Total Cost', compute='compute_resource', store=True)
    res_total_price = fields.Monetary(string='Total Price', compute='compute_resource', store=True)
    res_discount = fields.Float(string='Discount')
    customer_price = fields.Monetary(string='Total price to Customer', compute='compute_resource', store=True)
    res_margin = fields.Float(string='Margin', compute='compute_resource')
    res_margin_amount = fields.Monetary(string='Margin Amount', compute='compute_resource')
    overhead_percentage = fields.Float(related='costing_id.overhead_percentage')
    markup_percentage = fields.Float(related='costing_id.markup_percentage')

    @api.depends('ctc', 'crm', 'prm', 'res_total_cost','res_total_price','customer_price','res_margin','res_margin_amount','res_discount')
    def compute_resource(self):
        for line in self:
            line.res_margin = 0
            line.customer_price = 0
            line.crm = line.ctc + (line.ctc * line.overhead_percentage)
            line.prm = line.crm + (line.crm * line.markup_percentage)
            line.res_total_cost = line.crm * line.resource_qty
            line.res_total_price = round(line.prm * line.resource_qty,0)
            line.customer_price = line.res_total_price - line.res_total_price * line.res_discount
            if line.res_total_cost > 0:
                line.res_margin = (line.customer_price - line.res_total_cost) / line.customer_price
            line.res_margin_amount = line.customer_price - line.res_total_cost


            # if rec.costing_id.other_lines.resource == rec.costing_id.other_lines.service_type_id.resource_serivce_ids.resource and rec.costing_id.other_lines.service_type_id == rec.costing_id.other_lines.service_type_id.resource_serivce_ids.service_type_id:
            #     line_ctc = self.env['crm.service'].search([('rec.s', '=', line.id)])
            #     self.env['other.cost.line'].create({
            #         'costing_id': self.id,
            #         'ctc': line_ctc,
            #     })



    # @api.depends('selling_price_total')
    # def _currency_conversion(self):
    #     for rec in self:
    #         rec.amount_in_company_currency = rec.costing_id.pricelist_id.currency_id.with_context(date=rec.costing_id.date).compute(rec.selling_price_total, rec.company_currency)

    @api.depends('costing_id.other_lines')
    def _compute_sequence_no(self):
        for line in self:
            no = 0
            line.sequence_no = no
            for l in line.costing_id.other_lines:
                no += 1
                l.sequence_no = no

    # @api.onchange('name')
    # def product_id_change(self):
    #     if not self.name:
    #         return
    #     self.update({'type': self.name.type, 'amount': self.name.amount})


class SummerySaleCosting(models.Model):
    _name = "sale.costing.summery"

    description = fields.Char('Description')
    total_cost_summary = fields.Float('Total cost')
    total_price_summary = fields.Float('Total price')
    margin_summary = fields.Float('Margin')
    margin_percentage_summary = fields.Char('Margin%')
    current_revision_id = fields.Many2one('sale.costing', 'Current revision', readonly=True, copy=True)

class CostingTemplate(models.Model):
    _name = "costing.template"

    name = fields.Char("Name")
    template_ids = fields.One2many('sale.costing.template', 'template_id', string="Template")


class SaleCostingTemplate(models.Model):
    _name = "sale.costing.template"

    s_no = fields.Char(string="S.NO", compute="_compute_s_no")
    temp_epo_id = fields.Many2one('epo.type', string="Epo")
    temp_service_type_id = fields.Many2one('crm.service', string="Service Type")
    template_id = fields.Many2one('costing.template')

    @api.depends('template_id.template_ids')
    def _compute_s_no(self):
        for record in self:
            if record.id and record.template_id:
                record.s_no = str(record.template_id.template_ids.ids.index(record.id) + 1)
            else:
                record.s_no = False

class EpoType(models.Model):
    _inherit = 'epo.type'

    amount = fields.Float(string='Amount')
    service_type_id = fields.Many2one('crm.service', string='Service type')

