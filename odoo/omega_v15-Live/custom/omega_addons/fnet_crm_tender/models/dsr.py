from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from pytz import timezone


class VoipPhonecall(models.Model):
    _inherit = "voip.phonecall"

    outcome = fields.Selection([
        ('New Prospect', 'New Prospect'),
        ('Existing Prospect', 'Existing Prospect'),
        ('Suspect', 'Suspect'),
        ('follow', 'Follow-Up'),
        ('nil', 'NIL'),
        ('others', 'Others'),
    ], string='Outcome', default='New Prospect')
    product = fields.Char('Product')
    contact_name = fields.Char('Customer Name')
    value = fields.Float('Value')
    note = fields.Text('Note')
    call_date = fields.Date('Call Date', default=lambda self: fields.Date.today())
    phonecall_type = fields.Selection([
        ('Inside Sale', 'Inside Sale'),
        ('Outside Sale', 'Outside Sale'),
        ('Tender Related', 'Tender Related'),
        ('Proposal', 'Proposal'),
        ('Payment Followup', 'Payment Followup'),
        ('Internal Meeting', 'Internal Meeting'),
        ('Others', 'Others'),
    ], string='Type', default='Outside Sale')
    phonecall_types = fields.Selection([
        ('Inside Sale', 'Inside Sale - New'),
        ('Inside Sales_Existing', 'Inside Sales - Existing'),
        ('Outside Sale', 'Outside Sale - New'),
        ('Outside Sales_Existing', 'Outside Sales - Existing'),
        ('Tender Related', 'Tender Related'),
        ('Proposal', 'Proposal'),
        ('Payment Followup', 'Payment Followup'),
        ('Internal Meeting', 'Internal Meeting'),
        ('Others', 'Others'),
    ], string='Type', default='Outside Sale')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('voip.phonecall') or 'New'
        result = super(VoipPhonecall, self).create(vals)
        return result

    @api.constrains('call_date')
    def check_call_date_new(self):
        print('\n------------', 11111111111111, '-------11111111111111--------')
        today_date = fields.Date.today()
        # current_time = fields.Datetime.now().hour
        print('\n------------', today_date, '-------today_date--------')
        utc_now = fields.Datetime.now()
        ist_tz = timezone('Asia/Kolkata')
        ist_now = utc_now.astimezone(ist_tz)

        # Get the IST hour
        ist_hour = ist_now.hour
        print('\n------------', ist_hour, '-------current_time--------')
        for record in self:
            if record.call_date and today_date > record.call_date and ist_hour >= 11:
                print('\n------------', today_date > record.call_date, '-------today_date > record.call_date--------')
                raise ValidationError(_('Incorrect call date: The call date must be later than today at 11 AM.'))
