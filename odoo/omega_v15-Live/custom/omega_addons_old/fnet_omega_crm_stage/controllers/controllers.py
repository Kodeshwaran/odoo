# -*- coding: utf-8 -*-
from openerp import http

# class Stage(http.Controller):
#     @http.route('/stage/stage/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stage/stage/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stage.listing', {
#             'root': '/stage/stage',
#             'objects': http.request.env['stage.stage'].search([]),
#         })

#     @http.route('/stage/stage/objects/<model("stage.stage"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stage.object', {
#             'object': obj
#         })