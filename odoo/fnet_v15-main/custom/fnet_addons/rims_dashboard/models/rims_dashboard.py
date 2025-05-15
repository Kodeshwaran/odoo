from odoo import models, fields, api
from odoo.http import request
import datetime


class RimsDashboard(models.Model):
    _name = 'rims.dashboard'
    _description = 'Rims Dashboard'

    name = fields.Char("")

    @api.model
    def get_links_details(self):
        uid = request.session.uid
        apps = self.env['rims.links'].search([])

        apps_data = {
            'user': self.env['res.users'].search([('id', '=', uid)]),
            'name': [app.name for app in apps],
            'url': [app.url for app in apps]
        }
        return apps_data
