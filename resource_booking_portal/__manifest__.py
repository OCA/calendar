# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "resource_booking_portal",
    "summary": """
        This addons allow create booking from portal.
    """,
    "author": "Odoo Community Association (OCA), Binhex",
    "website": "https://github.com/OCA/calendar",
    "maintainers": ["adasatorres"],
    "category": "portal",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "resource_booking",
    ],
    "data": [
        "views/portal_templates.xml",
        "views/res_users_views.xml",
        "wizard/portal_wizard_views.xml",
    ],
}
