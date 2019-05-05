# -*- coding: utf-8 -*-
# Copyright 2019 Luis Iñiguez
# License AGPL-3.0 (https://www.gnu.org/licenses/agpl).
{
    "name": "Calendar DST bug fix",
    'summary': """This fix displays recurring calendar events correctly
                  after DST change""",
    "version": "10.0.1.0.0",
    "development_status": "Production",
    "category": "Extra Tools",
    "website": "https://github.com/OCA/calendar",
    "author": "Luis Iñiguez, Odoo Community Association (OCA)",
    "maintainers": ["luisiniguezh"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "preloadable": True,
    "depends": [
        "calendar",
    ],
}
