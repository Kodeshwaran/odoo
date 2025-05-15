# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sales_head = fields.Many2one('res.users', string='Sales Head', related='company_id.sales_head', readonly=False)
    md_person = fields.Many2one('res.users', string='MD', related='company_id.md_person', readonly=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    sales_head = fields.Many2one('res.users', string='Sales Head')
    md_person = fields.Many2one('res.users', string='MD')
