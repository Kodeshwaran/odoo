# -*- coding: utf-8 -*-
# from odoo import http


# class DeliveryNote(http.Controller):
#     @http.route('/delivery_note/delivery_note', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/delivery_note/delivery_note/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('delivery_note.listing', {
#             'root': '/delivery_note/delivery_note',
#             'objects': http.request.env['delivery_note.delivery_note'].search([]),
#         })

#     @http.route('/delivery_note/delivery_note/objects/<model("delivery_note.delivery_note"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('delivery_note.object', {
#             'object': obj
#         })
