from odoo import models, fields, api, _


class EmployeeAllowance(models.Model):
    _name = 'employee.allowance'

    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company, readonly=True)
    month = fields.Selection([('Jan', 'January'), ('Feb', 'February'),('Mar', 'March'),
                                          ('Apr', 'April'),('May', 'May'),('Jun', 'June'),
                                          ('Jul', 'July'),('Aug', 'August'),('Sep', 'September'),
                                          ('Oct', 'October'),('Nov', 'November'),('Dec', 'December')], string="Month")
    check = fields.Boolean(string='Check the box before updating', help='set the field to True after submit button is clicked')
    employee_details = fields.One2many('employee.details', 'allowance_id', string='Employees Details')
    state = fields.Selection([('draft', 'Draft'), ('updated', 'Updated'), ('closed', 'Closed')], default="draft")

    @api.depends('employee_details')
    def get_update(self):
        self.write({'state': 'updated'})
        for rec in self.employee_details:
            if rec.employee_id and rec.employee_id.contract_id:
                rec.employee_id.contract_id.mobile_deduction = rec.mbl_ded
                rec.employee_id.contract_id.ot_allowance = rec.ot_all
                rec.employee_id.contract_id.tds = rec.tds
                rec.employee_id.contract_id.other_deduction = rec.other_ded
                rec.employee_id.contract_id.arrears = rec.arrears
                rec.employee_id.contract_id.pt = rec.pt

    def action_close(self):
        self.write({'state': 'closed'})
        for rec in self.employee_details:
            if rec.employee_id and rec.employee_id.contract_id:
                rec.employee_id.contract_id.mobile_deduction = 0
                rec.employee_id.contract_id.ot_allowance = 0
                rec.employee_id.contract_id.tds = 0
                rec.employee_id.contract_id.other_deduction = 0
                rec.employee_id.contract_id.arrears = 0
                rec.employee_id.contract_id.pt = 0

class EmployeeDetails(models.Model):
    _name = 'employee.details'

    allowance_id = fields.Many2one('employee.allowance', string="Allowance Id")
    employee_id = fields.Many2one('hr.employee', string="Employee Name")
    mbl_ded = fields.Float(string="Mobile Deduction", digits=(16, 5))
    ot_all = fields.Float(string="OT Allowance", digits=(16, 5))
    tds = fields.Float(string="TDS", digits=(16, 5))
    other_ded = fields.Float(string="Other Deduction", digits=(16, 5))
    arrears = fields.Float(string="Arrears", digits=(16, 5))
    pt = fields.Float(string="PT", digits=(16, 5))