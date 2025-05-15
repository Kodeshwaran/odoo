from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class SaleBudget(models.Model):
    _name = 'sale.budget'
    _description = 'Sale Budget'
    _rec_name = 'name'

    name = fields.Char(string="Description", required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    sale_type_ids = fields.Many2many('sale.type', string="Sale Types")
    sale_budget_lines = fields.One2many('sale.budget.line', 'budget_id', string="Budget Lines")
    state = fields.Selection([('draft', 'Draft'), ('budget_computed', 'Budget Computed')], string='Status', default='draft')

    def reset_to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_compute_lines(self):
        if not self.sale_type_ids:
            raise ValidationError('Select atleast one Sale Type to generate budget lines')
        else:
            self.sale_budget_lines.unlink()
            for sale_type in self.sale_type_ids:
                for sub_type in sale_type.sales_sub_types:
                    vals = {
                        'budget_id': self.id,
                        'sale_type_id': sale_type.id,
                        'sale_sub_type_id': sub_type.id,
                    }
                    self.env['sale.budget.line'].create(vals)
            self.write({'state': 'budget_computed'})


class SaleBudgetLine(models.Model):
    _name = 'sale.budget.line'
    _description = 'Sale Budget Line'

    budget_id = fields.Many2one('sale.budget', string="Budget")
    sale_type_id = fields.Many2one('sale.type', string='Sale Type')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    sale_sub_type_id = fields.Many2one('sale.type.line', string='Sale Type Line')
    new_customer_target = fields.Float(string='New Customer Target')
    existing_customer_target = fields.Float('Existing Customer Target')
    new_vendor_target_percent = fields.Float('New Vendor Percentage')
    existing_vendor_target_percent = fields.Float('Existing Vendor Percentage')
    new_vendor_target = fields.Float('New Vendor Target', compute='_compute_percentage_calc')
    existing_vendor_target = fields.Float('Existing Vendor Target')
    new_expense_target = fields.Float('New Expense Target')
    existing_expense_target = fields.Float('Existing Expense Target')
    is_no_bill = fields.Boolean("No Bills", help="If selected, the target and margin amount only based on the percentage and not from the vendor bill.")

    @api.onchange('sale_type_id')
    def onchange_sale_type(self):
        self.sale_sub_type_id = False

    @api.onchange('is_no_bill', 'existing_customer_target', 'existing_vendor_target_percent')
    def onchange_vendor_target(self):
        if self.is_no_bill and self.existing_customer_target > 0 and self.existing_vendor_target_percent > 0:
            self.existing_vendor_target = self.existing_customer_target * self.existing_vendor_target_percent
        else:
            self.existing_vendor_target = 0

    @api.depends('new_customer_target', 'existing_customer_target', 'new_vendor_target_percent', 'existing_vendor_target_percent')
    def _compute_percentage_calc(self):
        for rec in self:
            rec.new_vendor_target = rec.new_customer_target - (rec.new_customer_target * rec.new_vendor_target_percent)
