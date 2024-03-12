# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Calendar - Import ics",
    "summary": "Allow importing an ics file to our calendar",
    "version": "15.0.1.0.1",
    "author": "ForgeFlow S.L.,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/calendar",
    "license": "AGPL-3",
    "depends": ["calendar"],
    "data": [
        "security/calendar_import_security.xml",
        "security/ir.model.access.csv",
        "wizards/wizard_import_ics.xml",
    ],
}
