from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import html2plaintext
from odoo.exceptions import ValidationError
from bs4 import BeautifulSoup
import re

import logging

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    due_amount = fields.Monetary(string="Due Amount", compute="compute_due_amount", store=True)
    is_expense_bill = fields.Boolean(string="Is Expense Bill", default=False)

    def _check_vendor_payment_limits(self):
        """
        Cron job method to check all vendors' payment limits every 12 hours.
        Sends an email to account_person_email if any vendor's unpaid bills exceed the payment limit.
        """
        # Get the account person email from General Settings
        account_person_email = self.env['ir.config_parameter'].sudo().get_param(
            'res.config.settings.account_person_email')

        if not account_person_email:
            raise ValidationError("No account person email configured in General Settings.")

        # Validate the email address using regex
        if not self._is_valid_email(account_person_email):
            raise ValidationError("Invalid email address in General Settings: %s" % account_person_email)

        # Find all partners with a set payment limit
        partners = self.env['res.partner'].search([('payment_limit', '>', 0)])

        # Prepare data for email
        vendors_exceeding_limit = []

        for partner in partners:
            # Get all unpaid or partially paid vendor bills for this partner
            vendor_bills = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'in_invoice'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('state', '=', 'posted')
            ])

            # Calculate the total due amount for all unpaid/partially paid bills
            total_due = sum(bill.amount_residual for bill in vendor_bills)

            # Check if the total due amount exceeds the partner's payment limit
            if total_due > partner.payment_limit:
                vendors_exceeding_limit.append({
                    'vendor_name': partner.name,
                    'total_due': total_due,
                    'payment_limit': partner.payment_limit,
                })

        # Send email if there are vendors exceeding their limits
        if vendors_exceeding_limit:
            self._send_limit_exceeded_email(vendors_exceeding_limit, account_person_email)

    def _send_limit_exceeded_email(self, vendors_exceeding_limit, account_person_email):
        """
        Sends an email with a list of vendors whose payment limits are exceeded.
        """
        subject = "Payment Limit Exceeded for Vendors"

        # Build the email body with an HTML table
        body_html = """
            <p>Dear User,</p>
            <p>The following vendors have exceeded their payment limits:</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Vendor</th>
                    <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Payment Limit</th>
                    <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Total Due</th>
                </tr>
        """

        for vendor in vendors_exceeding_limit:
            body_html += """
                <tr>
                    <td style="border: 1px solid #dddddd; padding: 8px;">{vendor_name}</td>
                    <td style="border: 1px solid #dddddd; padding: 8px;">{payment_limit}</td>
                    <td style="border: 1px solid #dddddd; padding: 8px;">{total_due}</td>
                </tr>
            """.format(
                vendor_name=vendor['vendor_name'],
                payment_limit=vendor['payment_limit'],  # Corrected placement
                total_due=vendor['total_due']  # Corrected placement
            )

        body_html += "</table><p>Please review the situation and take appropriate actions.</p>"

        # Create and send the email
        mail_values = {
            'subject': subject,
            'body_html': body_html,
            'email_to': account_person_email,
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

    def _is_valid_email(self, email):
        """
        Validates the email address using a simple regex pattern.
        """
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        return re.match(email_regex, email) is not None

    @api.depends('line_ids.debit', 'line_ids.credit')
    def compute_due_amount(self):
        for rec in self:
            total_credit = sum(line.credit for line in rec.line_ids)
            total_debit = sum(line.debit for line in rec.line_ids)
            rec.due_amount = total_debit - total_credit


    # @api.constrains('name', 'journal_id', 'state')
    # def _check_unique_sequence_number(self):
    #     moves = self.filtered(lambda move: move.state == 'posted' or move.state == 'draft')
    #
    #     if not moves:
    #         return
    #
    #     self.flush(['name', 'journal_id', 'move_type', 'state'])
    #
    #     # SQL to check for duplicates across posted or draft states
    #     self._cr.execute('''
    #         SELECT move2.id, move2.name
    #         FROM account_move move
    #         INNER JOIN account_move move2 ON
    #             move2.name = move.name
    #             AND move2.journal_id = move.journal_id
    #             AND move2.move_type = move.move_type
    #             AND move2.id != move.id
    #         WHERE move.id IN %s AND move2.state IN ('draft', 'posted')
    #     ''', [tuple(moves.ids)])
    #
    #     res = self._cr.fetchall()
    #     if res:
    #         # If there is a conflict, fetch the next available sequence number
    #         for move in moves:
    #             next_sequence = move._get_next_available_sequence()
    #             move.write({'name': next_sequence})
    #
    #         # Re-check after assigning new sequence numbers to ensure uniqueness
    #         self._cr.execute('''
    #             SELECT move2.id, move2.name
    #             FROM account_move move
    #             INNER JOIN account_move move2 ON
    #                 move2.name = move.name
    #                 AND move2.journal_id = move.journal_id
    #                 AND move2.move_type = move.move_type
    #                 AND move2.id != move.id
    #             WHERE move.id IN %s AND move2.state IN ('draft', 'posted')
    #         ''', [tuple(moves.ids)])
    #
    #         res = self._cr.fetchall()
    #         if res:
    #             # If there are still conflicts, raise a validation error
    #             problematic_numbers = ', '.join(r[1] for r in res)
    #             raise ValidationError(_('Journal entries must have a unique sequence number per journal.\n'
    #                                     'Duplicate sequence numbers found: %s') % problematic_numbers)
    #
    # def _get_next_available_sequence(self):
    #     """Custom method to generate the next available sequence."""
    #     for move in self:
    #         journal = move.journal_id
    #         sequence = journal.sequence_id
    #
    #         # Generate the next sequence number based on the journal's sequence
    #         if not sequence:
    #             raise ValidationError(_("Please define a sequence on the journal '%s'.") % journal.name)
    #
    #         # Get the next sequence for the journal
    #         next_sequence = sequence.next_by_id()
    #         return next_sequence

    # FUNCTION FOR CALCULATING CHEQUE AMOUNT
    @api.depends('amount_total')
    def _get_cheque_amount(self):
        if self.amount_total:
            self.cheque_amount = self.amount_total
        else:
            self.cheque_amount = False

    # FUNCTION FOR CALCULATING CHEQUE DATE
    @api.depends('invoice_date_due')
    def _get_cheque_date(self):
        if self.invoice_date_due:
            self.cheque_date = self.invoice_date_due
        else:
            self.cheque_date = False

    @api.depends('invoice_line_ids.analytic_account_id')
    def _compute_analytic_account_id(self):
        for move in self:
            analytic = move.invoice_line_ids.mapped('analytic_account_id')
            move.analytic_account_id = analytic.id if len(analytic) == 1 else False

    @api.onchange('line_ids', 'line_ids.partner_id')
    def onchange_partner_id(self):
        if self.move_type == 'entry':
            partner = self.line_ids.mapped('partner_id')
            self.partner_id = partner.id if len(partner) == 1 else False

    @api.model
    def _get_journal(self):
        res = []
        ttype = self._context.get('journal_type')
        if ttype:
            res = self.env['account.journal'].search([('name', '=', ttype)], limit=1)
        else:
            res = self._get_default_journal()
        return res

    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain="[('company_id', '=', company_id)]",
                                 default=_get_journal, )
            
    analytic_account_id = fields.Many2one('account.analytic.account', compute='_compute_analytic_account_id', string="Analytic account", store=True, readonly=True)
    cheque_number = fields.Char("Cheque Number")
    cheque_amount = fields.Float("Cheque Amount", compute="_get_cheque_amount")
    cheque_date = fields.Date("Cheque Date", compute="_get_cheque_date")
    cheque_details = fields.Text("Cheque Details")   
    note = fields.Char("Notes")
    narration_char = fields.Text("Narration")
    number_ref = fields.Char("Number Ref")
    amount_invoice = fields.Float("Amount Invoice 1 Ref")
    amount_invoice2 = fields.Float("Amount Invoice 2 Ref")
    cheque_narration = fields.Char("Cheque Narration")
    narration = fields.Html(string='Terms and Conditions', compute='_compute_narration', store=True, readonly=False)

    @api.onchange('narration')
    def onchange_narration(self):
        self._message_log(body=_('Narration has been changed to %s from %s' % (self.narration, self._origin.narration)))

    @api.depends('move_type', 'partner_id', 'company_id')
    def _compute_narration(self):
        for rec in self:
            rec.narration = rec.narration   

    @api.onchange('narration')
    def onchange_narration(self):
        if self.narration:
            soup = BeautifulSoup(self.narration, 'html.parser')
            self.narration_char = soup.get_text()


class AccountAccount(models.Model):
    _inherit = 'account.account'

    group_name = fields.Char(string="Group Name")


class ResPartner1(models.Model):
    _inherit = 'res.partner'

    payment_limit = fields.Float(string="Payment Limit", help="Defines the maximum payment limit allowed for the partner.")



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_person_email = fields.Char(string="Account Person Email", help="Email of the account person")

    def set_values(self):
        """Override the set_values method to save the email in system parameters"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.account_person_email', self.account_person_email)

    @api.model
    def get_values(self):
        """Override the get_values method to retrieve the email from system parameters"""
        res = super(ResConfigSettings, self).get_values()
        res['account_person_email'] = self.env['ir.config_parameter'].sudo().get_param('res.config.settings.account_person_email', default='')
        return res

class AccountReportStandardLedgerLine(models.TransientModel):
    _inherit = "account.report.standard.ledger.line"

    narration = fields.Html(related='move_id.narration', string="Narration")







