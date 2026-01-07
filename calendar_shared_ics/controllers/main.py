# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.http import Controller, content_disposition, request, route


class CalendarSharedIcsController(Controller):
    @route(
        ["/calendar/shared/<model('calendar.shared.ics'):shared>/ics"],
        type="http",
        auth="public",
        csrf=False,
        sitemap=False,
    )
    def calendar_shared_ics(self, shared, **kwargs):
        # super minimal, all the actual work
        # takes place in calendar.shared.ics
        shared = shared.sudo()
        if not shared.exists() or not shared.active:
            return request.not_found()
        if not shared._check_access_token(kwargs.get("access_token")):
            return request.not_found()
        try:
            content = shared._render_ics_content()
        except Exception:
            return request.not_found()
        filename = shared._get_ics_filename()
        return request.make_response(
            content,
            [
                ("Content-Type", "text/calendar; charset=utf-8"),
                ("Content-Disposition", content_disposition(filename)),
                ("Cache-Control", "no-store"),
            ],
        )
