# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Website Appointment Booking",
    "summary": "Public appointment booking pages for resource booking types",
    "version": "20.0.1.0.0",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "Ledo Enterprises LLC, ForgeFlow, Odoo Community Association (OCA)",
    "maintainers": ["dnplkndll"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "resource_booking",
        "website",
    ],
    "data": [
        "templates/booking.xml",
        "views/resource_booking_type_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_appointment_booking/static/src/scss/booking.scss",
            "website_appointment_booking/static/src/js/form_guard.esm.js",
            "website_appointment_booking/static/src/js/booking_page.esm.js",
        ],
    },
}
