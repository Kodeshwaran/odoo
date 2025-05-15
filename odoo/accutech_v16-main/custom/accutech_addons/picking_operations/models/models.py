from odoo import models

class PickingOperationsReport(models.AbstractModel):
    _name = 'report.picking_operations.report_picking_operations'
    _description = 'Picking Operations Report'

    def _get_report_values(self, docids, data=None):
        # Fetch the stock picking records
        docs = self.env['stock.picking'].browse(docids)

        # Set the number of records per page
        records_per_page = 10
        total_records = len(docs)
        total_pages = (total_records + records_per_page - 1) // records_per_page  # Calculate total pages

        # Determine the current page dynamically from context or data if needed
        current_page = 1  # Update this to be dynamic if necessary

        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,  # Pass the recordset as 'docs'
            'currentPage': current_page,
            'totalPages': total_pages,
        }
