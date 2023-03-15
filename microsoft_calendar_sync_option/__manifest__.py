# Copyright 2023 Le Filament
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Outlook Calendar Sync Option",
    "summary": "Manage options for Outlook calendar synchronization",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Productivity",
    "website": "https://github.com/OCA/calendar",
    "author": "Le Filament, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    "external_dependencies": {},
    "depends": ["calendar", "microsoft_calendar"],
    "data": ["views/res_config_settings_views.xml"],
    "demo": [],
}
