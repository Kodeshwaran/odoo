{
    'name': 'Helpdesk extended',
    'version': '1.0',
    'category': 'Ticket Generator',
    'summary': 'Helpdesk Extended',
    'description': """Ticket Generator""",
    'depends': ['helpdesk'],
    'data': [
             'views/ticket_view.xml',
             'data/ticket_sequence.xml',
             'data/ticket_templates.xml',
             ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OEEL-1',
}
