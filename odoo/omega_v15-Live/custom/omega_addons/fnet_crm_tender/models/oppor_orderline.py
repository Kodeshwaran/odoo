# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class Lead(models.Model):
    _inherit = 'crm.lead'
    _rec_name = 'opportunity_name'

    opportunity_order_line = fields.One2many('opportunity.order.line', 'lead_id', string='Product Line', copy=True)
    opportunity_name = fields.Char(string="Opportunity Name", readonly=True, required=False, store=True, copy=False)
    tender_counter = fields.Integer(compute='get_tender_count', readonly=True)
    commercial_deadline = fields.Date('Commercial Offer Deadline')
    technical_deadline = fields.Date('Technical Offer Deadline')
    probability_amount = fields.Float("Probability")
    managernotes = fields.Text('Sales Team Manager Remark')
    regrets = fields.Text("Reason for Regrets")

    def get_tender_count(self):
        for rec in self:
            purchase_id = self.env['purchase.requisition'].search([('oppor_id', '=', self.id)])
            rec.tender_counter = len(purchase_id)

    @api.model
    def create(self, vals):
        vals['opportunity_name'] = self.env['ir.sequence'].next_by_code('opportunity_sequence')
        return super(Lead, self).create(vals)


    def make_tender(self):
        """
        This is used to create the tender against the enquiry
        """
        tenders = self.env['purchase.requisition']
        # tender_count = tenders.search([('oppor_id', '=', self.id)])
        # if tender_count:
        #     raise UserError(_('You can create only one Tender !'))
        user = self.env['res.users'].search([('id', '=', self._uid)])
        if not self.partner_id:
            raise UserError(_('Please Select related customer !'))
        # if not self.opportunity_order_line:
        #     raise UserError(_('No Products Found..!'))

        values = {
            'user_id': self.user_id.id,
            'oppor_id': self.id,
            'company_id': user.company_id.id,
            'origin': self.opportunity_name,
            'customer_id': self.partner_id.id,
        }
        quotation = tenders.create(values)
        if quotation:
            value_line = self.env['opportunity.order.line'].search([('lead_id', '=', self.id)])
            for len_val in value_line:
                ret_value = {
                    'requisition_id': quotation.id,
                    'product_id': len_val.product_id.id,
                    'product_qty': len_val.quantity,
                    'product_uom_id': len_val.unit_measure.id,
                }

                tenders.env['purchase.requisition.line'].create(ret_value)
        # res = self.env['ir.actions.act_window'].for_xml_id('purchase_requisition', 'action_purchase_requisition')
        # res['domain'] = [('id', '=', quotation.id)]
        # return res

    def open_tender(self):
        """ This opens purchase tender view to view all opportunity associated to the call for tenders
            @return: the tender tree view
        """
        # res = self.env['ir.actions.act_window'].for_xml_id('purchase_requisition', 'action_purchase_requisition')
        # res['domain'] = [('oppor_id', '=', self.id)]
        return {
            'name': _('Tenders'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'purchase.requisition',
            'domain': [('oppor_id', '=', self.id)],
        }


class OpportunityOrderLine(models.Model):
    _name = 'opportunity.order.line'
    _description = 'Opportunity Order Line'

    lead_id = fields.Many2one('crm.lead', string='Product')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Expected Quantity')
    unit_measure = fields.Many2one('uom.uom', 'Unit of Measure')
    unit_price = fields.Float(string='Expected Price')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.quantity = 1
            rec.unit_measure = rec.product_id.uom_id.id