# -*- coding: utf-8 -*-
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_pro_forma = fields.Boolean('Allow Pro-Forma Invoices', related='company_id.allow_pro_forma', readonly=False)
    pro_forma_sequence = fields.Many2one(related='company_id.pro_forma_sequence', readonly=False)
