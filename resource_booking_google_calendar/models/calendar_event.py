# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def _google_sends_booking_invitations(self):
        """Tell whether Google Calendar is in charge of inviting the attendees.

        True for meetings linked to a resource booking whose organizer keeps
        an active Google Calendar synchronization.

        The decision relies on the long-lived refresh token, not on the
        validity of the short-lived access token that ``google_calendar``
        checks. That access token is refreshed lazily, right before Odoo
        talks to Google, which happens *after* the core calendar has already
        decided whether to send its own invitation emails. Checking it here
        would make the booking attendees receive two invitations whenever
        the organizer has not synchronized during the last hour.
        """
        self.ensure_one()
        if not self.sudo().resource_booking_ids:
            return False
        organizer = self.user_id.sudo()
        if not organizer:
            return False
        return bool(
            organizer.res_users_settings_id.google_calendar_rtoken
            and organizer._get_google_sync_status() == "sync_active"
        )

    def _skip_send_mail_status_update(self):
        """Leave invitations, reschedules and cancellations to Google."""
        if self._google_sends_booking_invitations():
            return True
        return super()._skip_send_mail_status_update()
