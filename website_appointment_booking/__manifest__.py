# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Website Appointment Booking",
    "summary": "Public appointment booking pages for resource booking types",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "Ledo Enterprises LLC, Odoo Community Association (OCA)",
    "maintainers": ["dnplkndll"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "resource_booking",
        "website",
        "crm",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_templates.xml",
        "templates/booking.xml",
        "views/resource_booking_type_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_appointment_booking/static/src/scss/booking.scss",
            "website_appointment_booking/static/src/js/booking_page.esm.js",
        ],
    },
}
