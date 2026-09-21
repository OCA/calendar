This module adds public appointment booking pages to the website, powered by
the OCA `resource_booking` module.

Booking types can be published on the website with a customizable URL slug.
Visitors can browse available time slots on a monthly calendar and book an
appointment without logging in.

Key features:

- Public booking page at `/book/<slug>` for each published booking type,
  listed in the website sitemap
- Monthly calendar showing available time slots based on resource availability
- Slots displayed in the visitor's timezone, with a selector to switch
- Server-rendered slot data: no extra AJAX calls needed
- Automatic partner creation or reuse based on visitor email
- Calendar invitation sent to both parties upon confirmation, organized by
  the assigned resource
- Submitted times are validated server-side against the offered slots
- Honeypot and optional reCAPTCHA v3 protection on the public form
- Race condition handling when two visitors try to book the same slot

Visitors whose working hours do not overlap the published calendar are not
handled here: turning those into leads needs `crm`, so it is left to a
separate glue module.
