from odoo import api, models, fields,tools



class EmployeeTags(models.Model):
    _name = "employee.tags"
    _description = 'employee Tags'


    name=fields.Char(sring='name')
    active=fields.Boolean(string='Active')
    color=fields.Integer(string='Color')
    color_2=fields.Char(string='Color')
