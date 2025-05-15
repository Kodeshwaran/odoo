# -*- coding: utf-8 -*-
# from odoo import http


# class CustomSalesReport(http.Controller):
#     @http.route('/custom_sales_report/custom_sales_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_sales_report/custom_sales_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_sales_report.listing', {
#             'root': '/custom_sales_report/custom_sales_report',
#             'objects': http.request.env['custom_sales_report.custom_sales_report'].search([]),
#         })

#     @http.route('/custom_sales_report/custom_sales_report/objects/<model("custom_sales_report.custom_sales_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_sales_report.object', {
#             'object': obj
#         })
