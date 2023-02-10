# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Resource Booking Remove Default Filter",
    "summary": """
        Remove the 'Involving me' filter as default filter when viewing resource bookings.""",
    "version": "14.0.1.0.0",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "maintainers": ["carmenbianca"],
    "license": "AGPL-3",
    "application": False,
    "depends": [
        "resource_booking",
    ],
    "excludes": [],
    "data": [
        "views/resource_booking_views.xml",
    ],
    "demo": [],
    "qweb": [],
}
