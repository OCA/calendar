# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Calendar Public Holidays on Working Schedules",
    "summary": "Generate global time off from public holidays so that the "
    "standard working schedule computations take them into account",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "category": "HR/Calendar",
    "author": "glueckkanja AG, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/calendar",
    "depends": ["calendar_public_holiday", "resource"],
    "demo": [
        "demo/calendar_public_holiday_demo.xml",
    ],
    "data": [
        "data/ir_cron.xml",
        "views/resource_calendar_views.xml",
        "views/resource_calendar_leaves_views.xml",
        "views/calendar_public_holiday_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
