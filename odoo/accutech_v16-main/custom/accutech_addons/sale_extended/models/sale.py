from typing import List, Union, Tuple
import html
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError



class SaleOrderExtended(models.Model):
    _inherit = 'sale.order'

    sale_order_line = fields.One2many('sale.order.line', 'order_id', string='Product Line', copy=True)
    customer_code = fields.Char(string="Customer Code")
    opportunity_id = fields.Many2one(
        comodel_name="crm.lead",
        string="Opportunity",
    )

    opportunity_no1 = fields.Char(
        string="Opportunity No",
        # related="opportunity_id.opportunity_no",
        readonly=True,
        store=True,
    )
    shipment_mode = fields.Many2one('shipment.mode', string='Shipment Mode')
    shipping_location = fields.Many2one('stock.quant', string="Shipping Location")
    rfq_count_custom = fields.Integer(compute='_compute_rfq_data', string="Purchase Orders")
    order_id = fields.Many2one('purchase.order', 'Purchase')
    # is_sale_approval = fields.Boolean(compute='_compute_sale_approval')
    send_approval_pricing = fields.Boolean(copy=False)
    confirm_button = fields.Boolean(copy=False)
    is_manager_approved = fields.Boolean(copy=False)
    po_type = fields.Selection(
        selection=[
            ('direct_po', 'Direct PO'),
            ('sale_po', 'Sale PO'),
        ],
        string='PO Type'
    )
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('sent', "Quotation Sent"),
            ('revision', 'Revision'),
            ('sale', "Sales Order"),
            ('done', "Locked"),
            ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    purchase_count = fields.Integer(compute='_compute_purchase_data', string="Purchase Orders")
    picking_status = fields.Selection(
        selection=[
            ('need_to_download', 'Need to Download'),
            ('downloaded', 'Downloaded')
        ],
        string="Picking Status",
        related='picking_ids.picking_status',
        store=True
    )
    remarks = fields.Char("Remarks")
    main_discount = fields.Float(string='Disc.', digits='Discount', default=0.000)
    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    manager_comments = fields.Html(
        # related='opportunity_id.manager_comments',
        readonly=False,  # Allows editing if needed
        copy=False
    )
    description = fields.Html(
        # related='opportunity_id.description',
        readonly=False,
        copy=False
    )
    website = fields.Char(string="Website")
    contact_person_id = fields.Many2one('res.partner',string="Contact Person")

    fixed_discount = fields.Float(string="Fixed Disc.", digits="Product Price", default=0.000)

    discount = fields.Float(string='% Disc.', digits='Discount', default=0.000)

    technical_issues_id = fields.Many2one('res.partner',string="Technical Issues")
    order_process_id = fields.Many2one('res.partner',string="Order Processing & Logistics")
    commercial_issue_id = fields.Many2one('res.partner',string="Commercial Issues")
    delivery_id = fields.Many2one('res.partner',string="Delivery")

    customer_po_no = fields.Char(string="Customer PO No")
    customer_po_date = fields.Date(string="Customer PO Date")

    quotation_name = fields.Char(string='Quotation Reference', required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _('New'))

    @api.onchange("discount")
    def _onchange_discount(self):
        for line in self:
            if line.discount != 0:
                self.fixed_discount = 0.0
                fixed_discount = (line.price_unit * line.product_qty) * (line.discount / 100.0)
                line.update({"fixed_discount": fixed_discount})
            if line.discount == 0:
                fixed_discount = 0.000
                line.update({"fixed_discount": fixed_discount})
            line._compute_amount()

    @api.onchange("fixed_discount")
    def _onchange_fixed_discount(self):
        for line in self:
            if line.fixed_discount != 0:
                self.discount = 0.0
                discount = ((self.product_qty * self.price_unit) - (
                            (self.product_qty * self.price_unit) - self.fixed_discount)) / (
                                       self.product_qty * self.price_unit) * 100 or 0.0
                line.update({"discount": discount})
            if line.fixed_discount == 0:
                discount = 0.0
                line.update({"discount": discount})
            line._compute_amount()


    def update_discount(self):
        for order in self:
            products_with_discount = self.env['product.product'].search([('is_default', '=', True)])
            if not any(order.order_line.mapped('product_id').mapped('is_default')):
                for product in products_with_discount:
                    values = {
                        'product_id': product.id,
                        'name': product.name,
                        'product_uom_qty': 1,
                        'price_unit': product.lst_price,
                        'discount': False,
                        'tax_id': False,
                    }
                    order.write({'order_line': [(0, 0, values)]})
            total_subtotal = sum(line.price_subtotal for line in order.order_line if not line.product_id.is_default)

            for line in order.order_line:
                if line.product_id.is_default:
                    discount_amount = total_subtotal * (order.main_discount / 100)
                    if total_subtotal > 0:
                        line.price_unit = -(discount_amount)
                    else:
                        line.price_unit = 0
                        line.price_subtotal = 0
            order.order_line._compute_amount()



    # @api.depends('is_sale_approval', 'order_line', 'order_line.product_uom_qty')
    # def _compute_sale_approval(self):
    #     for rec in self:
    #         rec.is_sale_approval = False
    #         po_quantities = sum(rec.order_id.order_line.mapped('product_qty'))
    #         sale_quantities = sum(rec.order_line.mapped('product_uom_qty'))
    #         if rec.po_type == 'sale_po':
    #             if po_quantities > sale_quantities:
    #                 rec.write({'is_sale_approval': True})
    #         else:
    #             rec.write({'is_sale_approval': False})
    
    def action_confirm(self):
        res = super(SaleOrderExtended, self).action_confirm()
        stock_manager = ''
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('sale_extended.group_stock_retriever_manager'):
                stock_manager += user.login
                stock_manager += ', '
        if stock_manager:
            subject = 'SO - %s confirmed' % self.name
            body = """<p>Hello,</p>
                                  <br/>
                                  <p>Quotation - %s has been confirmed as Sale Order-%s. Please proceed further.</p>
                                  <center>
                                      <p style="font-size: 15px;">
                                        <i>THIS IS AN AUTOMATICALLY GENERATED NOTIFICATION EMAIL</i>
                                      </p>
                                  </center>
                                   """ % (self.partner_id.name, self.name)
            message_body = body
            from_email = self.env.user.login
            template_data = {
                'subject': subject,
                'body_html': message_body,
                'email_from': from_email,
                'email_to': stock_manager,
            }
            template_id = self.env['mail.mail'].sudo().create(template_data)
            template_id.sudo().send()
            return res


    #
    # def _action_confirm(self):
    #     for order in self:
    #         if any(expense_policy not in [False, 'no'] for expense_policy in
    #                order.order_line.product_id.mapped('expense_policy')):
    #             if not order.analytic_account_id:
    #                 order._create_analytic_account()
    #
    # def action_create_delivery_order(self):
    #     self.order_line._action_launch_stock_rule()


    def _compute_rfq_data(self):
        for lead in self:
            lead.rfq_count_custom = self.env['purchase.order'].search_count([('sale_id', '=', self.id)])

    def action_view_rfq(self):
        action = self.env.ref('purchase.purchase_rfq').sudo().read()[0]
        sale_ids = self.env['purchase.order'].search([('sale_id', '=', self.id)])
        if len(sale_ids) > 1:
            action['domain'] = [('sale_id', '=', self.id)]
        else:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = sale_ids.id
        return action

    def _compute_purchase_data(self):
        for purchase in self:
            purchase.purchase_count = self.env['purchase.order'].search_count([('id', '=', self.order_id.id)])

    def action_view_purchase(self):
        action = self.env.ref('purchase.purchase_rfq').sudo().read()[0]
        purchase_ids = self.env['purchase.order'].search([('id', '=', self.order_id.id)])
        if len(purchase_ids) > 1:
            action['domain'] = [('id', '=', self.order_id.id)]
        else:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchase_ids.id
        return action

    # def action_draft(self):
    #     orders = self.filtered(lambda s: s.state in ['cancel', 'sent'])
    #     orders.write({'state': 'draft',
    #         'signature': False,
    #         'signed_by': False,
    #         'signed_on': False,
    #         'send_approval_pricing': False,
    #         'is_manager_approved': False,
    #         'confirm_button': False,
    #         'send_for_approval': False,
    #         'approve_button': False,})
    #     res = super(SaleOrderExtended, self).action_draft()
    #     return res

    def send_manager_pricing_approval(self):
        self.write({'send_approval_pricing': True})
        if not self.order_line:
            raise ValidationError('Please enter the product lines before sending for manager pricing approval.')
        # mail goes to manager(manager group or salesperson's manager, will decide later) on pricing approval/rejection

    def manager_approve(self):
        self.confirm_button = True
        if self.is_revision == True:
            self.approval_send_button = False
        self.write({'is_manager_approved': True, 'state': 'sent'})
        total_expected_price = sum(rec.price_unit for rec in self.order_line)
        if total_expected_price == 0.0:
            raise UserError('Please enter the unit price in sale order lines to approve the pricing.')
        # mail goes to salesperson on pricing approval

    def manager_reject(self):
        self.write({'send_approval_pricing': False})
        # mail goes to salesperson on pricing rejection
        pass

    def copy(self, default=None):
        default = default or {}
        # Avoid duplicating the sale order lines
        default['order_line'] = False
        return super(SaleOrderExtended, self).copy(default)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    _sql_constraints = [
        ('accountable_required_fields',
         "CHECK(display_type IS NOT NULL OR is_oti IS NOT NULL OR (product_id IS NOT NULL AND product_uom IS NOT NULL))",
         "Missing required fields on accountable sale order line."),
        ('non_accountable_null_fields',
         "CHECK(display_type IS NULL OR (product_id IS NULL AND price_unit = 0 AND product_uom_qty = 0 AND product_uom IS NULL AND customer_lead = 0))",
         "Forbidden values on non-accountable sale order line"),
    ]

    set = fields.Integer(string='Set', default=1)
    is_oti = fields.Boolean('OTI', default=False)
    product_name = fields.Char('One Time Item')
    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=False, precompute=True)
    tax_id = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        default=lambda self: self._get_default_tax()
    )
    parameter_1 = fields.Text(
        string='Parameter 1',
        related='product_template_id.parameter_1',
        readonly=True,
    )
    item_no = fields.Char(
        string="Item Number",
        # related='product_template_id.item_no',
        store=True
    )
    mfr_no = fields.Char(
        string="Mfr No",
        related='product_template_id.mfr_no',
        store=True,
        readonly=True
    )
    configuration_price = fields.Monetary(
        string="Configurator Price",
        related='product_template_id.configuration_price',
        store=True,
        readonly=True,
        currency_field='currency_id'
    )
    delivery_period = fields.Char("Delivery Period")
    header_text = fields.Char("Header Text")
    sac = fields.Char(string="SAC",
                        related='product_template_id.sac',
                        store=True,
                        readonly=True)
    hsn = fields.Char(string="HSN",
                        related='product_template_id.hsn',
                        store=True,
                        readonly=True)
    spec_remarks = fields.Text("SPEC Remarks")
    hs_code = fields.Char("HS Code")
    ic_po = fields.Char("IC-PO")
    # model = fields.Char('Model')
    # make = fields.Char('Make')
    model = fields.Char(string="Model",
                        related='product_template_id.model',
                        readonly=False)
    make = fields.Char(string="Make",
                       related='product_template_id.make',
                       readonly=False)
    country_id = fields.Many2one(
        'res.country',
        related='product_template_id.origin_country_id',
        store=True,
        readonly=True,
        string="Country/Region of Origin",
        help="Select the country associated with this record."
    )

    description_short = fields.Text('Description')

    @api.onchange('product_template_id')
    def _onchange_product_template(self):
        if self.product_template_id:
            self.item_no = self.product_template_id.item_no
        # if self.product_template_id and self.product_template_id.parameter_1:
        #     self.parameter_1 = self.product_template_id.parameter_1
        #     print('\n------------', self.parameter_1, '-------self.parameter_1--------')

    @api.onchange('item_no')
    def _onchange_item_no(self):
        if self.item_no:
            product_template = self.env['product.template'].search([('item_no', '=', self.item_no)], limit=1)
            product_product = self.env['product.product'].search([('item_no', '=', self.item_no)], limit=1)
            if product_template:
                self.product_template_id = product_template.id
                self.product_id = product_product.id
                self.product_uom = product_template.uom_id.id
            else:
                self.product_template_id = False
                self.product_id = False
                self.product_uom = False

    @api.onchange('product_template_id')
    def onchange_description_short(self):
        for line in self:
            if line.product_template_id:
                # Get the raw description from the product template
                description = line.product_template_id.description_short or ''

                # Remove all HTML tags using the html module
                clean_description = html.unescape(description)

                # Optionally, truncate to a maximum length (255 characters in this case)
                line.description_short = clean_description[:255]  # Adjust the length if necessary
            else:
                line.description_short = False

    @api.depends('order_id.state')
    def _compute_is_oti_visible(self):
        for line in self:
            # Hide the is_oti field if the parent sale order is in 'sale' or 'done' state
            if line.order_id.state in ['sale', 'done']:
                line.is_oti = False
            else:
                line.is_oti = True


    def _get_default_tax(self):
        # Get the current active company
        active_company = self.env.company
        print("\n--- Active Company: ", active_company.name, "--\n")
        # Search for a tax in the current active company
        tax = self.env['account.tax'].search([
            ('company_id', '=', active_company.id),
            ('type_tax_use', '=', 'sale')  # Optional: Restrict to sales taxes
        ], limit=1)  # Get the first matching tax
        if tax:
            # Return the tax ID in the correct format for Many2many field
            return [(6, 0, [tax.id])]

        # If no tax is found, return an empty list or handle the fallback logic
        return []

    # _sql_constraints = [
    #     ('accountable_required_fields',
    #      "CHECK(display_type IS NOT NULL OR is_oti NOT NULL OR (product_id IS NOT NULL AND product_uom IS NOT NULL))",
    #      "Missing required fields on accountable sale order line."),
    #     ('non_accountable_null_fields',
    #      "CHECK(display_type IS NULL OR (product_id IS NULL AND price_unit = 0 AND product_uom_qty = 0 AND product_uom IS NULL AND customer_lead = 0))",
    #      "Forbidden values on non-accountable sale order line"),
    # ]



