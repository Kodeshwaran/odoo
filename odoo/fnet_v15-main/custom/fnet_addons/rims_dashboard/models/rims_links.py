# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RimsDashboard(models.Model):
    _name = 'rims.links'
    _description = 'Rims Links'
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True)
    app_icon = fields.Binary("Icon", store=True)
    show_in_dashboard = fields.Boolean(string="Show in Dashboard", default=True)
    url = fields.Char(string="URL", required=True)

    def action_open_url(self):
        if self.url:
            url = self.url
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
