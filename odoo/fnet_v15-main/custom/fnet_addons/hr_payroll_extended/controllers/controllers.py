# -*- coding: utf-8 -*-
# from odoo import http


# class HrPayrollExtended(http.Controller):
#     @http.route('/hr_payroll_extended/hr_payroll_extended', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_payroll_extended/hr_payroll_extended/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_payroll_extended.listing', {
#             'root': '/hr_payroll_extended/hr_payroll_extended',
#             'objects': http.request.env['hr_payroll_extended.hr_payroll_extended'].search([]),
#         })

#     @http.route('/hr_payroll_extended/hr_payroll_extended/objects/<model("hr_payroll_extended.hr_payroll_extended"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_payroll_extended.object', {
#             'object': obj
#         })
