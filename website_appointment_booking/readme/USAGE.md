Once a booking type is published:

1. Share the URL `/book/<slug>` with your clients or embed it on your website.
2. Visitors see a monthly calendar with available days highlighted.
3. Clicking a day reveals the available time slots for that day.
4. Clicking a time slot shows a simple form asking for name and email.
5. Upon confirmation, a `resource.booking` record is created and confirmed
   automatically, and calendar invitations are sent to both parties.
6. If a slot is no longer available (race condition), the visitor is redirected
   back to the calendar with an informative error message.
