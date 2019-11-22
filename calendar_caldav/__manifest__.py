# Copyright 2019 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Calendar CalDAV',
    'summary': 'Synchronize your CalDAV calendar with Odoo calendar',
    'version': '11.0.1.0.0',
    'category': 'Tools',
    'license': 'AGPL-3',
    'author': "Onestein,Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/calendar',
    'depends': [
        'calendar',
    ],
    'external_dependencies': {
        'python': [
            'caldav'
        ]
    },
    'data': [
        'security/calendar_caldav_calendar_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'templates/assets.xml',
        'views/res_users_view.xml',
        'wizards/calendar_caldav_setup_wizard_view.xml',
        'wizards/calendar_caldav_select_wizard_view.xml'
    ],
    'qweb': [
        'static/src/xml/calendar_caldav.xml',
    ],
    'installable': True,
}
