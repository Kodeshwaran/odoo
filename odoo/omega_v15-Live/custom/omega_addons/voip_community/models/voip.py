from odoo import fields, models, api


class VoipPhonecall(models.Model):
    _name = "voip.phonecall"
    _description = 'VOIP Phonecall'

    _order = "sequence, id"

    name = fields.Char('Call Name', required=True)
    date_deadline = fields.Date('Due Date', default=lambda self: fields.Date.today())
    call_date = fields.Datetime('Call Date')
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.uid)
    partner_id = fields.Many2one('res.partner', 'Contact')
    activity_id = fields.Many2one('mail.activity', 'Linked Activity')
    mail_message_id = fields.Many2one('mail.message', 'Linked Chatter Message', index=True)
    note = fields.Html('Note')
    duration = fields.Float('Duration', help="Duration in minutes.")
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    in_queue = fields.Boolean('In Call Queue', default=True)
    sequence = fields.Integer('Sequence', index=True,
        help="Gives the sequence order when displaying a list of Phonecalls.")
    start_time = fields.Integer("Start time")
    state = fields.Selection([
        ('pending', 'Not Held'),
        ('cancel', 'Cancelled'),
        ('open', 'To Do'),
        ('done', 'Held'),
        ('rejected', 'Rejected'),
        ('missed',   'Missed')
    ], string='Status', default='open',
        help='The status is set to To Do, when a call is created.\n'
             'When the call is over, the status is set to Held.\n'
             'If the call is not applicable anymore, the status can be set to Cancelled.')
    phonecall_type = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing')
    ], string='Type', default='outgoing')