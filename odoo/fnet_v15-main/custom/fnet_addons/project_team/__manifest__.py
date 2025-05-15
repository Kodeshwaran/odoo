# See LICENSE file for full copyright and licensing details.

{
    'name': 'Project - Set Team and members',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Project Team Management',
    'category': 'Project Management',
    'website': 'http://www.serpentcs.com',
    'version': '15.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'project',
        'crm',
        'mm_crm',
        'project_extended',
        'sale',
    ],
    'data': [
        'security/project_security.xml',
        'security/ir.model.access.csv',
        'views/project_team_view.xml',
    ],
    'images': [
        'static/description/ProjectTeam.png',
    ],
    'installable': True,
}
