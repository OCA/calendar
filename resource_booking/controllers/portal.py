# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from urllib.parse import quote_plus

from dateutil.parser import isoparse

from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request, route
from odoo.tests.common import Form

from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    def _get_booking_sudo(self, booking_id, access_token):
        """Get sudoed booking record from its ID."""
        booking_sudo = self._document_check_access(
            "resource.booking", booking_id, access_token
        )
        return booking_sudo.with_context(
            using_portal=True, tz=booking_sudo.type_id.resource_calendar_id.tz
        )

    def _prepare_portal_layout_values(self):
        """Compute values for multi-booking portal views."""
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        booking_count = request.env["resource.booking"].search_count([])
        values.update({"booking_count": booking_count})
        return values

    def _booking_get_page_view_values(self, booking_sudo, access_token, **kwargs):
        """Compute values for single-booking portal views."""
        return self._get_page_view_values(
            booking_sudo,
            access_token,
            {"page_name": "booking", "booking_sudo": booking_sudo},
            "my_bookings_history",
            False,
            **kwargs
        )

    @route(
        ["/my/bookings", "/my/bookings/page/<int:page>"],
        auth="user",
        type="http",
        website=True,
    )
    def portal_my_bookings(self, page=1, **kwargs):
        """List bookings that I can access."""
        Booking = request.env["resource.booking"].with_context(using_portal=True)
        values = self._prepare_portal_layout_values()
        pager = portal.pager(
            url="/my/bookings",
            total=values["booking_count"],
            page=page,
            step=self._items_per_page,
        )
        bookings = Booking.search(
            [], limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_bookings_history"] = bookings.ids
        values.update({"bookings": bookings, "pager": pager, "page_name": "bookings"})
        return request.render("resource_booking.portal_my_bookings", values)

    @route(["/my/bookings/<int:booking_id>"], type="http", auth="public", website=True)
    def portal_booking_page(self, booking_id, access_token=None, **kwargs):
        """Portal booking form."""
        try:
            booking_sudo = self._get_booking_sudo(booking_id, access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")
        # ensure attachment are accessible with access token inside template
        for attachment in booking_sudo.mapped("message_ids.attachment_ids"):
            attachment.generate_access_token()
        values = self._booking_get_page_view_values(
            booking_sudo, access_token, **kwargs
        )
        return request.render("resource_booking.resource_booking_portal_form", values)

    @route(
        [
            "/my/bookings/<int:booking_id>/schedule",
            "/my/bookings/<int:booking_id>/schedule/<int:year>/<int:month>",
        ],
        auth="public",
        type="http",
        website=True,
    )
    def portal_booking_schedule(
        self, booking_id, access_token=None, year=None, month=None, error=None, **kwargs
    ):
        """Portal booking scheduling."""
        try:
            booking_sudo = self._get_booking_sudo(booking_id, access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")
        values = self._booking_get_page_view_values(
            booking_sudo, access_token, **kwargs
        )
        values.update(booking_sudo._get_calendar_context(year, month))
        values.update({"error": error, "page_name": "booking_schedule"})
        return request.render(
            "resource_booking.resource_booking_portal_schedule", values
        )

    @route(
        ["/my/bookings/<int:booking_id>/cancel"],
        auth="public",
        type="http",
        website=True,
    )
    def portal_booking_cancel(self, booking_id, access_token=None, **kwargs):
        """Cancel the booking."""
        booking_sudo = self._get_booking_sudo(booking_id, access_token)
        booking_sudo.action_cancel()
        return request.redirect("/my")

    @route(
        ["/my/bookings/<int:booking_id>/confirm"],
        auth="public",
        type="http",
        website=True,
    )
    def portal_booking_confirm(self, booking_id, access_token, when, **kwargs):
        """Confirm a booking in a given datetime."""
        booking_sudo = self._get_booking_sudo(booking_id, access_token).with_context(
            autoconfirm_booking_requester=True
        )
        when_tz_aware = isoparse(when)
        when_naive = datetime.utcfromtimestamp(when_tz_aware.timestamp())
        try:
            with Form(booking_sudo) as booking_form:
                booking_form.start = when_naive
        except ValidationError as error:
            url = booking_sudo.get_portal_url(
                suffix="/schedule/{:%Y/%m}".format(when_tz_aware),
                query_string="&error={}".format(quote_plus(error.name)),
            )
            return request.redirect(url)
        booking_sudo.action_confirm()
        return request.redirect(booking_sudo.get_portal_url())
