from odoo import models, fields, api, _
import logging
from odoo.exceptions import ValidationError


class QualityCheck(models.Model):
    _name = 'quality.check'
    _description = 'Quality Check'

    name = fields.Char(string='Quality Check', required=True, default=lambda self: _('New'))
    picking_id = fields.Many2one('stock.picking', string='Delivery Order', required=True)
    responsible_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    product_lines = fields.One2many('quality.check.line', 'quality_check_id', string='Products')
    success = fields.Boolean(string='Success', default=False)
    remarks = fields.Char("Remarks")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('quality_success', 'Quality Success')
    ], string='State', default='draft')


    def action_success(self):
        self.state = 'quality_success'
        self.success = True

        # Transfer data from quality checks to stock picking
        if self.picking_id:
            for quality_line in self.product_lines:  # Use the One2many field `product_lines` in `quality.check`
                # Find the matching stock move in the picking
                stock_move = self.env['stock.move'].search([
                    ('picking_id', '=', self.picking_id.id),
                    ('product_id', '=', quality_line.product_id.id)
                ], limit=1)

                if stock_move:
                    # Update the qty_done in stock.move based on quality check's passed_qty
                    stock_move.write({'quantity_done': quality_line.passed_qty})

    def action_approve(self):
        # Update the state of the current record
        self.state = 'approved'


    def action_reject(self):
        self.state = 'rejected'



    @api.model
    def create_quality_check(self, picking_id):
        """Creates a Quality Check for the given picking"""
        picking = self.env['stock.picking'].browse(picking_id)

        # Fetch stock moves related to the picking
        moves = self.env['stock.move'].search([('picking_id', '=', picking.id)])

        product_lines = []
        for move in moves:
            product_lines.append((0, 0, {
                'product_id': move.product_id.id,
                'reserved_qty': move.product_uom_qty,
                'passed_qty': 0.0,
                'uom_id': move.product_uom.id
            }))

        # Create the quality check record
        return self.create({
            'picking_id': picking.id,
            'product_lines': product_lines
        })

    @api.model
    def create(self, vals):
        if 'name' not in vals:
            sequence = self.env['ir.sequence'].search([('code', '=', 'quality.check')], limit=1)
            if sequence:
                vals['name'] = sequence.next_by_id()
            else:
                vals['name'] = _('New')
        return super(QualityCheck, self).create(vals)


class QualityCheckLine(models.Model):
    _name = 'quality.check.line'
    _description = 'Quality Check Line'

    quality_check_id = fields.Many2one('quality.check', string='Quality Check', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    reserved_qty = fields.Float(string='Reserved Quantity')
    passed_qty = fields.Float(string='Passed Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    move_line_id = fields.Many2one('stock.move.line', string='Stock Move Line')
    question = fields.Char("Question")

