# Copyright 2021 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Google Calendar Hide Credentials",
    "version": "14.0.1.0.0",
    "category": "Productivity",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/calendar",
    "summary": "Hides credentials in General Settings menu" "for Google Calendar",
    "depends": ["google_calendar"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
