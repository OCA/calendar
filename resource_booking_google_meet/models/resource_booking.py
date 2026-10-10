# Copyright 2026 Ledo Enterprises - D. Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ResourceBooking(models.Model):
    _inherit = "resource.booking"

    def _prepare_meeting_vals(self):
        """Ensure google_calendar generates a per-booking Meet URL.

        Behaviour:
        - Booking type with no videocall_location → clear location on the event
          so google_calendar's _google_values() satisfies `not location` and sends
          conferenceData to Google, which returns a unique meet.google.com URL.
        - Booking type with a videocall_location URL → leave everything unchanged;
          the static URL (Zoom, Whereby, etc.) is preserved and Google won't add
          conferencing because videocall_location is already non-empty.
        """
        vals = super()._prepare_meeting_vals()
        if not vals.get("videocall_location"):
            # google_calendar only requests a Meet URL when both videocall_location
            # and location are falsy on the event. Clear location here so the sync
            # condition passes even when the booking type has a physical address.
            vals["location"] = False
        return vals
