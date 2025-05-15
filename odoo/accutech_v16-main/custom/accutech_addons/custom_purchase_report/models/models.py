from odoo import models
from num2words import num2words

class SalesQuotationReport(models.AbstractModel):
    _name = 'report.custom_purchase_report.report_purchase_order_quotation'
    _description = 'Purchase Quotation Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['purchase.order'].browse(docids)

        # Pagination logic
        records_per_page = 10
        total_records = len(docs)
        total_pages = (total_records + records_per_page - 1) // records_per_page
        current_page = 1  # Assuming this is the first page

        return {
            'doc_ids': docids,
            'doc_model': 'purchase.order',
            'docs': docs,
            'currentPage': current_page,
            'totalPages': total_pages,
        }


class SaleOrder(models.Model):
    _inherit = 'purchase.order'

    def amount_total_in_words(self):
        """
        Converts the total amount into words in title case and appends the Abu Dhabi currency (AED) with Fils.
        """
        try:
            amount_in_words = self.currency_id.amount_to_text(self.amount_total).replace(',', '')
            return amount_in_words

        except Exception as e:
            return f"Error converting amount to words: {e}"


    # def amount_total_in_words(self):
    #     amount_words = num2words(self.amount_total, lang='en')
    #     amount_words_title_case = amount_words.title()
    #     return f"AED {amount_words_title_case} Only"

    # def group_set_string(self):
    #     set_products = {}
    #     purchase_order_lines = self.order_line
    #     set_values = self.order_line.mapped('set')
    #
    #     if set_values and len(set(set_values)) != 1:
    #         for rec in purchase_order_lines:
    #             key = rec.set
    #             if key not in set_products:
    #                 set_products[key] = {
    #                     'products': [],
    #                     'total_subtotal': 0.0,
    #                     'model': [],
    #                     'make': [],
    #                     'description_purchase': [],
    #                     'total_qty': 0.0,
    #                     'total_discount': 0.0,
    #                     'price_unit': rec.price_unit,
    #                 }
    #
    #             # Use product_name if product_id is not present
    #             product_name = rec.product_id.name if rec.product_id else rec.product_name or '-'
    #             set_products[key]['products'].append(product_name)
    #
    #             description = (
    #                     rec.product_id.description_purchase or
    #                     rec.product_template_id.description_purchase or
    #                     rec.product_id.description_short or
    #                     rec.product_name or '-'
    #             )
    #             set_products[key]['description_purchase'].append(description)
    #
    #             set_products[key]['model'].append(rec.product_id.model or '-')
    #             set_products[key]['make'].append(rec.product_id.make or '-')
    #             set_products[key]['total_subtotal'] += rec.price_subtotal
    #             set_products[key]['total_qty'] += rec.product_uom_qty
    #             set_products[key]['total_discount'] += rec.discount
    #
    #         # Post-process to convert lists into strings
    #         for key in set_products:
    #             set_products[key]['products'] = ' + '.join(set_products[key]['products'])
    #             set_products[key]['description_purchase'] = ' + '.join(filter(None, set_products[key]['description_purchase']))
    #             set_products[key]['model'] = ' + '.join(filter(None, set_products[key]['model']))
    #             set_products[key]['make'] = ' + '.join(filter(None, set_products[key]['make']))
    #
    #         return set_products
    #
    #     return False
