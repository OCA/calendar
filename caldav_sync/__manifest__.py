#    Bemade Inc.
#
#    Copyright (C) 2023-June Bemade Inc. (<https://www.bemade.org>).
#    Author: Marc Durepos (Contact : mdurepos@durpro.com)
#
#    This program is under the terms of the GNU Lesser General Public License (LGPL-3)
#    For details, visit https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    "name": "CalDAV Synchronization",
    "version": "17.0.0.8.2",
    "license": "LGPL-3",
    "category": "Productivity",
    "summary": "Synchronize Odoo Calendar Events with CalDAV Servers",
    "author": "Bemade Inc., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/calendar",
    "depends": ["base", "calendar"],
    "development_status": "Beta",
    # caldav > 2.0.1 is not compatible with Odoo 18.0 due to new dependencies introduced
    "external_dependencies": {
        "python": ["caldav>=1.3.9,<=2.0.1", "icalendar", "markdownify", "markdown2"],
    },
    "images": ["static/description/images/main_screenshot.png"],
    "data": [
        "views/res_users_views.xml",
        "data/ir_cron_data.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
