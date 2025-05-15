from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from bs4 import BeautifulSoup


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shipment_type = fields.Char("Carrier Type")
    omega_trn_no = fields.Char("Omega TRN No.",related='company_id.vat')
    package_name = fields.Char("Package")
    package_dimension = fields.Char("Package Dimension")
    package_net = fields.Char("Net Weight")
    package_gross = fields.Char("Gross Weight")
    invoice_checklist = fields.Boolean('Invoice')
    packing_list_checklist = fields.Boolean('Packing List / Delivery Note')
    exit_bill_checklist = fields.Boolean('Bill of Exit from customs')
    certificates_checklist = fields.Boolean('Certificates / Documents mentioned in the PO')
    remarks_checklist = fields.Text('Remarks')

    def check_same(self, line):
        soup_1 = BeautifulSoup(line.description_picking, features="lxml", from_encoding="utf-8").text
        soup_2 = BeautifulSoup(line.product_id.name, features="lxml", from_encoding="utf-8").text
        if soup_2 == soup_1:
            return True
        else:
            return False

    def action_report_delivery(self):
        if not self.invoice_checklist or not self.packing_list_checklist or not self.exit_bill_checklist or not self.certificates_checklist:
            raise ValidationError("All the checklist for documents under Additional Info tab should be selected in order to print the delivery slip report.")
        return self.env.ref('stock.action_report_delivery').report_action(self)

class StockMove(models.Model):
    _inherit = 'stock.move'

    description_picking = fields.Html('Description of Picking')