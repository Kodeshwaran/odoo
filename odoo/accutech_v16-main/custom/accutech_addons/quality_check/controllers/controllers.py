# -*- coding: utf-8 -*-
# from odoo import http


# class QualityCheck(http.Controller):
#     @http.route('/quality_check/quality_check', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/quality_check/quality_check/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('quality_check.listing', {
#             'root': '/quality_check/quality_check',
#             'objects': http.request.env['quality_check.quality_check'].search([]),
#         })

#     @http.route('/quality_check/quality_check/objects/<model("quality_check.quality_check"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('quality_check.object', {
#             'object': obj
#         })
