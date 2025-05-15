from odoo import models, fields
from num2words import num2words

class AccountMoveReport(models.AbstractModel):
    _name = 'report.custom_account_report.report_account_move_invoice'
    _description = 'Account Move Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        sale = ''
        sale_id = self.env['sale.order'].search([('invoice_ids', '=', docids)], limit=1)
        if sale_id:
            sale = sale_id
        
        # account_id = ''
        # account = self.env['account.move'].search([('id', '=', docids)])
        # print('\n------------', account.purchase_id, '-------account.purchase_id,--------')
        # if account:
        #     account_id = account

        stock_id = ''
        stock_picking = self.env['stock.picking'].search([
            # ('purchase_id', '=', account_id.purchase_id),
            ('location_id.name', 'ilike', 'Output')
        ], limit=1)

        if stock_picking:
            stock_id = stock_picking

        # Pagination logic
        records_per_page = 10
        total_records = len(docs)
        total_pages = (total_records + records_per_page - 1) // records_per_page
        current_page = 1  # Assuming this is the first page

        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'currentPage': current_page,
            'totalPages': total_pages,
            'sale': sale,
            'stock': stock_id,
        }


class AccountMove(models.Model):
    _inherit = 'account.move'


    def amount_total_in_words(self):
        """
        Converts the total amount into words in title case and appends the Abu Dhabi currency (AED) with Fils.
        """
        try:
            # dirhams = int(self.amount_total)
            # fils = round((self.amount_total - dirhams) * 100)
            #
            # dirhams_words = num2words(dirhams, lang='en').title()
            #
            # fils_words = num2words(fils, lang='en').title() if fils > 0 else None
            #
            # if fils_words:
            #     return f"USD {dirhams_words}, And {fils_words} Fils Only"
            # else:
            #     return f"USD {dirhams_words} Only"
            amount_in_words = self.currency_id.amount_to_text(self.amount_total).replace(',', '')
            return amount_in_words

        except Exception as e:
            return f"Error converting amount to words: {e}"

class AccountPaymentReport(models.AbstractModel):
    _name = 'report.custom_account_report.report_account_move_credit_note'
    _description = 'Account Payment Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)

        sale = False
        stock_id = False

        sale_id = self.env['sale.order'].search([
            ('invoice_ids', 'in', docids)
        ], limit=1)
        if sale_id:
            sale = sale_id

        stock_picking = self.env['stock.picking'].search([
            ('location_id.name', 'ilike', 'Output')
        ], limit=1)
        print("--------", stock_picking,"----stock_picking---\n")
        if stock_picking:
            stock_id = stock_picking

        records_per_page = 10
        total_records = len(docs)
        total_pages = (total_records + records_per_page - 1) // records_per_page
        current_page = 1

        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'currentPage': current_page,
            'totalPages': total_pages,
            'sale': sale,
            'stock': stock_id,
        }