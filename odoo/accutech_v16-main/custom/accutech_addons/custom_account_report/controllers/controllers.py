# -*- coding: utf-8 -*-
# from odoo import http


# class CustomAccountReport(http.Controller):
#     @http.route('/custom_account_report/custom_account_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_account_report/custom_account_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_account_report.listing', {
#             'root': '/custom_account_report/custom_account_report',
#             'objects': http.request.env['custom_account_report.custom_account_report'].search([]),
#         })

#     @http.route('/custom_account_report/custom_account_report/objects/<model("custom_account_report.custom_account_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_account_report.object', {
#             'object': obj
#         })
