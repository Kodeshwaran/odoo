from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class AccountMove(models.Model):
    _inherit = "account.move"

    stock_returns = fields.Many2many('stock.picking', string="Stock Returns")
    return_count = fields.Integer(string="Returns", compute="_return_count")

    def view_returns(self):
        return {
            'name': _('Return Products'),
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.stock_returns.ids)],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'active_test': False},
        }

    def _return_count(self):
        for rec in self:
            rec.return_count = len(rec.stock_returns)

    def return_grn(self):
        picking_ids = self.env['stock.picking'].search([('origin', '=', self.invoice_origin)])
        picking_id = picking_ids[0] if picking_ids else False
        print("---", picking_id, "--picking--")
        if picking_id:
            new_picking = self.env['stock.picking'].create({
                'move_lines': [],
                'partner_id': picking_id.partner_id.id,
                'picking_type_id': picking_id.picking_type_id.return_picking_type_id.id or picking_id.picking_type_id.id,
                'state': 'draft',
                'origin': _("Return of %s") % picking_id.name,
                'location_id': picking_id.location_dest_id.id,
                'location_dest_id': picking_id.location_id.id,
                'move_type': picking_id.move_type
            })
            for line in self.invoice_line_ids.filtered(lambda x: not x.display_type and not x.is_rounding_line):
                vals = {
                    'product_id': line.product_id.id,
                    'name':line.name,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': new_picking.id,
                    'state': 'draft',
                    'date': fields.Datetime.now(),
                    'location_id': picking_id.location_dest_id.id,
                    'location_dest_id': picking_id.location_id.id,
                    'picking_type_id': new_picking.picking_type_id.id,
                    'warehouse_id': picking_id.picking_type_id.warehouse_id.id,
                    'procure_method': 'make_to_stock',
                }
                print("---", vals, "--vals--")
                new_picking.write({'move_lines': [(0, 0, vals)]})
            self.write({'stock_returns': new_picking})
            return {
                'name': _('Returned Picking'),
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'res_id': new_picking.id,
                'type': 'ir.actions.act_window',
            }

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
