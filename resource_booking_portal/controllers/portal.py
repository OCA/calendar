# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    @route(
        ["/my/bookings/prepare/form"],
        auth="user",
        type="http",
        website=True,
    )
    def portal_bookings_prepare_form(self):
        values = {
            "page_name": "create_booking",
            "types": request.env["resource.booking.type"]
            .sudo()
            .search_read([], ["id", "name"]),
        }
        return request.render("resource_booking_portal.booking_create_form", values)

    @route(
        ["/my/bookings/create"],
        auth="user",
        type="http",
        method=["POST"],
        website=True,
        csrf=False,
    )
    def portal_bookings_create(self, **post):

        Booking = request.env["resource.booking"].sudo()
        BookingType = request.env["resource.booking.type"].sudo()
        partner_id = request.env.user.partner_id
        res = Booking.create(
            {
                "name": post.get("name"),
                "type_id": BookingType.browse(int(post.get("type"))).id,
                "partner_id": partner_id.id,
                "combination_auto_assign": True,
                "description": post.get("description", False),
                "user_id": partner_id.user_id.id,
            }
        )

        return request.redirect("/my/bookings/%s/schedule" % res.id)
