from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TermsConditions(models.Model):
    _name = 'sale.terms'
    _description = 'Sale Terms'

    name = fields.Char()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    terms_conditions_ids = fields.One2many('sale.terms.conditions', 'terms_conditions_id', string='Terms & Conditions')



class SaleTermsConditions(models.Model):
    _name = 'sale.terms.conditions'
    _description = 'Sale terms and Conditions'
    _rec_name='value'

    # name = fields.Char(string="Name")
    value = fields.Char()
    terms_conditions_id = fields.Many2one('sale.terms')


class TermsConditionsTemplate(models.Model):
    _name = 'sale.terms.template'
    _description = 'Sale Terms Template'

    name = fields.Char()
    terms_conditions_ids = fields.Many2many('sale.terms', copy=False, string="Template")



class SaleOrderTermsConditions(models.Model):
    _name = 'sale.order.terms.conditions'
    _description = 'Sale Order Terms and Conditions'

    name = fields.Char(string="Name")
    value = fields.Char(string="Value")
    terms_conditions_id = fields.Many2one('sale.terms')
    terms_conditions_value_ids = fields.Many2one('sale.terms.conditions', string='Terms & Conditions')
    order_id = fields.Many2one('sale.order', string="Sale Order")

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    terms_conditions_template_id = fields.Many2one('sale.terms.template',string='Terms & Conditions', copy=False)
    terms_conditions_ids = fields.One2many('sale.order.terms.conditions', 'order_id')

    @api.onchange('terms_conditions_template_id')
    def terms_conditions_onchange(self):
        """ Updates terms_conditions_ids in sale order when a template is selected. """
        self.terms_conditions_ids = False  # Clear existing conditions if any
        if self.terms_conditions_template_id:
            terms_condition_ids = self.env['sale.terms'].search([
                ('id', 'in', self.terms_conditions_template_id.terms_conditions_ids.ids)
            ])

            for terms in self.terms_conditions_template_id.terms_conditions_ids:
                self.env['sale.order.terms.conditions'].create({
                    'order_id': self.id,
                    'terms_conditions_id': terms.id,
                })



