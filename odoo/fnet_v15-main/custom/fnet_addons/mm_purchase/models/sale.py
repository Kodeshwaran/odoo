# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
import json
from lxml import etree


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            if not self.env.user.has_group('purchase.group_purchase_manager'):
                doc = etree.XML(res['arch'])
                for node in doc.xpath("//field[@name='commitment_date']"):
                    node.set("readonly", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res
