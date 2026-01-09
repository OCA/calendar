# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
{
    "name": "Shared ICS calendars (token-protected)",
    "version": "16.0.1.0.0",
    "category": "Calendar",
    "summary": "Share readonly calendar feeds via ICS with access tokens",
    "license": "AGPL-3",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/calendar",
    "depends": ["calendar", "portal", "mail"],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/calendar_shared_ics_views.xml",
        "views/landing_page.xml",
    ],
    "installable": True,
    "application": False,
    "external_dependencies": {"python": ["vobject"]},
    "maintainers": ["ntsirintanis"],
}
