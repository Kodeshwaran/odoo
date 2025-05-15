# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    state_taxes_ids = fields.Many2many('account.tax', 'productmp_taxes_rel', 'prod_id', 'tax_id', string='State Taxes', domain=[('type_tax_use', '=', 'sale')])
    code_new = fields.Char('Code')
    product_master_type = fields.Selection([('DELL', 'Dell'), ('KASPERSKY', 'Kaspersky'), ('CITRIX', 'Citrix'), ('VMWARE', 'VMware'), ('MICROSOFT', 'Microsoft'), ('SOPHOS', 'Sophos')], string="Product Master Type")

    @api.model
    def create(self, vals):
        if vals['l10n_in_hsn_code'] != False and (len(vals['l10n_in_hsn_code']) < 6):
            raise ValidationError("Length of HSN/SAC Code can either be 6 or 10 characters only")
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        if 'l10n_in_hsn_code' in vals and (len(vals['l10n_in_hsn_code']) < 6):
            raise ValidationError("Length of HSN/SAC Code can either be 6 or 10 characters only")
        return super(ProductTemplate, self).write(vals)




