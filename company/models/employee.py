from datetime import date
from odoo import api, fields, models, tools


class CompanyEmployee(models.Model):
    _name = "company.employee"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "company employee"

    name = fields.Char(string='Name', Tracking=True)
    image = fields.Image(string='Image')
    tags_ids = fields.Many2many('employee.tags', string='tags')

    @api.model
    def create(self, vals):
        vals['ref'] = self.env['ir.sequence'].next_by_code('company.employee')
        return super(CompanyEmployee, self).create(vals)

    def write(self, vals):
        if not self.ref and not vals.get('ref'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('company.employee')
        return super(CompanyEmployee, self).create(vals)

    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', tracking=True, store=True)
    ref = fields.Char(string='Ref', Tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender', default='male')
    active = fields.Boolean(string='Active', default=True)
    meeting_id = fields.Many2one('company.employee', string='Meeting_id')

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            today = date.today()
            if rec.date_of_birth:
                rec.age = today.year - rec.date_of_birth.year
            else:
                rec.age = 1

    def name_get(self):
        employee_list = []
        for record in self:
            name = str(record.ref) + '' + str(record.name)
            employee_list.append((record.id, name))
        return employee_list
