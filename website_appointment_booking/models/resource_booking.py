# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup

from odoo import models
from odoo.tools.mail import plaintext2html


class ResourceBooking(models.Model):
    _inherit = "resource.booking"

    def _prepare_meeting_vals(self):
        """Add the notes of a public booking to its meeting.

        Only for bookings made on the public page: elsewhere the description
        defaults to the type's advice and may hold internal text.
        """
        vals = super()._prepare_meeting_vals()
        if self.env.context.get("website_appointment_booking_notes") and (
            self.description
        ):
            advice = self.type_id.requester_advice
            vals["description"] = (
                plaintext2html(advice) if advice else Markup()
            ) + Markup(self.description)
        return vals
