from odoo import models, fields, api, _
from odoo.exceptions import ValidationError  # Import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char(string="Customer Code", readonly=True, copy=False)
    admin_user = fields.Many2one(
        'res.users',
        string="Admin Person",
        help="The admin user responsible for this res.partner"
    )
    trn_no = fields.Char(string="TRN NO")
    aed_account = fields.Char(string="AED Account")
    usd_account = fields.Char(string="USD Account")
    euro_account = fields.Char(string="Euro Account")

    @api.model
    def create(self, vals):
        # Check if a partner with the same name already exists, excluding the current record if it's being copied
        if vals.get('name'):
            existing_partner = self.search([('name', '=', vals['name'])], limit=1)
            if existing_partner:
                # Ensure that if this is a duplicate (copy), it doesn't create a new record
                if vals.get('id') != existing_partner.id:
                    raise ValidationError(_("A customer with the same name already exists."))

        # Handle customer_code if not provided
        if vals.get('customer_code', _('New')) == _('New'):
            vals['customer_code'] = self.env['ir.sequence'].next_by_code('res.partner') or _('New')

        return super(ResPartner, self).create(vals)

    def write(self, vals):
        # Check if a partner with the same name already exists when updating
        if vals.get('name'):
            existing_partner = self.search([('name', '=', vals['name'])], limit=1)
            if existing_partner:
                # Ensure that if this is a duplicate (copy), it doesn't create a new record
                if self.id != existing_partner.id:
                    raise ValidationError(_("A customer with the same name already exists."))

        return super(ResPartner, self).write(vals)

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    aed_account = fields.Char(string="AED Account")
    usd_account = fields.Char(string="USD Account")
    euro_account = fields.Char(string="Euro Account")