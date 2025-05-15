# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_type = fields.Selection([('new', 'New Customer'), ('existing', 'Existing Customer')], default='existing')
    request_count = fields.Integer(string='Request Count', compute="compute_request_count")

    # def action_sale_quotations_new(self):
    #     if self.partner_type == 'new' and not self.partner_id:
    #         raise UserError(_('Request a new Customer through the Customer Creation Request button'))
    #     return super(CrmLead, self).action_sale_quotations_new()

    def compute_request_count(self):
        for rec in self:
            partner_request_count = self.env['partner.request'].search_count([('opportunity_id', '=', self.id)])
            rec.request_count = partner_request_count

    def action_view_customer_request(self):
        partner_request = self.env['partner.request'].search([('opportunity_id', '=', self.id)], limit=1)
        return {
            'name': _('Customer Creation Request'),
            'res_model': 'partner.request',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            'res_id': partner_request.id,
        }

    def action_create_partner(self):
        partner_creation = self.env['partner.request'].create({
            'opportunity_id': self.id,
            'name': self.partner_name or '',
            'street': self.street or '',
            'street2': self.street2 or '',
            'city': self.city or '',
            'state_id': self.state_id.id or False,
            'zip': self.zip or '',
            'country': self.country_id.id or False,
        })
        return {
            'name': _('Customer Creation Request'),
            'res_model': 'partner.request',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            'res_id': partner_creation.id,
        }
