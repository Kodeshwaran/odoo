from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"
   
    current_revision_id = fields.Many2one('sale.order', 'Current revision', readonly=True, copy=True)
    old_revision_ids = fields.One2many('sale.order', 'current_revision_id', 'Old revisions', readonly=True,
                                       context={'active_test': False})
    revision_number = fields.Integer('Revision', copy=False)
    unrevisioned_name = fields.Char('Order Reference', copy=False, readonly=True)
    active = fields.Boolean('Active', default=True, copy=True)
    revised = fields.Boolean('Revised Quotation')   
    
    @api.model
    def create(self, vals):
        if 'unrevisioned_name' not in vals:
            # if vals.get('name', 'New') == 'New':
            #     seq = self.env['ir.sequence']
            #     vals['name'] = seq.next_by_code('sale.order') or '/'
            # vals['unrevisioned_name'] = vals['name']
            if vals.get('quotation_name', 'New') == 'New':
                vals['quotation_name'] = self.env['ir.sequence'].next_by_code('sale.quotation') or _('New')
            vals['unrevisioned_name'] = vals['quotation_name']
        return super(SaleOrder, self).create(vals)
    
    def action_revision(self):
        self.ensure_one()
        view_ref = self.env['ir.model.data'].sudo().check_object_reference('sale', 'view_order_form')
        view_id = view_ref and view_ref[1] or False,
        self.with_context(sale_revision_history=True).copy()
        self.write({'state': 'draft'})
        self.order_line.write({'state': 'draft'})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }
        
    @api.returns('self', lambda value: value.id)
    def copy(self, defaults=None):
        if not defaults:
            defaults = {}
        if not self.unrevisioned_name:
            self.unrevisioned_name = self.quotation_name
        if self.env.context.get('sale_revision_history'):
            prev_name = self.quotation_name
            revno = self.revision_number
            self.write({'revision_number': revno + 1, 'quotation_name': '%s-%02d' % (self.unrevisioned_name, revno + 1)})
            defaults.update({'quotation_name': prev_name,
                             'revision_number': revno,
                             'revised': True,
                             'active': True,
                             'state': 'cancel',
                             'current_revision_id': self.id,
                             'unrevisioned_name': self.unrevisioned_name,
                             'sale_order_approval_rule_ids': [(4, rec.id) for rec in self.sale_order_approval_rule_ids],
                             'sale_order_approval_history': [(4, rec.id) for rec in self.sale_order_approval_history],
            })
            values = self._get_data_sale_order_approval_rule_ids()
            if values:
                self.write({'send_approve_process': True, 'send_for_approval': False})
                for v in values:
                    v.update({'state': 'draft'})
                    self.env['sale.order.approval.rules'].create(v)
        return super(SaleOrder, self).copy(defaults)
