# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_geolocation = fields.Boolean(string='Enable Geolocation')
    enable_geofencing = fields.Boolean(string='Enable Geofencing')
    geo_fencing_distance = fields.Float(string='Geo-Fencing Distance')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_geolocation = fields.Boolean(string='Enable Geolocation', related='company_id.enable_geolocation', readonly=False)
    enable_geofencing = fields.Boolean(string='Enable Geofencing', related='company_id.enable_geofencing', readonly=False)
    geo_fencing_distance = fields.Float(string='Geo-Fencing Distance(km)', related='company_id.geo_fencing_distance', readonly=False)
