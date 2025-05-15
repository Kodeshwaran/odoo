from odoo import api, fields, models, _
# ~ import uuid
from odoo.exceptions import UserError, except_orm


class CustomerPartner(models.Model):
    _inherit = 'res.partner'

    custom_street = fields.Char('Street')
    custom_street2 = fields.Char('Street2')
    custom_zip = fields.Char('Zip', size=24)
    custom_city = fields.Char('City')
    custom_state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    custom_country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            partner = self.env['res.partner'].search([('name', '=', vals.get('name')), ('id', '!=', self.id)])
            if partner and partner.name != 'Administrator':
                raise UserError(_("The partner already exist!"))
        return super(CustomerPartner, self).create(vals)


    def write(self, vals):
        if vals.get('name'):
            partner = self.env['res.partner'].search([('name', '=', vals.get('name')), ('id', '!=', self.id)])
            if partner and partner.name != 'Administrator':
                raise UserError(_("The partner already exist!"))
        return super(CustomerPartner, self).write(vals)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    iban_number = fields.Char("IBAN No.")
