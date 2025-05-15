from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class ProductTemplate(models.Model):
    _inherit = 'product.product'

    @api.constrains('detailed_type')
    def product_validation(self):
        for rec in self:
            if rec.detailed_type in ['product', 'consu'] and rec.invoice_policy != 'delivery':
                raise ValidationError("Invoicing Policy must be selected as 'Delivered Quantities' for storable product")
            if rec.detailed_type in ['product', 'consu'] and rec.purchase_method != 'receive':
                raise ValidationError("Control Policy must be selected as 'On Received Quantities' for storable product")
            if rec.detailed_type == 'service' and rec.service_policy != 'ordered_timesheet':
                raise ValidationError("Invoicing Policy must be selected as 'Prepaid/Fixed Price' for service product")
            if rec.detailed_type == 'service' and rec.purchase_method != 'purchase':
                raise ValidationError("Control Policy must be selected as 'On Ordered Quantities' for service product")
