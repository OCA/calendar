# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Resource booking",
    "summary": "Manage appointments and resource booking",
    "version": "13.0.2.4.0",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["Yajo"],
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    "external_dependencies": {
        "python": [
            # Used implicitly
            "cssselect",
            # Only for tests
            "freezegun",
        ],
    },
    "depends": [
        "calendar",
        "mail",
        "portal",
        "resource",
        "web_calendar_slot_duration",
    ],
    "data": [
        "data/mail.xml",
        "security/resource_booking_security.xml",
        "security/ir.model.access.csv",
        "templates/assets.xml",
        "templates/portal.xml",
        "views/calendar_event_views.xml",
        "views/resource_booking_combination_views.xml",
        "views/resource_booking_type_views.xml",
        "views/resource_booking_views.xml",
        "views/menus.xml",
    ],
    "demo": ["demo/res_users_demo.xml"],
}
