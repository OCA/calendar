# Copyright (C) 2021 Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Calendar Partner Color",
    "summary": "Adapt calendar color based on partner's color",
    "version": "14.0.0.1.0",
    "category": "Calendar",
    "website": "https://github.com/OCA/calendar",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["calendar", "web_calendar_color_field"],
    "data": [
        "views/calendar_event.xml",
        "views/partner.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["hparfr"],
    "pre_init_hook": "pre_init_hook",
}
