from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
class PurchaseOrderLines(models.Model):
    _inherit = 'purchase.order.line'

    product_category_id=fields.Many2one('product.category','Product Category', change_default=True)
    product_id = fields.Many2one('product.product', string='Product',required=False, change_default=True)

    @api.onchange('product_id')
    def onchange_product_id(self):

        result = {}
        if not self.product_id:
            return result

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if self.product_qty==1:
            self.price_unit = self.product_qty = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        product_lang = self.product_id.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
        })
        if not self.name:
            self.name = product_lang.display_name
            if product_lang.description_purchase:
                self.name += '\n' + product_lang.description_purchase

        fpos = self.order_id.fiscal_position_id
        if self.env.uid == SUPERUSER_ID:
            company_id = self.env.user.company_id.id
            self.taxes_id = fpos.map_tax(
                self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
        else:
            self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)
        self._suggest_quantity()
        self._onchange_quantity()

        return result

    def _suggest_quantity(self):

        '''
        Suggest a minimal quantity based on the seller
        '''
        if not self.product_id:
            return

        seller_min_qty = self.product_id.seller_ids\
            .filtered(lambda r: r.name == self.order_id.partner_id)\
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty:
            self.product_qty = seller_min_qty[0].min_qty or 1.0
            self.product_uom = seller_min_qty[0].product_uom
        elif self.product_qty==1:
            self.product_qty = 1.0



class Purchaseorder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def bid_received(self):
        len_product=len(self.order_line)
        count_val=0
        for order in self.order_line:
            if order.product_id:
               count_val+=1
        if count_val==len_product:
            return super(Purchaseorder, self).bid_received()
        else:
            raise UserError(_('Please set Product name before Change the Bid Received State.'))
    @api.multi
    def send_rfq(self):
        len_product = len(self.order_line)
        count_val = 0
        for order in self.order_line:
            if order.product_id:
                count_val += 1
        if count_val == len_product:
            return super(Purchaseorder, self).send_rfq()
        else:
            raise UserError(_('Please set Product name before Confirm the RFQ.'))

