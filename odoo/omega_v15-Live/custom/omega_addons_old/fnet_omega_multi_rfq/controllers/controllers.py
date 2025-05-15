# -*- coding: utf-8 -*-
from odoo import http

# class MuliRfq(http.Controller):
#     @http.route('/muli_rfq/muli_rfq/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/muli_rfq/muli_rfq/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('muli_rfq.listing', {
#             'root': '/muli_rfq/muli_rfq',
#             'objects': http.request.env['muli_rfq.muli_rfq'].search([]),
#         })

#     @http.route('/muli_rfq/muli_rfq/objects/<model("muli_rfq.muli_rfq"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('muli_rfq.object', {
#             'object': obj
#         })