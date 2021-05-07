# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Resource Planning',
    'version': '12.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Plan resources allocation and utilization analysis',
    'author':
        'Brainbean Apps, '
        'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'depends': [
        'base_setup',
        'mail',
        'calendar',
        'resource',
    ],
    'data': [
        'security/resource_planning.xml',
        'security/ir.model.access.csv',
        'views/resource_planning.xml',
        'views/resource_planning_line.xml',
        'views/resource_planning_plan.xml',
        'views/res_config_settings.xml',
    ],
}
