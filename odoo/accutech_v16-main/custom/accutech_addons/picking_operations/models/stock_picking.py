from odoo import models, fields, api, _
import logging
import base64
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_status = fields.Selection([
        ('need_to_download', 'Need to Download'),
        ('downloaded', 'Downloaded')
    ], default='need_to_download', string="Picking Status")

    # quality_check_ids = fields.One2many('quality.check', 'picking_id', string='Quality Checks')

    def action_open_quality_check(self):
        """Open or create a quality check"""
        check = self.env['quality.check'].search([('picking_id', '=', self.id)], limit=1)
        if not check:
            check = self.env['quality.check'].create_quality_check(self.id)  # Ensure picking_id is passed correctly
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check',
            'view_mode': 'form',
            'res_id': check.id,
        }

    def button_validate(self):
        if self.picking_type_id.code == 'outgoing':
            related_out_pickings = self.search([
                ('picking_type_id.code', '=', 'outgoing'),
                ('origin', '=', self.origin),
                ('id', '!=', self.id),
                ('state', '!=', 'done')
            ])

            if any(picking.state != 'done' for picking in related_out_pickings):
                raise ValidationError(
                    "You cannot validate this picking record because there are pending delivery operations (outgoing orders). "
                    "Please ensure all deliveries are completed before validating this record."
                )

        elif self.picking_type_id.code == 'incoming':
            return super(StockPicking, self).button_validate()

        if self.picking_type_id.code == 'outgoing' and self.state == 'ready':
            for move in self.move_lines:
                if move.product_uom_qty > move.reserved_availability:
                    move.write({'quantity_done': move.reserved_availability})

        return super(StockPicking, self).button_validate()

    def update_downloaded_status(self):
        for picking in self:
            # Toggle the is_downloaded field
            picking.picking_status = 'downloaded'

            # Fetch the correct report action
            report = self.env['ir.actions.report']._get_report_from_name('picking_operations.report_picking_operations')

            # Validate report exists
            if not report:
                raise ValidationError("Report not found. Ensure the report name is correct and exists in the database.")

            # Render the QWeb report as PDF
            pdf_content, report_type = report._render_qweb_pdf(report.id, self.id)

            # Validate PDF content
            if not pdf_content:
                raise ValueError("Failed to generate PDF report.")

            # Create an attachment for the report
            attachment = self.env['ir.attachment'].create({
                'name': f"Picking_Report_{', '.join(self.mapped('name'))}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'mimetype': 'application/pdf',
                'res_model': 'stock.picking',
                'res_id': picking.id,
            })

            # Return the URL for the attachment to trigger download
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
