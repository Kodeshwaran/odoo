from datetime import date
from odoo import api, fields, models, _
from dateutil import relativedelta


class ProductMaster(models.Model):
    _name = "product.master"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char("Product Name", tracking=True)
    name1 = fields.Char(related="name",string="Product Name1", tracking=True,store=True)
    name2 = fields.Char(related="name",string="Product Name2", tracking=True,store=True)
    customer_id = fields.Integer(string="Customer ID", tracking=True,store=True)

class Product1Private(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        res = super(Product1Private, self).create(vals)
        user1 = self.env['product.master'].create({
            'name': vals.get('name')
        })
        return res

    def write(self, vals):
        res = super(Product1Private, self).write(vals)

        if 'name' in vals:
            user = self.env['product.master'].search([('login', '=', self.work_email)])
            if user:
                user.write({'name': vals['name']})
        return res


