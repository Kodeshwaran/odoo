from dataclasses import field

from docutils.nodes import description
from odoo import models, fields
from bs4 import BeautifulSoup

from datetime import datetime
from num2words import num2words

class SalesQuotationReport(models.AbstractModel):
    _name = 'report.custom_sales_report.report_sales_quotation'
    _description = 'Sales Quotation Report'

    def _get_report_values(self, docids, data=None):
        purchase_id = ''
        purchase_order = self.env['purchase.order'].search([('sale_id', '=', docids)], limit=1)
        if purchase_order:
            purchase_id = purchase_order


        # Fetch the sale order documents
        docs = self.env['sale.order'].browse(docids)

        # Pagination setup
        records_per_page = 10
        total_records = len(docs)
        total_pages = (total_records + records_per_page - 1) // records_per_page  # Calculate total pages

        current_page = 1  # Default to the first page

        # Return the context for the report
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'currentPage': current_page,
            'totalPages': total_pages,
            'purchase': purchase_id,
        }

class SalesOrderReport(models.AbstractModel):
    _name = 'report.custom_sales_report.report_sales_order'
    _description = 'Sales Quotation Report'

    def _get_report_values(self, docids, data=None):
        purchase_id = ''
        purchase_order = self.env['purchase.order'].search([('sale_id', '=', docids)], limit=1)
        if purchase_order:
            purchase_id = purchase_order


        # Fetch the sale order documents
        docs = self.env['sale.order'].browse(docids)

        # Pagination setup
        records_per_page = 10
        total_records = len(docs)
        total_pages = (total_records + records_per_page - 1) // records_per_page  # Calculate total pages

        current_page = 1  # Default to the first page

        # Return the context for the report
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'currentPage': current_page,
            'totalPages': total_pages,
            'purchase': purchase_id,
        }

    # def _get_report_values(self, docids, data=None):
    #     purchase = ''
    #     purchase_order = self.env['purchase.order'].search([('sale_id', '=', self.id)])
    #     if purchase_order:
    #         purchase = purchase_order
    #     # Fetch the documents
    #     docs = self.env['sale.order'].browse(docids)
    #
    #     # For demonstration, assuming pagination with a fixed number of records per page
    #     records_per_page = 10
    #     total_records = len(docs)
    #     total_pages = (total_records + records_per_page - 1) // records_per_page  # Calculate total pages
    #
    #     current_page = 1
    #     sales_contacts = {}
    #
    #
    #     return {
    #         'doc_ids': docids,
    #         'doc_model': 'sale.order',
    #         'docs': docs,
    #         'currentPage': current_page,
    #         'totalPages': total_pages,
    #         'purchase': purchase,
    #     }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # def description_short_report(self):
    #     description = ''
    #     # h = html2text.HTML2Text()
    #     for line in self.order_line:
    #         if line.description_short:
    #             description = line.description_short
    #             print('\n------------', description, '-------description--------')
    #     return description

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

    def group_set_string(self):
        set_products = {}
        sale_order_lines = self.order_line

        for rec in sale_order_lines:
            key = rec.set
            if key not in set_products:
                set_products[key] = {
                    'products': [],
                    'total_subtotal': 0.0,
                    'model': [],
                    'make': [],
                    'description_short': [],
                    'total_qty': 0.0,
                    'total_discount': 0.0,
                    'price_unit': rec.price_unit,
                    'hsn': [],
                    'country_id': [],
                    'parameter_1': [],
                    'delivery_period': [],
                    'spec_remarks': [],
                    'uom': [],
                    'header_text': [],  # New field
                }

            product_name = rec.product_id.name if rec.product_id else rec.product_name or ''
            set_products[key]['products'].append(product_name)

            description_short = rec.description_short
            set_products[key]['description_short'].append(description_short)

            set_products[key]['model'].append(rec.product_id.model or '')
            set_products[key]['make'].append(rec.product_id.make or '')
            set_products[key]['total_subtotal'] += rec.price_subtotal
            set_products[key]['total_qty'] += rec.product_uom_qty
            set_products[key]['total_discount'] += rec.discount  # Add discount to total_discount

            hsn = rec.hsn or ''
            set_products[key]['hsn'].append(hsn)

            country_name = rec.country_id.name if rec.country_id else ''
            set_products[key]['country_id'].append(country_name)

            parameter_1 = rec.parameter_1 or ''
            set_products[key]['parameter_1'].append(parameter_1)

            delivery_period = rec.delivery_period or ''
            set_products[key]['delivery_period'].append(delivery_period)

            spec_remarks = rec.spec_remarks or ''
            set_products[key]['spec_remarks'].append(spec_remarks)

            uom_name = rec.product_uom.name if rec.product_uom else ''
            set_products[key]['uom'].append(uom_name)

            # Process new field
            header_text = rec.header_text or ''
            set_products[key]['header_text'].append(header_text)

        # Convert list fields into concatenated strings
        for key in set_products:
            set_products[key]['products'] = ' + '.join(set_products[key]['products'])
            set_products[key]['description_short'] = ' + '.join(filter(None, set_products[key]['description_short']))
            set_products[key]['model'] = ' + '.join(filter(None, set_products[key]['model']))
            set_products[key]['make'] = ' + '.join(filter(None, set_products[key]['make']))
            set_products[key]['hsn'] = ' + '.join(filter(None, set_products[key]['hsn']))
            set_products[key]['country_id'] = ' + '.join(filter(None, set_products[key]['country_id']))
            set_products[key]['parameter_1'] = ' + '.join(filter(None, set_products[key]['parameter_1']))
            set_products[key]['delivery_period'] = ' + '.join(filter(None, set_products[key]['delivery_period']))
            set_products[key]['spec_remarks'] = ' + '.join(filter(None, set_products[key]['spec_remarks']))
            set_products[key]['uom'] = ' + '.join(filter(None, set_products[key]['uom']))
            set_products[key]['header_text'] = ' + '.join(filter(None, set_products[key]['header_text']))

        return set_products if set_products else False

    def get_purchase_order_id(self):
        purchase_order = self.env['purchase.order'].search([('sale_id', '=', self.id)])
        return purchase_order

