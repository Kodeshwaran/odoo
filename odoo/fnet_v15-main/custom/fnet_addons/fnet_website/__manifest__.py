
{
    'name': 'Futurenet Website',
    'summary': """Futurenet Website""",
    'version': '15.0.1.0.0',
    'description': """Futurenet Website""",
    'author': 'Harideevagan M',
    'company': 'Futurenet',
    'website': 'https://www.futurenet.in',
    'category': 'Website',
    'depends': ['base', 'mail', 'website'],
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/home_page.xml',
        'views/contact_us.xml',
        'views/footer.xml',
    ],
    'images': ['static/description/wsicon.png'],
    'installable': True,
    'auto_install': False,
}

