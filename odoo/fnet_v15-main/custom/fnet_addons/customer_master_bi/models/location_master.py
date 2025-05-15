from datetime import date
from odoo import api, fields, models, _
from dateutil import relativedelta


class CompanyMaster(models.Model):
    _name = "company.master"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char("Customer Name", tracking=True)
    name1 = fields.Char(related="name",string="Customer Name1", tracking=True,store=True)
    name2 = fields.Char(related="name",string="Customer Name2", tracking=True,store=True)
    customer_id = fields.Integer(string="Customer ID", tracking=True,store=True)

class ResPartner1Private(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        res = super(ResPartner1Private, self).create(vals)
        user1 = self.env['company.master'].create({
            'name': vals.get('name')
        })
        return res

    def write(self, vals):
        res = super(ResPartner1Private, self).write(vals)

        if 'name' in vals:
            user = self.env['company.master'].search([('login', '=', self.work_email)])
            if user:
                user.write({'name': vals['name']})
        return res