class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string="Product",
        ondelete='cascade', check_company=False,
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.")


class Product(models.Model):
    _inherit = "product.template"

    company_id = fields.Many2one('res.company', default=False)
    stock_keeping_unit = fields.Char('Product ID(SKU)')
    parameter_1 = fields.Text(string='Parameter 1')
    parameter_2 = fields.Text(string='Parameter 2')
    parameter_3 = fields.Text(string='Parameter 3')
    parameter_4 = fields.Text(string='Parameter 4')
    parameter_5 = fields.Text(string='Parameter 5')
    description_invoice = fields.Text(
        'INVOICE DESCRIPTION',
        help='Invoice details the customer.\n', note='Please enter details'
    )
    description_short = fields.Text(
        'SHORT DESCRIPTION')
    item_no = fields.Char(string="Item Number")
    configuration_price = fields.Monetary(string="Configurator Price", currency_field='currency_id')
    mfr_no = fields.Char(string="Mfr No")
    item_group = fields.Char(string="Item Group")
    model = fields.Char('Model')
    make = fields.Char('Make')
    sac = fields.Char("SAC")
    hsn = fields.Char("HSN")
    origin_country_id = fields.Many2one('res.country', string="Country of Origin")
    # country_id = fields.Many2one(
    #     'res.country',
    #     string="Country/Region of Origin",
    #     help="Select the country associated with this record."
    # )

    def name_get(self):
        result = []
        for product in self:
            name = ''
            if product.item_no:
                name += '[' + product.item_no + ']'
            name += product.name
            if product.model:
                name += '[' + product.model + ']'
            if product.make:
                name += '[' + product.make + ']'
            if product.origin_country_id:
                name += '[' + product.origin_country_id.name + ']'
            result.append((product.id, name))
        return result

    # @api.model
    # def create(self, vals):
    #     user = self.env.user
    #     current_company = self.env.company  # Get the current company context
    #
    #     # Ensure the current company is "Accom" (i.e., the company the user is currently in)
    #     if current_company.name != 'Accom':
    #         raise UserError(_("You must switch to the 'Accom' company to create products."))
    #
    #     # Ensure the user has "Accom" in their allowed companies
    #     if current_company not in user.company_ids:
    #         raise UserError(
    #             _("You are restricted from creating products because you do not belong to the 'Accom' company."))
    #
    #     # Optionally set company_id to the current company if not provided
    #     if not vals.get('company_id'):
    #         vals['company_id'] = current_company.id
    #
    #     return super(Product, self).create(vals)
    #
    # def write(self, vals):
    #     user = self.env.user
    #     current_company = self.env.company  # Get the current company context
    #
    #     # Ensure the current company is "Accom"
    #     if current_company.name != 'Accom':
    #         raise UserError(_("You must switch to the 'Accom' company to modify products."))
    #
    #     # Ensure the user has "Accom" in their allowed companies
    #     if current_company not in user.company_ids:
    #         raise UserError(
    #             _("You are restricted from modifying products because you do not belong to the 'Accom' company."))
    #
    #     # Optionally prevent changing the company_id to a different company
    #     if 'company_id' in vals and vals['company_id'] != current_company.id:
    #         raise UserError(
    #             _("You cannot change the company of the product from 'Accom'. It must remain under the current company."))
    #
    #     return super(Product, self).write(vals)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            args += ['|', '|', '|', '|', '|', '|', '|',
                     ('name', operator, name),
                     ('item_no', operator, name),
                     ('parameter_1', operator, name),
                     ('parameter_2', operator, name),
                     ('parameter_3', operator, name),
                     ('parameter_4', operator, name),
                     ('parameter_5', operator, name),
                     ('model', operator, name),
                     ('make', operator, name)]
        return super(Product, self)._search(args, limit=limit, access_rights_uid=name_get_uid)


