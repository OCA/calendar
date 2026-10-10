This module adds public appointment booking pages to the website, powered by
the OCA `resource_booking` module.

Booking types can be published on the website with a customizable URL slug.
Visitors can browse available time slots on a monthly calendar and book an
appointment without logging in.

Key features:

- Public booking page at `/book/<slug>` for each published booking type
- Monthly calendar showing available time slots based on resource availability
- Server-rendered slot data -- no extra AJAX calls needed
- Automatic partner creation or reuse based on visitor email
- Calendar invitation sent to both parties upon confirmation
- Race condition handling when two visitors try to book the same slot
