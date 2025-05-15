# -*- coding: utf-8 -*-
from openerp import http

# class Purchasereminder(http.Controller):
#     @http.route('/purchasereminder/purchasereminder/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchasereminder/purchasereminder/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchasereminder.listing', {
#             'root': '/purchasereminder/purchasereminder',
#             'objects': http.request.env['purchasereminder.purchasereminder'].search([]),
#         })

#     @http.route('/purchasereminder/purchasereminder/objects/<model("purchasereminder.purchasereminder"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchasereminder.object', {
#             'object': obj
#         })