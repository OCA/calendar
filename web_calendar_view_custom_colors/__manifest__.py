# © 2019 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Calendar View Configuration',
    'version': '11.0.1.0.0',
    'author': 'Savoir-faire Linux, Odoo Community Association (OCA)',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'license': 'LGPL-3',
    'category': 'Calendar',
    'summary': 'Calendar View Colors Configuration',
    'depends': [
        'base',
        'calendar',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'views/calendar_view_config_view.xml',
        'templates/assets.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
