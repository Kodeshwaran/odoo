from odoo import models, fields, api, _
from datetime import date
from datetime import datetime
import odoo.addons.decimal_precision as dp


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    def _date_compute(self):
        for record in self:
            if record.date_join:
                current_date = fields.Date.today()
                date1 = datetime.strptime(str(record.date_join), '%Y-%m-%d')
                date2 = datetime.strptime(str(current_date), '%Y-%m-%d')
                total_months = (date2.year - date1.year) * 12 + date2.month - date1.month
                record.experience_current_company = total_months
            else:
                record.experience_current_company = 1

    employee_id = fields.Char(string="Test")
    date_probation = fields.Date('Probation End Date')
    date_join = fields.Date("Joining Date")
    city = fields.Char("City")
    pf_number = fields.Char("PF Number")
    uan_number = fields.Char("PF UAN Number")
    aadhar_number = fields.Char("Aadhar Number")
    pan_number = fields.Char("Pan Number")
    confirm_date = fields.Date("Confirmation Date")
    esi_number = fields.Char("ESI Number")
    experience_previous_company = fields.Integer("Previous Experience")
    experience_current_company = fields.Integer("Experience in current Company", readonly=False, compute='_date_compute')
    original_dob = fields.Date(string="Original DOB")
    wedding_anniversary = fields.Date(string="Wedding Anniversary date")
    children_name = fields.Char(string="Children1 Name")
    children_dob = fields.Date(string="Children1 DOB")
    children2_name = fields.Char(string="Children2 Name")
    children2_dob = fields.Date(string="Children2 DOB")
    employeeid = fields.Char(string="Employee ID", required=True, default=lambda self: _('New'), copy=False)
    notes = fields.Text()
    manager = fields.Boolean(string="Is a Manager")
    mode_of_pay = fields.Selection(string="Mode of Payment", selection=[("cash", "Cash"), ("bank", "Bank")])
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account Number")
    company_id = fields.Many2one('res.company', string="Company")
    ins_policy_renewal = fields.Date(string="Insurance Policy Renewal Date")
    remaining_leaves = fields.Float(string='Remaining Legal Leaves',
                                    help='Total number of legal leaves allocated to this employee, change this value to create allocation/leave request. Total based on all the leave types without overriding limit')
    medical_exam = fields.Date(string="Medical Exam")
    employee_categ = fields.Selection([('employee', 'Employee'), ('intern', 'Internship'), ('consultant', 'Consultant')], default='employee',
                                      string="Employee Type")

    # @api.model
    # def create(self, vals):
    #     if vals.get('employeeid', _('New')) == _('New'):
    #         vals['employeeid'] = self.env['ir.sequence'].next_by_code('employee.id') or _('New')
    #     return super(HrEmployeeBase, self).create(vals)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # Allowances
    salary_arrears = fields.Float("Salary Arrears")
    ot_allowance = fields.Float(string="OT")
    data_card_alw = fields.Float(string="Data Card")
    bonus = fields.Float(string="Bonus")
    is_bonus = fields.Boolean(string="Is Bonus")
    is_conveyance = fields.Boolean(string="Is Conveyance")
    conveyance = fields.Float(string="Conveyance")
    earning_alw = fields.Float(string="Earned Allowance")
    basic_percentage = fields.Float(string="Basic", digits=dp.get_precision('Payment Terms'))
    is_hra = fields.Boolean(string="Is HRA")
    is_travel_added = fields.Boolean(string="Is TA Not in Basic")
    is_other = fields.Boolean(string="Is Other")
    other_allowance = fields.Float(string="Other Allowance")
    consolidate_pay = fields.Float(string="Consolidate Pay")
    # Deductions
    is_esi = fields.Boolean(string="IS ESI")
    is_pf = fields.Boolean(string="IS PF")
    pt = fields.Float(string="PT")
    tds = fields.Float(string="TDS")
    other_deduction = fields.Float(string="Other Deduction")
    mobile_deduction = fields.Float(string="Mobile Deduction")
    advance_salary = fields.Float(string="Advance Salary")
    is_new_emp = fields.Boolean(string="Is New")
    new_employee = fields.Float(string="Worked days for New Employee")
    is_medical = fields.Boolean(string="Is Medical")
    medical = fields.Float(string="Medical")
    arrears = fields.Float(string="Arrears")
    is_arrear = fields.Boolean(string="Is Salary Revised")
    non_cash = fields.Float(string="Non Cash Component")

    @api.model
    def _contract_expiry(self):
        contracts = self.env['hr.contract'].search([('date_end', '<', fields.Date.to_string(date.today())), ('state', '=', 'open')])
        if contracts:
          for contract in contracts:
              contract.update({
                  'state': 'close',
              })

    def assign_open_contract_all(self):
        vals = self.search([])
        for val in vals:
            val._assign_open_contract()


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee'

    date_probation = fields.Date('Probation End Date')


class TableCreation(models.Model):
    _name = 'table.creation'
