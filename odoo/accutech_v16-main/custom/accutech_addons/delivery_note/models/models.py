from odoo import models
from num2words import num2words


class DeliveryNoteReport(models.AbstractModel):
    _name = 'report.delivery_note.report_delivery_note'
    _description = 'Delivery Note Report'

    def _get_report_values(self, docids, data=None):
        # Fetch the documents from stock.picking
        docs = self.env['stock.picking'].browse(docids)

        # For demonstration, assuming pagination with a fixed number of records per page
        records_per_page = 10
        total_records = len(docs)
        total_pages = (total_records + records_per_page - 1) // records_per_page  # Calculate total pages

        current_page = 1

        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'currentPage': current_page,
            'totalPages': total_pages,
        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'


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

    # def amount_total_in_words(self):
    #     """
    #     Converts the total value of the picking into words in title case
    #     and appends the Abu Dhabi currency (AED) with Fils.
    #     """
    #     try:
    #         total_amount = sum(line.quantity_done * line.product_id.standard_price for line in self.move_lines)
    #         dirhams = int(total_amount)
    #         fils = round((total_amount - dirhams) * 100)
    #
    #         dirhams_words = num2words(dirhams, lang='en').title()
    #         fils_words = num2words(fils, lang='en').title() if fils > 0 else None
    #
    #         if fils_words:
    #             return f"AED {dirhams_words}, And {fils_words} Fils Only"
    #         else:
    #             return f"AED {dirhams_words} Only"
    #
    #     except Exception as e:
    #         return f"Error converting amount to words: {e}"
