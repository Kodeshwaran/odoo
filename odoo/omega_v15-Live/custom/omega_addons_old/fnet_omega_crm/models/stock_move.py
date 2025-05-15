# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil import relativedelta
import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.addons.procurement.models import procurement
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"
    
    item_no = fields.Char('Item No')
    
    @api.multi
    def assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a new
        picking to assign them to. """
        Picking = self.env['stock.picking']
        for move in self:
            picking = Picking.search([
                ('group_id', '=', move.group_id.id),
                ('location_id', '=', move.location_id.id),
                ('location_dest_id', '=', move.location_dest_id.id),
                ('picking_type_id', '=', move.picking_type_id.id),
                ('printed', '=', False),
                ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])], limit=1)
            if not picking:
                picking = Picking.create(move._get_new_picking_values())
            move.write({'picking_id': picking.id,'item_no':move.procurement_id.sale_line_id.item_no})
        return True
    _picking_assign = assign_picking

    def _get_new_picking_values(self):
        """ Prepares a new picking for this move as it could not be assigned to
        another picking. This method is designed to be inherited. """
        return {
            'origin': self.origin,
            'company_id': self.company_id.id,
            'move_type': self.group_id and self.group_id.move_type or 'direct',
            'partner_id': self.partner_id.id,
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
        }
    _prepare_picking_assign = _get_new_picking_values 
    
class StockPickingInherit(models.Model):
    _inherit = "stock.picking"
    
    shipment_type = fields.Char("Carrier Type")
    omega_trn_no = fields.Char("Omega TRN No.")
    package_name = fields.Char("Package")
    package_dimention = fields.Char("Package Dimension")
    package_net = fields.Char("Net Weight")
    package_gross = fields.Char("Gross Weight")
           
