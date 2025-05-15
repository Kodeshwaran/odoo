# -*- coding: utf-8 -*-

from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.exceptions import UserError, AccessError,except_orm


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'
    
    vendor_id = fields.Many2many('res.partner', 'pur_partner_rel', 'rfq_rel_id', 'vendor_ids', "Vendor")
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)],
                                 required=False)
    description = fields.Text('Description', required=True)
    product_category_id = fields.Many2one('product.category', 'Product Category')
    select_line = fields.Boolean('Select')  
    item_no = fields.Char('Item No')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    # @api.depends('purchase_ids')
    # def _compute_orders_number(self):
    #     for requisition in self:
    #         g = (tuple(requisition.purchase_ids.ids))
    #         if len(g) == 1:
    #             self.env.cr.execute("select distinct on (partner_id) partner_id from purchase_order where id = %s"%(g))
    #             lin = self.env.cr.fetchall()
    #             m = len(lin)
    #             requisition.order_count = len(lin)
    #         if g == ():
    #             pass
    #         if len(g) > 1:
    #             self.env.cr.execute("select distinct on (partner_id) partner_id from purchase_order where id in %s"%(g,))
    #             lin = self.env.cr.fetchall()
    #             m = len(lin)
    #             requisition.order_count = len(lin)

    def select_all_vendor(self):
        pur_req = self.env['purchase.requisition'].browse(self.ids)
        for line in pur_req.line_ids:
            self.env.cr.execute("update purchase_requisition_line  set select_line = 't' where requisition_id = '%s'"%(self.id))

    def create_rfqs(self):
        partner_list=[]
        no_of_PR = self.env['purchase.order'].search([('requisition_id','=',self.id)])
        ss= tuple(no_of_PR.ids)
        
        for j in range(len(no_of_PR)):
            partner_list.append(no_of_PR[j].partner_id.id)
        no_of = self.env['purchase.requisition.line'].search([('requisition_id','=',self.id),('select_line','=',True)])
        gg = (tuple(no_of.ids))
        vendor_ids=''
        if len(gg) == 1:
            self.env.cr.execute("""select distinct on (ppr.vendor_ids) ppr.vendor_ids
                                     from purchase_requisition_line as prl
                                     left join pur_partner_rel as ppr on ppr.rfq_rel_id = prl.id
                                     where prl.id = %s"""%(gg))
            vendor_ids = self.env.cr.fetchall()
        elif len(gg)>1:
            self.env.cr.execute("""select distinct on (ppr.vendor_ids) ppr.vendor_ids
                                     from purchase_requisition_line as prl
                                     left join pur_partner_rel as ppr on ppr.rfq_rel_id = prl.id
                                     where prl.id in %s"""%(gg,))
            vendor_ids = self.env.cr.fetchall()
        for h in vendor_ids:
            if h[0] in partner_list:
                vendors = self.env['res.partner'].search([('id','=',h[0])])
                raise UserError(_("For %s  RFQ Already Created")%(vendors.name))
        no_of_PRs = self.env['purchase.requisition.line'].search([('requisition_id','=',self.id),('select_line','=',True)])
        g = (tuple(no_of_PRs.ids))
        if len(g) == 1:
            self.env.cr.execute("""select distinct on (ppr.vendor_ids) ppr.vendor_ids
                                     from purchase_requisition_line as prl
                                     left join pur_partner_rel as ppr on ppr.rfq_rel_id = prl.id
                                     where prl.id = %s"""%(g))
            vendor_ids = self.env.cr.fetchall()
        elif len(g)>1:
            self.env.cr.execute("""select distinct on (ppr.vendor_ids) ppr.vendor_ids
                                     from purchase_requisition_line as prl
                                     left join pur_partner_rel as ppr on ppr.rfq_rel_id = prl.id
                                     where prl.id in %s"""%(g,))
            vendor_ids = self.env.cr.fetchall()
        elif len(g) == 0:
            raise UserError(_("Please Select Vendor in PRODUCTS......!"))
        for i in vendor_ids:
            if i[0] not in partner_list:
                
                FiscalPosition = self.env['account.fiscal.position']
                fpos = FiscalPosition.get_fiscal_position(i)
                fpos = FiscalPosition.browse(fpos)
                partner = self.env['res.partner']
                payment_term = partner.browse(i).property_supplier_payment_term_id

                currency = partner.property_purchase_currency_id or self.company_id.currency_id
                if self.type_id.line_copy != 'copy':
                    return
                po_creation = {
                        'partner_id':i,
                        'fiscal_position_id': fpos.id,
                        'payment_term_id': payment_term.id,
                        'company_id': self.company_id.id,
                        'currency_id' : currency.id,
                        'origin' : self.name,
                        'partner_ref': self.name, # to control vendor bill based on agreement reference
                        'notes': self.description,
                        'date_order': self.date_end or fields.Datetime.now(),
                        'picking_type_id':self.picking_type_id.id,
                        'requisition_id':self.id,
                }
                poid = self.env['purchase.order'].create(po_creation)
                self.env.cr.execute("""
                            select prl.product_id,ppr.vendor_ids,prl.id,prl.product_uom_id,prl.product_qty,prl.price_unit,
                            prl.account_analytic_id,uom.id,prl.description as name,prl.item_no
                            from purchase_requisition_line as prl
                            left join purchase_requisition as po on po.id = prl.id
                            left join pur_partner_rel as ppr on ppr.rfq_rel_id = prl.id
                            left JOIN product_product pp ON (pp.id = prl.product_id)
                            left JOIN product_template apt ON (apt.id = pp.product_tmpl_id)
                            left join product_uom uom on (uom.id = apt.uom_id)
                            where prl.requisition_id = %d and ppr.vendor_ids =%d and prl.select_line='t'"""%(self.id,i[0]))
                fin = self.env.cr.fetchall()
                for lines in fin:
                    order_lines = []
                    h = self.env['product.product'].browse(lines[0])
                    product_lang = h.with_context({
                    'lang': partner.lang,
                    'partner_id': partner.id,
                    })
                    name = h.display_name
                    if product_lang.description_purchase:
                        name += '\n' + product_lang.description_purchase
                    if fpos:
                        taxes_ids = fpos.map_tax(h.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.company_id))
                    else:
                        taxes_ids = h.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.company_id).ids
                    # Create PO line
                    order_lines = {
                        'name':lines[8],
                        'product_id': lines[0],
                        'product_uom': lines[3] or lines[7],
                        'product_qty': lines[4],
                        'price_unit': lines[5] ,
                        'taxes_id': [(6, 0, taxes_ids)],
                        'date_planned': self.schedule_date or fields.Date.today(),
                        'procurement_ids': [(6, 0, [self.procurement_id.id])] if self.procurement_id else False,
                        'account_analytic_id': lines[6],
                        'order_id':poid.id,
                        'item_no':lines[9],
                    }
                    self.env['purchase.order.line'].create(order_lines)
               
            else:
                raise UserError(_("selected Vendor's RFQ alfready created.......!"))        


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    requisition_id = fields.Many2one('purchase.requisition', string='Purchase Agreement', copy=False, readonly=True)
    
    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):

        if len(self.requisition_id.vendor_id.ids)>0:

            for i in range(len(self.requisition_id.vendor_id.ids)):
                
                if not self.requisition_id:
                    return
                
                requisition = self.requisition_id
                
                if self.partner_id:
                    partner = self.partner_id
                else:
                    partner_ids = requisition.vendor_id.ids[i]
                    partner = self.env['res.partner'].browse(partner_ids)
                    
                payment_term = partner.property_supplier_payment_term_id
                currency = partner.property_purchase_currency_id or requisition.company_id.currency_id

                FiscalPosition = self.env['account.fiscal.position']
                fpos = FiscalPosition.get_fiscal_position(partner.id)
                fpos = FiscalPosition.browse(fpos)

                self.partner_id = partner.id
                self.fiscal_position_id = fpos.id
                self.payment_term_id = payment_term.id,
                self.company_id = requisition.company_id.id
                self.currency_id = currency.id
                self.origin = requisition.name
                self.partner_ref = requisition.name # to control vendor bill based on agreement reference
                self.notes = requisition.description
                self.date_order = requisition.date_end or fields.Datetime.now()
                self.picking_type_id = requisition.picking_type_id.id

                if requisition.type_id.line_copy != 'copy':
                    return

                # Create PO lines if necessary
                order_lines = []
                for line in requisition.line_ids:
                    # Compute name
                    product_lang = line.product_id.with_context({
                        'lang': partner.lang,
                        'partner_id': partner.id,
                    })
                    name = product_lang.display_name
                    if product_lang.description_purchase:
                        name += '\n' + product_lang.description_purchase

                    # Compute taxes
                    if fpos:
                        taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id))
                    else:
                        taxes_ids = line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id).ids

                    # Compute quantity and price_unit
                    if line.product_id:
                        if line.product_uom_id != line.product_id.uom_po_id:
                            product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                            price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
                        else:
                            product_qty = line.product_qty
                            price_unit = line.price_unit
                    else:
                        product_qty = line.product_qty
                        price_unit = line.price_unit

                    if requisition.type_id.quantity_copy != 'copy':
                        product_qty = 0

                    # Compute price_unit in appropriate currency
                    if requisition.company_id.currency_id != currency:
                        price_unit = requisition.company_id.currency_id.compute(price_unit, currency)
                    unit_measure = 0
                    description = ''
                    if line.product_id:
                        unit_measure = line.product_id.uom_po_id.id
                        description = name
                    else:
                        unit_measure = line.product_uom_id.id
                        description = line.description
                    # Create PO line
                    order_lines.append((0, 0, {
                        'name': description,
                        'product_id': line.product_id.id,
                        'product_category_id': line.product_category_id.id,
                        'product_uom': unit_measure,
                        'product_qty': product_qty,
                        'price_unit': price_unit,
                        'taxes_id': [(6, 0, taxes_ids)],
                        'date_planned': requisition.schedule_date or fields.Date.today(),
                        'procurement_ids': [(6, 0, [requisition.procurement_id.id])] if requisition.procurement_id else False,
                        'account_analytic_id': line.account_analytic_id.id,
                        'item_no':line.item_no,
                    }))
                self.order_line = order_lines
        else:

            if not self.requisition_id:
                return
            
            requisition = self.requisition_id
            
            if self.partner_id:
                partner = self.partner_id
            else:
                partner = requisition.vendor_id
            payment_term = partner.property_supplier_payment_term_id
            currency = partner.property_purchase_currency_id or requisition.company_id.currency_id

            FiscalPosition = self.env['account.fiscal.position']
            fpos = FiscalPosition.get_fiscal_position(partner.id)
            fpos = FiscalPosition.browse(fpos)

            self.partner_id = partner.id
            self.fiscal_position_id = fpos.id
            self.payment_term_id = payment_term.id,
            self.company_id = requisition.company_id.id
            self.currency_id = currency.id
            self.origin = requisition.name
            self.partner_ref = requisition.name # to control vendor bill based on agreement reference
            self.notes = requisition.description
            self.date_order = requisition.date_end or fields.Datetime.now()
            self.picking_type_id = requisition.picking_type_id.id

            if requisition.type_id.line_copy != 'copy':
                return

            # Create PO lines if necessary
            order_lines = []
            for line in requisition.line_ids:
                # Compute name
                product_lang = line.product_id.with_context({
                    'lang': partner.lang,
                    'partner_id': partner.id,
                })
                name = product_lang.display_name
                if product_lang.description_purchase:
                    name += '\n' + product_lang.description_purchase

                # Compute taxes
                if fpos:
                    taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id))
                else:
                    taxes_ids = line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id).ids

                # Compute quantity and price_unit
                if line.product_id:
                    if line.product_uom_id != line.product_id.uom_po_id:
                        product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                        price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
                    else:
                        product_qty = line.product_qty
                        price_unit = line.price_unit
                else:
                    product_qty = line.product_qty
                    price_unit = line.price_unit

                if requisition.type_id.quantity_copy != 'copy':
                    product_qty = 0

                # Compute price_unit in appropriate currency
                if requisition.company_id.currency_id != currency:
                    price_unit = requisition.company_id.currency_id.compute(price_unit, currency)
                unit_measure = 0
                description = ''
                if line.product_id:
                    unit_measure = line.product_id.uom_po_id.id
                    description = name
                else:
                    unit_measure = line.product_uom_id.id
                    description = line.description

                # Create PO line
                order_lines.append((0, 0, {
                    'name': description,
                    'product_id': line.product_id.id,
                    'product_category_id':line.product_category_id.id,
                    'product_uom': unit_measure,
                    'product_qty': product_qty,
                    'price_unit': price_unit,
                    'taxes_id': [(6, 0, taxes_ids)],
                    'date_planned': requisition.schedule_date or fields.Date.today(),
                    'procurement_ids': [(6, 0, [requisition.procurement_id.id])] if requisition.procurement_id else False,
                    'account_analytic_id': line.account_analytic_id.id,
                    'item_no':line.item_no,
                }))
            self.order_line = order_lines

    
