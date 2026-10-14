# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Resource Booking - Google Calendar",
    "summary": "Let Google Calendar send the booking invitations when the "
    "organizer synchronizes their calendar",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "maintainers": ["JordiBForgeFlow"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": True,
    "depends": [
        "resource_booking",
        "google_calendar",
    ],
}
