# Copyright 2019 ACSONE SA/NV
# Copyright 2024 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Calendar Event Link To Stock picking",
    "summary": """
        This module add a link between stock pickings and calendar events""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "INVITU," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/calendar",
    "depends": ["stock", "calendar_event_link_base"],
    "data": ["views/stock_picking_views.xml"],
    "demo": [],
}
