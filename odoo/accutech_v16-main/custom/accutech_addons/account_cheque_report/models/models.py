# -*- coding: utf-8 -*-

#-*- coding:utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from num2words import num2words


class BankCheckReport(models.AbstractModel):
    _inherit = 'account.move'
    _description = 'Bank Cheque'

    @api.model
    def _get_report_values(self, docids, data=None):
        inv = self.env['account.move'].browse(docids)
        print (inv.to_self, "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': inv,
            'data': data,
        }

    def amount_total_in_words(self):
        """
        Converts the total debit amount in line_ids into words (dirhams and fils) and
        returns the result with a line break after the first 6 words and extra space between lines.
        """
        try:
            # Sum all the debit amounts from account.move.line records
            total_debit = sum(line.debit for line in self.line_ids)

            # Convert the total debit amount to dirhams and fils
            dirhams = int(total_debit)  # Get the integer part for dirhams
            fils = round((total_debit - dirhams) * 100)  # Get the decimal part for fils (in cents)

            # Convert dirhams and fils to words
            dirhams_words = num2words(dirhams, lang='en').title()  # Convert dirhams to words
            fils_words = num2words(fils, lang='en').title() if fils > 0 else None  # Convert fils to words, if any

            # Combine dirhams and fils into one string
            if fils_words:
                amount_in_words = f"AED {dirhams_words}, And {fils_words} Fils Only"
            else:
                amount_in_words = f"AED {dirhams_words} Only"

            # Split the amount in words into individual words
            words = amount_in_words.split()

            # Create a result string where we will place a line break after 6 words and additional spacing
            result = []
            for i in range(0, len(words), 8):
                chunk = " ".join(words[i:i + 8])  # Take a chunk of 6 words
                result.append(chunk)  # Add the chunk to the result

            # Join the chunks with a <br/> tag to create a line break after every 6 words
            # Add a second <br/> tag for extra space between lines
            return "<br/><br/>".join(result)

        except Exception as e:
            # Handle any errors that may occur (for example, missing line_ids or other issues)
            return f"Error converting amount to words: {e}"
