# -*- coding: utf-8 -*-
{
    'name': 'Farming',
    'version': '15.1',
    'category': 'Farming',
    'author': 'Farming',
    'description': """
       """,
    'depends': [],
    'installable': True,
    'auto_install': False,
    'data' : [  ],
     "author": "LasLabs, Tecnativa, ITerra, " "Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["web", "mail"],
    "development_status": "Production/Stable",
    "maintainers": ["Yajo", "Tardo", "SplashS"],
    "excludes": ["web_enterprise"],
    "data": ["views/res_users.xml", "views/web.xml"],
    "assets": {
        "web.assets_frontend": [
            "/web_responsive/static/src/legacy/js/website_apps_menu.js",
            "/web_responsive/static/src/legacy/scss/website_apps_menu.scss",
        ],
        "web.assets_backend": [
            "/web_responsive/static/src/legacy/scss/web_responsive.scss",
            "/web_responsive/static/src/legacy/js/web_responsive.js",
            "/web_responsive/static/src/legacy/scss/kanban_view_mobile.scss",
            "/web_responsive/static/src/legacy/js/kanban_renderer_mobile.js",
            "/web_responsive/static/src/components/ui_context.esm.js",
            "/web_responsive/static/src/components/apps_menu/apps_menu.scss",
            "/web_responsive/static/src/components/apps_menu/apps_menu.esm.js",
            "/web_responsive/static/src/components/navbar/main_navbar.scss",
            "/web_responsive/static/src/components/control_panel/control_panel.scss",
            "/web_responsive/static/src/components/control_panel/control_panel.esm.js",
            "/web_responsive/static/src/components/search_panel/search_panel.scss",
            "/web_responsive/static/src/components/search_panel/search_panel.esm.js",
            "/web_responsive/static/src/components/attachment_viewer/attachment_viewer.scss",
            "/web_responsive/static/src/components/attachment_viewer/attachment_viewer.esm.js",
            "/web_responsive/static/src/components/hotkey/hotkey.scss",
        ],
}


































