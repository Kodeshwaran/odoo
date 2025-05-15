# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hr Attendance Geolocation",
    "summary": """
        With this module the geolocation of the user is tracked at the
        check-in/check-out step""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow S.L.," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr",
    "depends": ['hr', "hr_attendance", 'hr_attendance_extended'],
    "data": [
        'security/ir.model.access.csv',
        "views/assets.xml",
        "views/res_config_settings.xml",
        "views/hr_employee.xml",
        "views/hr_attendance_views.xml",
        "data/location_data.xml",
        'wizard/attendance_report.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'hr_attendance_geolocation/static/src/js/attendance_geolocation.js'
        ]
    }
}
