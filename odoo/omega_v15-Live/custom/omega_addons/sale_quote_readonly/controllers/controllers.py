# -*- coding: utf-8 -*-
# from odoo import http


# class SaleQuoteReadonly(http.Controller):
#     @http.route('/sale_quote_readonly/sale_quote_readonly', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_quote_readonly/sale_quote_readonly/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_quote_readonly.listing', {
#             'root': '/sale_quote_readonly/sale_quote_readonly',
#             'objects': http.request.env['sale_quote_readonly.sale_quote_readonly'].search([]),
#         })

#     @http.route('/sale_quote_readonly/sale_quote_readonly/objects/<model("sale_quote_readonly.sale_quote_readonly"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_quote_readonly.object', {
#             'object': obj
#         })
