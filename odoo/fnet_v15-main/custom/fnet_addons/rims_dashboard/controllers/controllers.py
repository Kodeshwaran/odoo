# -*- coding: utf-8 -*-
# from odoo import http


# class RimsDashboard(http.Controller):
#     @http.route('/rims_dashboard/rims_dashboard', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rims_dashboard/rims_dashboard/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rims_dashboard.listing', {
#             'root': '/rims_dashboard/rims_dashboard',
#             'objects': http.request.env['rims_dashboard.rims_dashboard'].search([]),
#         })

#     @http.route('/rims_dashboard/rims_dashboard/objects/<model("rims_dashboard.rims_dashboard"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rims_dashboard.object', {
#             'object': obj
#         })
