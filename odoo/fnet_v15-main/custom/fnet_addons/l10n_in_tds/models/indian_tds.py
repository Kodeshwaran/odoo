from odoo import models, fields, api, _


class SectionTds(models.Model):
    _name = 'section.tds'
    _description = "TDS Section Informations"

    name = fields.Char(string='Name', required=True, help="TDS Section. Ex: 194C etc.,")
    effect_date = fields.Date('Effect Date')
    nature = fields.Char(string='Nature of Payment')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('section.tds'))
    cut_off = fields.Float(string='Cut-off Value')
    acc_receivable_id = fields.Many2one('account.account', string='TDS Reversal G/L Account', required=True, company_dependent=True)
    acc_payable_id = fields.Many2one('account.account', string='TDS Payable G/L Account', required=True, company_dependent=True)
    tds_line_ids = fields.One2many('section.tds.line', 'tds_id', string="TDS Section Line")

class SectionTdsLine(models.Model):
    _name = 'section.tds.line'
    _description = "TDS Section Line Informations"

    tds_id = fields.Many2one('section.tds', string="TDS Section")
    from_dt = fields.Date(string="From Date")
    to_dt = fields.Date(string="To Date")
    company_percent = fields.Float(string='Companies %', digits=(16, 3), help="TDS rate for Companies")
    individual_percent = fields.Float(string='Individual / HUF %', digits=(16, 3), help="TDS rate for Individual / HUF")
    others_percent = fields.Float(string='No PAN %', digits=(16, 3), help="TDS rate when PAN Number is not available")

class Partner(models.Model):
    _inherit = 'res.partner'

    tds_applicable = fields.Boolean(string='TDS Applicable ?')
    tds_section_id = fields.Many2one('section.tds', string='TDS Section')
    tds_type = fields.Selection([('company', 'Company'), ('individual', 'Individual')], string='Type')
    tcs_applicable = fields.Boolean(string='TCS Applicable ?')
    tcs_section_id = fields.Many2one('section.tcs', string='TCS Section')
    tcs_type = fields.Selection([('company', 'Company'), ('individual', 'Individual')], string='Type')
    disable_tcs_warn = fields.Boolean(string='194Q Declaration')

class SectionTcs(models.Model):
    _name = 'section.tcs'
    _description = "TCS Section Informations"

    name = fields.Char(string='Name', required=True, help="TDS Section. Ex: 194C etc.,")
    tcs_percentage = fields.Float(string="TCS(%)",digits=(16, 3))
    limit_amt = fields.Float(string="Limit Amount")
    acc_receivable_id = fields.Many2one('account.account', string='TCS Reversal G/L Account', required=True)
    acc_payable_id = fields.Many2one('account.account', string='TCS Payable G/L Account', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('section.tcs'))
    starting_month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                          ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                          ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')], 
                          string='Month')
    tcs_line_ids = fields.One2many('section.tcs.line', 'tcs_id', string="TDS Section Line")


class SectionTcsLine(models.Model):
    _name = 'section.tcs.line'
    _description = "TCS Section Line Informations"

    tcs_id = fields.Many2one('section.tcs', string="TCS Section")
    from_dt = fields.Date(string="From Date")
    to_dt = fields.Date(string="To Date")
    tcs_percentage = fields.Float(string="TCS(%)",digits=(16, 3))
    limit_amt = fields.Float(string="Limit Amount")
    gst_tax_id = fields.Many2one('account.tax',string="GST")
    tcs_tax_id = fields.Many2one('account.tax',string="TCS Tax")
