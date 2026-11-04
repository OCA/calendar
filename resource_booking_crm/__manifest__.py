# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Resource Booking - CRM",
    "summary": "Create CRM leads or opportunities from scheduled bookings",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "maintainers": ["JordiBForgeFlow"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["resource_booking", "crm"],
    "data": [
        "views/resource_booking_type_views.xml",
        "views/resource_booking_views.xml",
        "views/crm_lead_views.xml",
    ],
}
