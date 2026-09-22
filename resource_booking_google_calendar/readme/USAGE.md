1. The user who will organize the meetings connects their Google Calendar.
   The organizer is the booking's **Organizer** field: by default the user
   who creates the booking in the backend, or the first human resource of
   the combination for bookings made from a public booking page.
2. A booking assigned to that resource is scheduled, from the backend, the
   portal or a public booking page.
3. The meeting is pushed to Google Calendar, which emails the invitation to
   the customer and to the resources. Odoo does not send its own invitation,
   nor the reschedule and cancellation emails for that meeting.

If the push to Google fails, the meeting stays flagged for synchronization
and is sent the next time the organizer opens their calendar or when the
Google Calendar synchronization cron runs.
