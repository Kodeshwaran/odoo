# -*- coding: utf-8 -*-
from openerp import http

# class PurchaseDetails(http.Controller):
#     @http.route('/purchase_details/purchase_details/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_details/purchase_details/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_details.listing', {
#             'root': '/purchase_details/purchase_details',
#             'objects': http.request.env['purchase_details.purchase_details'].search([]),
#         })

#     @http.route('/purchase_details/purchase_details/objects/<model("purchase_details.purchase_details"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_details.object', {
#             'object': obj
#         })