from datetime import date
from odoo import api, fields, models, _
from dateutil import relativedelta


class SaletypeMaster(models.Model):
    _name = "saletype.master"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char("Sale Type Name", tracking=True)
    name1 = fields.Char(related="name",string="Sale Type Name1", tracking=True,store=True)
    name2 = fields.Char(related="name",string="Sale Type Name2", tracking=True,store=True)
    customer_id = fields.Integer(string="ID", tracking=True,store=True)

class Saletype1Private(models.Model):
    _inherit = 'sale.type'

    @api.model
    def create(self, vals):
        res = super(Saletype1Private, self).create(vals)
        user1 = self.env['saletype.master'].create({
            'name': vals.get('name')
        })
        return res
    #
    # def write(self, vals):
    #     res = super(Saletype1Private, self).write(vals)
    #
    #     if 'name' in vals:
    #         user = self.env['saletype.master'].search([('login', '=', self.work_email)])
    #         if user:
    #             user.write({'name': vals['name']})
    #     return res


