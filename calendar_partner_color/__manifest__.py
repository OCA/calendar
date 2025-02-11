# Copyright (C) 2021 Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Calendar Partner Color",
    "summary": "Adapt calendar color based on partner's color",
    "version": "16.0.0.1.0",
    "category": "Calendar",
    "website": "https://github.com/OCA/calendar",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["calendar"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "calendar_partner_color/static/src/views/**/*",
        ],
    },
    "excludes": ["calendar_event_type_color"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["hparfr"],
    "pre_init_hook": "pre_init_hook",
}
