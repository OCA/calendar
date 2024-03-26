# Copyright 2021 Tecnativa - Jairo Llopis
# Copyright 2022 Tecnativa - Pedro M. Baeza
# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Resource booking",
    "summary": "Manage appointments and resource booking",
    "version": "16.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["pedrobaeza", "ows-cloud"],
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    "uninstall_hook": "uninstall_hook",
    "external_dependencies": {
        "python": [
            # Used implicitly
            "cssselect",
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
        "data/mail_data.xml",
        "security/resource_booking_security.xml",
        "security/ir.model.access.csv",
        "templates/portal.xml",
        "views/calendar_event_views.xml",
        "views/mail_activity_views.xml",
        "views/res_partner_views.xml",
        "views/resource_booking_combination_views.xml",
        "views/resource_booking_type_views.xml",
        "views/resource_booking_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "resource_booking/static/src/js/booking_portal.js",
            "resource_booking/static/src/scss/portal.scss",
        ],
        "web.assets_tests": [
            "resource_booking/static/src/js/tours/resource_booking_tour.js"
        ],
    },
    "demo": ["demo/res_users_demo.xml"],
}
