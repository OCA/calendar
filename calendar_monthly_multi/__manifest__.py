{
    "name": "Calendar Monthly Extension",
    "version": "16.0.1.0.0",
    "category": "Productivity/Calendar",
    "license": "AGPL-3",
    "author": "Onestein,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/calendar",
    "depends": ["calendar"],
    "data": [
        "security/ir_model_access.xml",
        "data/calendar_recurrence_day_data.xml",
        "data/calendar_recurrence_weekday_data.xml",
        "views/calendar_event_view.xml",
    ],
    "assets": {
        "web.assets_backend": ["calendar_monthly_multi/static/src/scss/backend.scss"]
    },
}
