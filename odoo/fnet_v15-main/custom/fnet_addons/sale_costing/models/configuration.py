from odoo import models, fields, api, _


class OtherSalecostTemplate(models.Model):
    _name = "other.salecost.template"
    _description = 'other sale cost template'

    name = fields.Char("Name")
    charge_ids = fields.Many2many('other.salecost', string="Charges Template")
    type = fields.Selection(string="Default Amount in", related="charge_ids.type")
    amount = fields.Float(string="Cost Type", related="charge_ids.amount")

class OtherSalecost(models.Model):
    _name = "other.salecost"
    _description = 'other sale cost'

    name = fields.Char("Name")
    type = fields.Selection([('fixed', 'Amount'), ('percentage', 'Percentage')], string="Default Amount in", default='fixed')
    amount = fields.Float("Default Value", default=1.0)
    cost_type = fields.Selection([('work', 'EX-Work'), ('landed', 'Landed'), ('other', 'Other')], string="Cost Type", default='other')


class CostCancelRequest(models.TransientModel):
    _name = 'cost.cancel.request'
    _description = 'Cost Cancel Request'

    name = fields.Char("Cancel Reason", required=1)

    def action_confirm(self):
        cost_id = self.env['sale.costing'].browse(self.env.context.get('active_id'))
        cost_id.write({
            'state': 'cancel',
            'cancel_reason': self.name
        })
        return True

