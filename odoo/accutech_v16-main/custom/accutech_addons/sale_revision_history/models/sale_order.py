from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"
   
    current_revision_id = fields.Many2one('sale.order', 'Current revision', readonly=True, copy=True)
    old_revision_ids = fields.One2many('sale.order.revision.line', 'current_sale_id', 'Old revisions', readonly=True,
                                       context={'active_test': False})

    revision_number = fields.Integer('Revision', copy=False)
    unrevisioned_name = fields.Char('Order Reference', copy=False, readonly=True)
    active = fields.Boolean('Active', default=True, copy=True)
    revised = fields.Boolean('Revised Quotation')
    quotation_name = fields.Char(string='Quotation Reference', required=True, copy=False, readonly=True, index=True,
                                 default=lambda self: _('New'))
    revision = fields.Integer(string='Sale Revision', copy=False)
    is_stage_1 = fields.Boolean(copy=False)
    is_stage_3 = fields.Boolean(copy=False)
    is_stage_2 = fields.Float(copy=False)
    approve_button = fields.Boolean(compute='_compute_approve_button', string='Approve Button ?',
                                    search='_search_to_approve_orders', copy=False)

    def name_get(self):
        result = []
        for sale in self:
            name = sale.name if sale.state in ['sale', 'done'] else sale.quotation_name
            result.append((sale.id, name))
        return result
    
    @api.model
    def create(self, vals):
        if 'unrevisioned_name' not in vals:
            if vals.get('quotation_name', 'New') == 'New':
                vals['quotation_name'] = self.env['ir.sequence'].next_by_code('sale.quotation') or _('New')
            vals['unrevisioned_name'] = vals['quotation_name']
        return super(SaleOrder, self).create(vals)
    
    def action_revision(self):
        self.ensure_one()
        if not self.sale_order_approval_rule_ids:
            self.send_for_approval = False
        view_ref = self.env['ir.model.data'].sudo().check_object_reference('sale', 'view_order_form')
        view_id = view_ref and view_ref[1] or False,
        self.with_context(sale_revision_history=True).copy()
        revisions = self.old_revision_ids.search([], limit=1)
        if revisions:
            for line in revisions:
                line.write({
                    'name': self.quotation_name,
                    'custom_date': datetime.now(),
                    'create_uid': self.env.user.id,
                    'current_sale_id': self.id,
                })
        else:
            self.old_revision_ids.create({
                'name': self.quotation_name,
                'custom_date': datetime.now(),
                'create_uid': self.env.user.id,
                'current_sale_id': self.id,
            })
        self.write({'state': 'draft', 'send_approval_pricing': False, 'is_manager_approved': False, 'is_revision': True})
        self.order_line.write({'state': 'draft'})
        # for rec in self:
        #     if rec.sale_order_approval_rule_ids == False:
        #         rec.write({'send_for_approval': False, 'state': 'revision'})
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

    def button_confirm_done_delivery_revision(self):
        for rec in self:
            for picking in rec.picking_ids:
                if len(rec.picking_ids) >= 1 and picking.state != 'done':
                    print("\n---1111111111----\n")
                    pick_lines_ids = set(
                        pick_line.sale_line_id.id for pick_line in picking.move_ids_without_package)
                    order_line_ids = set(line.id for line in rec.order_line)

                    for pick_line in picking.move_ids_without_package:
                        if pick_line.sale_line_id.id not in order_line_ids:
                            print("\n---@2222222222----\n")
                            pick_line.unlink()

                    for line in rec.order_line:
                        corresponding_pick_line = picking.move_ids_without_package.filtered(
                            lambda sl: sl.sale_line_id.id == line.id
                        )
                        print("\n---", corresponding_pick_line, "--corresponding_pick_line--\n")
                        if not corresponding_pick_line:
                            picking.move_ids_without_package.create({
                                'picking_id': picking.id,
                                'sale_line_id': line.id,
                                'product_id': line.product_id.id,
                                'name': line.name or line.product_id.display_name,
                                'product_uom_qty': line.product_uom_qty,
                                'quantity_done': 0,
                                'location_id': picking.location_id.id,
                                'location_dest_id': picking.location_dest_id.id,
                                'product_uom': line.product_uom.id,
                                'state': 'confirmed',
                                'company_id': rec.company_id.id,
                                'date': picking.scheduled_date,
                            })

                    for pick_line in picking.move_ids_without_package:
                        for line in rec.order_line:
                            if line.id == pick_line.sale_line_id.id:
                                print("\n---printtssssssssssssss----\n")
                                if line.product_uom_qty != pick_line.product_uom_qty:
                                    if line.product_uom_qty < pick_line.quantity_done:
                                        raise ValidationError(
                                            f"You have already completed {pick_line.quantity_done} units, so you cannot reduce the product count to {line.product_qty}. You can only increase the count to more than the {pick_line.quantity_done} units already done.")
                                    if line.product_uom_qty > pick_line.quantity_done:
                                        pick_line.product_uom_qty = line.product_uom_qty
                else:
                    print("\n---333333333----\n")
                    for line in rec.order_line:
                        corresponding_pick_line = [
                            picking.move_ids_without_package.filtered(
                                lambda pl: pl.sale_line_id.id == line.id
                            )
                            for picking in rec.picking_ids
                            for line in rec.order_line
                        ]
                        if not corresponding_pick_line:
                            picking.move_ids_without_package.create({
                                'picking_id': picking.id,
                                'sale_line_id': line.id,
                                'product_id': line.product_id.id,
                                'name': line.name or line.product_id.display_name,
                                'product_uom_qty': line.product_uom_qty,
                                'quantity_done': 0,
                                'location_id': picking.location_id.id,
                                'location_dest_id': picking.location_dest_id.id,
                                'product_uom': line.product_uom.id,
                                'state': 'confirmed',
                                'company_id': rec.company_id.id,
                                'date': picking.scheduled_date,
                            })
                    if picking.state != 'done':
                        order_line_ids = set(line.id for line in rec.order_line)
                        [pick_line.unlink() for picking in rec.picking_ids for pick_line in
                         picking.move_ids_without_package if pick_line.sale_line_id.id not in order_line_ids]
                        for pick_line in picking.move_ids_without_package:
                            for line in rec.order_line:
                                if line.product_id.id == pick_line.product_id.id:
                                    product_not_done = 0
                                    product_done = 0
                                    product_not_done = sum(pro.product_uom_qty for picking in rec.picking_ids for pro in
                                                           picking.move_ids_without_package if
                                                           picking.state != 'done' and pick_line.product_id == pro.product_id)
                                    product_done = sum(pro.product_uom_qty for picking in rec.picking_ids for pro in
                                                       picking.move_ids_without_package if
                                                       picking.state == 'done' and pick_line.product_id == pro.product_id)
                                    product = product_done + product_not_done
                                    if line.product_uom_qty != product:
                                        if line.product_uom_qty < product_done:
                                            raise ValidationError(
                                                f"You have already completed {product_done} units, so you cannot reduce the product count to {line.product_uom_qty}. You can only increase the count to more than the {product_done} units already done.")
                                        elif line.product_uom_qty < product:
                                            value = product - line.product_uom_qty
                                            if value == 0:
                                                pick_line.unlink()
                                            else:
                                                pick_line.product_uom_qty = pick_line.product_uom_qty - value
                                        elif line.product_uom_qty > product:
                                            value = line.product_uom_qty - product
                                            pick_line.product_uom_qty = pick_line.product_uom_qty + value
            if rec.state == 'revision':
                rec.write({'state': 'sale'})

    def button_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent', 'revision'])
        orders.write({'state': 'draft'})

    def create_revision(self):
        self.ensure_one()
        view_ref = self.env['ir.model.data']._xmlid_lookup('sale.view_order_form')
        print("\n---", view_ref, "--view_ref--\n")
        view_id = view_ref and view_ref[1] or False
        print("\n---", view_id, "--view_id--\n")

        new_revision = self.with_context(new_sale_revision=True).copy()
        self.write({'current_revision_id': new_revision.id})

        self.write({'state': 'draft'})
        self.order_line.write({'state': 'draft'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'res_id': new_revision.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

    def action_done_revision(self):
        for sale in self:
            if sale.picking_ids:
                if all(picking.state == 'done' for picking in sale.picking_ids):
                    raise UserError(
                        'All transfers are fully completed. This Purchase Order is no longer useful. Please create a new Purchase Order.')
            if any(picking.state == 'done' for picking in sale.picking_ids) or any(
                    picking.state == 'assigned' for picking in sale.picking_ids):
                print("\n---11111111111111----\n")
                # raise UserError('Unable to amend this purchase order, You must first cancel all receptions related to this purchase order.')
                sale.state = 'revision'
                # purchase.stage_1 = True
                for line in sale.order_line:
                    line.approval_state = 'no'
                if sale.sale_order_approval_rule_ids:
                    for approval in sale.sale_order_approval_rule_ids:
                        if approval.state != 'draft':
                            approval.state = 'draft'
                            approval.date = False
                            approval.user_id = False
                            approval.is_approved = False
                    old_name = sale.name
                    original_name = sale.name
                    if not original_name:
                        return
                    name_parts = original_name.rsplit('-', 1)
                    if len(name_parts) > 1 and name_parts[1].isdigit() and len(name_parts[1]) == 2:
                        base_name = name_parts[0]
                    else:
                        base_name = original_name
                    sale.revision += 1
                    new_name = f"{base_name}-{str(sale.revision).zfill(2)}"
                    sale.write({'name': new_name, 'is_stage_3': False})
                    print("\n---", sale.name, "--sale.name--\n")
                    self.with_context(sale_revision=True).rename_revision()
                    sale.message_post(
                        body=f"Sale Order name changed from '{old_name}' to '{sale.name}'"
                    )
            else:
                print("\n---2222222222222----\n")
                # sale.picking_ids.filtered(lambda r: r.state != 'cancel').action_cancel()
                for invoice_loop in sale.invoice_ids:
                    if invoice_loop.state not in ['draft', 'cancel']:
                        raise UserError(
                            'Unable to amend this Sale order, You must first cancel all Customer Invoices related to this sale order.')
                    else:
                        invoice_loop.filtered(lambda r: r.state != 'cancel').button_cancel()
                if sale.sale_order_approval_rule_ids:
                    for approval in sale.sale_order_approval_rule_ids:
                        if approval.state != 'draft':
                            approval.state = 'draft'
                            approval.date = False
                            approval.user_id = False
                            approval.is_approved = False
                for history in sale.sale_order_approval_history:
                    if history.state in ['send_for_approval', 'approved']:
                        history.unlink()
                sale.button_draft()
                sale.create_revision()
                sale.write({'send_for_approval': False, 'state': 'revision'})

    def rename_revision(self):
        if self.env.context.get('sale_revision'):
            revisions = self.old_revision_ids.search([], limit=1)
            if revisions:
                for line in revisions:
                    line.write({
                        'name': self.name,
                        'custom_date': datetime.now(),
                        'create_uid': self.env.user.id,
                        'current_sale_id': self.id,
                    })
            else:
                self.old_revision_ids.create({
                    'name': self.name,
                    'custom_date': datetime.now(),
                    'create_uid': self.env.user.id,
                    'current_sale_id': self.id,
                    })

    @api.returns('self', lambda value: value.id)
    def copy(self, defaults=None):
        if not defaults:
            defaults = {}
        if not self.unrevisioned_name:
            self.unrevisioned_name = self.quotation_name
        if self.env.context.get('sale_revision_history'):
            prev_name = self.quotation_name
            revno = self.revision_number
            self.write(
                {'revision_number': revno + 1, 'quotation_name': '%s-%02d' % (self.unrevisioned_name, revno + 1)})
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
                print("--------", 1111111111111,"----1111111111111---\n")
                self.write({'send_approve_process': True, 'send_for_approval': False})
                for v in values:
                    v.update({'state': 'draft'})
                    self.env['sale.order.approval.rules'].create(v)
        return super(SaleOrder, self).copy(defaults)

class SaleOrderApprovalRules(models.Model):
    _inherit = 'sale.order.line'

    approval_state = fields.Selection(related="order_id.approval_state")

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancel(self):
        if any(move.state not in ('draft', 'cancel', 'waiting', 'confirmed', 'done', 'assigned') for move in self):
            raise UserError(_('You can only delete draft or cancelled moves.'))

class SaleOrderRevisions(models.Model):
    _name = 'sale.order.revision.line'

    name = fields.Char('Reference')
    current_sale_id = fields.Many2one('sale.order', 'Current Variation', readonly=True, copy=True)
    custom_date = fields.Datetime('Superseeded On')
    state = fields.Selection(string='State', related='current_sale_id.state')