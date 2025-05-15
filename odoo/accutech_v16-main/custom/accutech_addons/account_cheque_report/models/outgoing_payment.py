# -*- coding: utf-8 -*-

#-*- coding:utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from num2words import num2words


class OutgoingPayment(models.AbstractModel):
    _name = 'report.account_cheque_report.report_outgoing_payment'
    _description = 'Outgoing Payment'

    def _get_report_values(self, docids, data=None):
        # Fetch the account.move records
        docs = self.env['account.move'].browse(docids)
        print('\n-------', docs, '---docs----')
        # For demonstration, assuming pagination with a fixed number of records per page
        records_per_page = 10
        total_records = len(docs)
        total_pages = (total_records + records_per_page - 1) // records_per_page  # Calculate total pages

        current_page = 1
        sales_contacts = {}

        # Dictionary to hold payments for each account.move
        payments_dict = {}
        payments = []
        # Access the payments related to each account.move
        for move in docs:
            print('\n-------', move, '---move----')
            # Fetch account.payment records where move_id matches the current move
            payments = self.env['account.payment'].search([]).filtered(lambda p: move.id in p.reconciled_bill_ids.ids)
            print('\n-------', payments, '---payments----')
            # Store the related payments in the dictionary
            payments_dict[move.id] = payments

            # You can now work with payments, e.g., sum their amounts or collect details
            for payment in payments:
                print(f"Payment amount for move {move.name}: {payment.amount}")

        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'currentPage': current_page,
            'totalPages': total_pages,
            'payments_dict': payments,  # Use this in the report template
        }
