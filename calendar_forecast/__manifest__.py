# -*- coding: utf-8 -*-

{
    "name": "Calendar Project Task Schedulable",
    "version": "12.0.0.0.1",
    "category": "Calendar",
    "summary": "Module to allow scheduling project tasks",
    "description": "",
    "website": "https://github.com/oca/calendar",
    "depends": [
        "hr_timesheet",
        "web_widget_x2many_2d_matrix",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/calendar_forecast_views.xml",
    ],
    "installable": True,
    "application": False,
}
