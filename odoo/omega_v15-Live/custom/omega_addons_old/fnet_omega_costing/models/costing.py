# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _


class PurchaseCosting(models.Model):
    _name = 'purchase.costing'
    
    name = fields.Char('Name', size=64, required=True)
    active = fields.Boolean('Active',default=True)

# purchase_costing()


class CostingDuty(models.Model):
    _name = 'costing.duty'
    
    name = fields.Char('Name', size=64, required=True)
    amount = fields.Float('Value', required=True)
    active = fields.Boolean('Active', default=True)
    
# costing_duty()


class CostingMargin(models.Model):
    _name = 'costing.margin'

    name = fields.Char('Name', size=64, required=True)
    amount = fields.Float('Value', required=True)
    active = fields.Boolean('Active', default=True)
