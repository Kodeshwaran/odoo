from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TermsConditions(models.Model):
    _name = 'account.terms'
    _description = 'Account Terms'

    name = fields.Char()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    terms_conditions_ids = fields.One2many('account.terms.conditions', 'terms_conditions_id', string='Terms & Conditions')


class SaleTermsConditions(models.Model):
    _name = 'account.terms.conditions'
    _description = 'Account Terms and Condition'
    _rec_name = 'value'


    # name = fields.Char()
    value = fields.Char()
    terms_conditions_id = fields.Many2one('account.terms')


class AccountMoveTermsConditions(models.Model):
    _name = 'account.move.terms.conditions'
    _description = 'Account MOve Terms and Conditions'

    name = fields.Char()
    value = fields.Char()
    invoice_id = fields.Many2one('account.move')
    terms_conditions_id = fields.Many2one('account.terms')
    terms_conditions_value_ids = fields.Many2one('account.terms.conditions', string='Terms & Conditions')


class AccountTermsConditionsTemplate(models.Model):
    _name = 'account.terms.template'
    _description = 'account Terms Template'

    name = fields.Char()
    terms_conditions_ids = fields.Many2many('account.terms', copy=False, string="Template")



class AccountMoveDescriptionDetails(models.Model):
    _name = 'account.move.description.details'
    _description = 'Account MOve Description Details'

    name = fields.Char()
    value = fields.Char()
    invoice_id = fields.Many2one('account.move')


class AccountMOve(models.Model):
    _inherit = 'account.move'

    terms_conditions_template_id = fields.Many2one('account.terms.template', copy=False)
    terms_conditions_ids = fields.One2many('account.move.terms.conditions', 'invoice_id')
    description_detail_ids = fields.One2many('account.move.description.details', 'invoice_id')
    note_inside_description = fields.Html(string='Note Inside Description')
    project_description = fields.Text(string="Description")
    # total_claimed_description = fields.Monetary(string="Total Claimed Previously")
    # retention_description = fields.Monetary(string="Retention")

    @api.onchange('terms_conditions_template_id')
    def terms_conditions_onchange(self):
        """ Updates terms_conditions_ids in sale order when a template is selected. """
        self.terms_conditions_ids = False  # Clear existing conditions if any
        if self.terms_conditions_template_id:
            terms_condition_ids = self.env['sale.terms'].search([
                ('id', 'in', self.terms_conditions_template_id.terms_conditions_ids.ids)
            ])

            for terms in self.terms_conditions_template_id.terms_conditions_ids:
                self.env['account.move.terms.conditions'].create({
                    'invoice_id': self.id,
                    'terms_conditions_id': terms.id,
                })
