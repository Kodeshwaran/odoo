from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TermsConditions(models.Model):
    _name = 'purchase.terms'
    _description = 'Purchase Terms'

    name = fields.Char()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    terms_conditions_ids = fields.One2many('purchase.terms.conditions', 'terms_conditions_id', string='Terms & Conditions')


class PurchaseTermsConditions(models.Model):
    _name = 'purchase.terms.conditions'
    _description = 'Purchase Terms and Conditions'
    _rec_name = 'value'

    # name = fields.Char()
    value = fields.Char()
    terms_conditions_id = fields.Many2one('purchase.terms')

class PurchaseTermsConditionsTemplate(models.Model):
    _name = 'purchase.terms.template'
    _description = 'purchase Terms Template'

    name = fields.Char()
    terms_conditions_ids = fields.Many2many('purchase.terms', copy=False, string="Template")


class PurchaseOrderTermsConditions(models.Model):
    _name = 'purchase.order.terms.conditions'
    _description = 'Purchase order Terms conditions'

    name = fields.Char()
    value = fields.Char()
    order_id = fields.Many2one('purchase.order')
    terms_conditions_id = fields.Many2one('purchase.terms')
    terms_conditions_value_ids = fields.Many2one('purchase.terms.conditions', string='Terms & Conditions')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    terms_conditions_template_id = fields.Many2one('purchase.terms.template', copy=False)
    terms_conditions_ids = fields.One2many('purchase.order.terms.conditions', 'order_id')
    note_after_terms_conditions = fields.Html(string='Note After Terms & Conditions')
    note_inside_description = fields.Html(string='Note Inside Description')
    note_inside_below_description = fields.Html(string='Note Inside Description Bottom')
    show_in_report = fields.Boolean('Show description in Report')
    bill_to = fields.Many2one('res.company', string='Bill To')
    ship_to = fields.Many2one('res.company', string='Ship To')
    bill_to_contact = fields.Char('Bill To Contact')
    ship_to_contact = fields.Char('Ship To Contact')

    @api.onchange('terms_conditions_template_id')
    def terms_conditions_onchange(self):
        """ Updates terms_conditions_ids in sale order when a template is selected. """
        self.terms_conditions_ids = False  # Clear existing conditions if any
        if self.terms_conditions_template_id:
            terms_condition_ids = self.env['purchase.terms'].search([
                ('id', 'in', self.terms_conditions_template_id.terms_conditions_ids.ids)
            ])

            for terms in self.terms_conditions_template_id.terms_conditions_ids:
                self.env['purchase.order.terms.conditions'].create({
                    'order_id': self.id,
                    'terms_conditions_id': terms.id,
                })




class ResCompany(models.Model):
    _inherit = 'res.company'

    set_categ_id = fields.Many2one('product.category', string='Product Category')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    set_categ_id = fields.Many2one(
        'product.category',
        string='Default Product Category',
        related='company_id.set_categ_id',
        readonly=False,
        default_model='res.company'
    )

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_default_category_id(self):
        company = self.env.context.get('force_company') or self.env.user.company_id
        return company.set_categ_id

    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True, help="Select category for the current product")
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id)