class ProductProduct(models.Model):
    _inherit = "product.product"

    parameter_1 = fields.Text(string='Parameter 1')
    parameter_2 = fields.Text(string='Parameter 2')
    parameter_3 = fields.Text(string='Parameter 3')
    parameter_4 = fields.Text(string='Parameter 4')
    parameter_5 = fields.Text(string='Parameter 5')
    item_no = fields.Char(
        string="Item Number",
        related='product_tmpl_id.item_no',
        store=True,
    )
    configuration_price = fields.Monetary(
        string="Configurator Price",
        related='product_tmpl_id.configuration_price',
        store=True,
        readonly=False,
        currency_field='currency_id'
    )
    mfr_no = fields.Char(
        string="Mfr No",
        related='product_tmpl_id.mfr_no',
        store=True,
        readonly=False
    )
    # type = fields.Char(
    #     string="Type",
    #     related='product_tmpl_id.type',
    #     store=True,
    #     readonly=False
    # )
    item_group = fields.Char(
        string="Item Group",
        related='product_tmpl_id.item_group',
        store=True,
        readonly=False
    )


    def name_get(self):
        result = []
        for product in self:
            name = ''
            if product.item_no:
                name += '[' + product.item_no + ']'
            name += product.name
            if product.model:
                name += '[' + product.model + ']'
            if product.make:
                name += '[' + product.make + ']'
            if product.origin_country_id:
                name += '[' + product.origin_country_id.name + ']'
            result.append((product.id, name))
        return result


# class IrActionsReport(models.Model):
#     _inherit = "ir.actions.report"
#
#     @api.model
#     def _remove_picking_operation_report(self):
#         report = self.env.ref("stock.action_report_picking",raise_if_not_found=False)
#         if report:
#             report.write({'binding_model_id':False})
