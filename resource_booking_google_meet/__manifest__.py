# Copyright 2026 Ledo Enterprises - D. Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Resource Booking — Google Meet by default",
    "version": "18.0.1.0.0",
    "category": "Marketing/Online Appointment",
    "summary": "Default new resource bookings to Google Meet for the videocall",
    "author": "Ledo Enterprises, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/calendar",
    "license": "AGPL-3",
    "depends": ["resource_booking", "google_calendar"],
    "data": ["data/mail_template_meet_link.xml"],
    "installable": True,
    "auto_install": False,
    "maintainers": ["dnplkndll"],
}
