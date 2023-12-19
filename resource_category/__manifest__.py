# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

{
    "name": "Resource Category",
    "summary": "Add categories to resources",
    "version": "14.0.1.0.0",
    "category": "Generic Modules",
    "website": "https://github.com/OCA/calendar",
    "author": "Coop IT Easy SC, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "resource",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/resource_category_view.xml",
        "views/resource_resource_view.xml",
    ],
}
