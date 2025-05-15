from odoo import api, fields, models,tools



class CompanyMeeting(models.Model):
    _name = "company.meeting"
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "company meeting"
    _rec_name='employee_id'



    employee_id=fields.Many2one("company.employee",string='employee_id ',tracking=True)
    office_lines_ids=fields.One2many('meeting.office.lines', 'employee_id'
                                     ,string='office lines')
    hide_sales_price = fields.Boolean(string='Hide sales price')

    @api.model
    def create(self, vals):
        vals['ref'] = self.env['ir.sequence'].next_by_code('company.meeting')
        return super(CompanyMeeting, self).create(vals)

    def write(self, vals):
        if not self.ref and not vals.get('ref'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('company.meeting')
        return super(CompanyMeeting, self).create(vals)



    ref=fields.Char(string='Reference',help="Reference for employee")
    prescription=fields.Html(string='prescription')
    gender=fields.Selection(string='Gender',related='employee_id.gender',readonly=False)
    meeting_time=fields.Datetime(string="Meeting_Time",default=fields.Datetime.now)
    attented_date=fields.Date(string="Meeting_Date",default=fields.Date.context_today)
    priority=fields.Selection([
        ('0','Normal'),
        ('1', 'low'),
        ('2','high'),
        ('3','very high')

    ],string="priority")
    state=fields.Selection([
        ('draft', 'Draft'),
        ('in_consultation', 'in_consultation'),
        ('done', 'Done'),
        ('cancel', 'cancel')
    ] ,default='draft',required=True)
    manager_id=fields.Many2one('res.users',string='Manager')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.ref = self.employee_id.ref

    def action_test(self):
        print("Button clicked...........!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    def action_test(self):
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Clicked SuccessFully',
                'type': 'rainbow_man',
            }
        }
    def action_in_consultation(self):
        for rec in self:
            rec.state = 'in_consultation'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

class Meetingofficeline(models.Model):
    _name = "meeting.office.lines"
    _description = "appointment fo product"

    product_id=fields.Many2one('product.product',required=True)
    price_unit=fields.Float(string='Price',related='product_id.list_price')
    qty=fields.Integer(string='Quantity',default='1')
    employee_id=fields.Many2one('company.meeting',string='Meeting')