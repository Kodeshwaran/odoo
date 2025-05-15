from odoo import models, api

class ProformaInvoiceReport(models.AbstractModel):
    _name = 'report.proforma_invoice.report_proforma_invoice_main'
    _description = 'Proforma Invoice Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['proforma.invoice'].browse(docids)
        if not docs:
            raise ValueError("No Proforma Invoice records found for the given IDs.")

        # Create a dictionary to store purchase orders for each invoice
        purchase_orders_by_invoice = {}

        for doc in docs:
            # Assuming `sale_order_id` is a field on `proforma.invoice`
            if doc.sale_order_id:
                purchase_order = self.env['purchase.order'].search([
                    ('sale_id', '=', doc.sale_order_id.id)
                ], limit=1)
                if purchase_order:
                    purchase_orders_by_invoice[doc.id] = purchase_order

        return {
            'doc_ids': docids,
            'doc_model': 'proforma.invoice',
            'docs': docs,
            'purchase_orders_by_invoice': purchase_orders_by_invoice,
        }
