# -*- coding: utf-8 -*-
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pro_forma_number = fields.Char(string='Pro-forma number', readonly=True, copy=False)
    pro_forma_date = fields.Date(string='Pro-forma Date', readonly=True, copy=False)
    pro_forma_generated = fields.Boolean(string='Pro Forma Generated', default=False)
    approval_state = fields.Selection([('no', 'No Approvals'),
                                       ('not_sent', 'Not Sent'),
                                       ('to_approve', 'Waiting for Approval'),
                                       ('approved', 'Approved'),
                                       ], string="Approval Status",)

    def generate_pro_forma(self):
        today = fields.Date.today()
        for order in self:
            company = order.company_id or order.env.company
            if company.pro_forma_sequence:
                date = order.date_order or today
                sequence = company.pro_forma_sequence
                order.pro_forma_number = sequence.with_context(ir_sequence_date=date).next_by_id()
                order.pro_forma_date = today
                order.pro_forma_generated = True
