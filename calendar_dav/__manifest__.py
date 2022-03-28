# Copyright 2022 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Calendar dav",
    "summary": "Extension of the base_dav module to work better with the calendar",
    "version": "11.0.1.0.0",
    "category": "Calendar",
    "website": "https://github.com/OCA/calendar",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": True,
    "post_init_hook": "post_init_hook",
    "depends": [
        "base_dav",
        "calendar",
    ],
}
