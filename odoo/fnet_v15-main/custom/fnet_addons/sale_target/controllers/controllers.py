# -*- coding: utf-8 -*-
# from odoo import http


# class SaleTarget(http.Controller):
#     @http.route('/sale_target/sale_target', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_target/sale_target/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_target.listing', {
#             'root': '/sale_target/sale_target',
#             'objects': http.request.env['sale_target.sale_target'].search([]),
#         })

#     @http.route('/sale_target/sale_target/objects/<model("sale_target.sale_target"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_target.object', {
#             'object': obj
#         })
