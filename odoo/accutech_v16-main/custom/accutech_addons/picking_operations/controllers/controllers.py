# -*- coding: utf-8 -*-
# from odoo import http


# class PickingOperations(http.Controller):
#     @http.route('/picking_operations/picking_operations', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/picking_operations/picking_operations/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('picking_operations.listing', {
#             'root': '/picking_operations/picking_operations',
#             'objects': http.request.env['picking_operations.picking_operations'].search([]),
#         })

#     @http.route('/picking_operations/picking_operations/objects/<model("picking_operations.picking_operations"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('picking_operations.object', {
#             'object': obj
#         })
