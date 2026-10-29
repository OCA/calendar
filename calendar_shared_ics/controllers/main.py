# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging

from odoo.http import Controller, content_disposition, request, route

_logger = logging.getLogger(__name__)


class CalendarSharedIcsController(Controller):
    @route(
        ["/calendar/shared/<int:shared_id>/ics"],
        type="http",
        auth="public",
        csrf=False,
        sitemap=False,
    )
    def calendar_shared_ics(self, shared_id, **kwargs):
        # super minimal, all the actual work
        # takes place in calendar.shared.ics
        shared = request.env["calendar.shared.ics"].sudo().browse(shared_id)
        if not shared.exists() or not shared.active:
            raise request.not_found()
        if not shared._check_access_token(kwargs.get("access_token")):
            raise request.not_found()
        try:
            content = shared._render_ics_content()
        except Exception:
            _logger.exception("Failed to render shared ICS feed %s", shared.id)
            raise request.not_found() from None
        filename = shared._get_ics_filename()
        return request.make_response(
            content,
            [
                ("Content-Type", "text/calendar; charset=utf-8"),
                ("Content-Disposition", content_disposition(filename)),
                ("Cache-Control", "no-store"),
            ],
        )

    @route(
        ["/calendar/shared/<int:shared_id>/landing"],
        type="http",
        auth="public",
        csrf=False,
        sitemap=False,
    )
    def calendar_shared_ics_landing(self, shared_id, **kwargs):
        # Public landing page: user can copy/paste the https/webcal subscription URL.
        # and also login in the backend, if internal
        shared = request.env["calendar.shared.ics"].sudo().browse(shared_id)
        if not shared.exists() or not shared.active:
            raise request.not_found()
        if not shared._check_access_token(kwargs.get("access_token")):
            raise request.not_found()
        shared._portal_ensure_token()
        backend_url = (
            f"{shared.get_base_url()}/web#id={shared.id}"
            f"&model={shared._name}&view_type=form"
        )
        return request.render(
            "calendar_shared_ics.shared_ics_landing_page",
            {
                "shared": shared,
                "ics_url": shared.share_url,
                "webcal_url": shared.share_webcal_url,
                "backend_url": backend_url,
            },
        )
