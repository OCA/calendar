# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Resource Category Booking",
    "summary": "Glue module between resource category and resource booking",
    "version": "14.0.1.0.0",
    "category": "Hidden",
    "website": "https://github.com/OCA/calendar",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "resource_category",
        "resource_booking",
    ],
    "auto_install": True,
    "data": [
        "security/ir.model.access.csv",
        "views/menus.xml",
    ],
}
