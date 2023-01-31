# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Resource Booking Combination Auto Create",
    "summary": "Create bookable resource combinations automatically",
    "version": "14.0.1.0.0",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "multi_step_wizard",
        "resource_booking",
        "resource_category",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/resource_booking_combination_wizard_view.xml",
        "views/resource_booking_view.xml",
    ],
}
