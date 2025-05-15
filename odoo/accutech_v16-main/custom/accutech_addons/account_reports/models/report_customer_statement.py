from odoo import models, api

class ReportCustomerStatement(models.AbstractModel):
    _name = 'report.account_reports.report_customer_statement_report_main'
    _description = 'Customer Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        partner_id = data.get('partner_id') if data else None
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        domain = [('partner_id', '=', partner_id)]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))

        # Fetch only specific fields (this reduces memory + avoids unnecessary joins)
        move_lines = self.env['account.move.line'].search_read(
            domain,
            fields=[
                'display_type',
                'product_id',
                'product_uom_id',
                'quantity',
                'date_maturity',
            ],
            order='date asc'
        )

        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(partner_id),
            'move_lines': move_lines,
            'date_from': date_from,
            'date_to': date_to,
        }
