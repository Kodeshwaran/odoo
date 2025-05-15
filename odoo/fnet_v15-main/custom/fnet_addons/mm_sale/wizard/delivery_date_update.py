# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang


class SaleOrderLineWizard(models.TransientModel):

    _name = 'sale.order.line.wizard'
    _description = 'Sale Order Line Delivery Date'

    delivery_date = fields.Date(string='Delivery Date',  required=True)
    order_delivery_date = fields.Date(string='Ordered Delivered Date')
    sale_order_line_id = fields.Many2one('sale.order.line', 'SALE Line')

    def action_delivery_date_update(self):
        if self.sale_order_line_id:
            self.sale_order_line_id.write({'ordered_delivery_date': self.delivery_date})
            self.email_delivery_update()

        else:
            raise UserError(_('Please refresh your screen and try again.'))

    def email_delivery_update(self):
        mail_template = self.env.ref('mm_sale.email_delivery_data_update')
        mail_template.send_mail(self.id, force_send=True)
