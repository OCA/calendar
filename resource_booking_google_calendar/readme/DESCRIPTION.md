This module glues `resource_booking` with `google_calendar`.

When the organizer of a booking synchronizes their calendar with Google,
Odoo pushes the meeting to Google Calendar and Google invites every attendee
by email. Odoo also sends its own invitation, reschedule and cancellation
emails unless the organizer's Google *access token* is still valid at that
moment. That token expires one hour after the last synchronization and is
only refreshed right before Odoo talks to Google, which happens after the
emails have been sent. In practice the customer receives two invitations
whenever the resource has not opened their calendar during the last hour.

With this module, meetings created from a resource booking never trigger the
Odoo emails when the organizer has an active Google Calendar connection: the
attendees only receive the invitations sent by Google. Bookings whose
organizer does not synchronize with Google keep receiving the Odoo emails.
Plain meetings without a booking are not affected.
