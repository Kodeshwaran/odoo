# -*- coding: utf-8 -*-
{
    'name': "Project Extended",
    'summary': """This module includes extended features of project, task and timesheet modules.""",
    'description': """This module includes extended features of project, task and timesheet modules.""",
    'author': "Futurenet",
    'website': "http://www.futurenet.in",
    'category': 'Project',
    'version': '15.0.1',
        'depends': ['project', 'sale', 'sale_timesheet', 'mm_master', 'crm', 'product','mm_sale','mail','pre_sale', 'sale_crm', 'mm_crm', 'partner_creation'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/security_rule.xml',
        'data/sequence.xml',
        'data/cron.xml',
        'data/mail_template.xml',
        'views/res_configuration_views.xml',
        'views/project_views.xml',
        'views/timesheet_views.xml',
        'wizards/commitment_date_wizard.xml',
        'wizards/assign_manager_wizard.xml',
        'wizards/scope_document_wizard.xml',
    ],
}
