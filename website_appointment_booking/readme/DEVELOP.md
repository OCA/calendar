## Purpose

Public, login-free booking pages for `resource.booking.type` records, reusing the slot
computation of `resource_booking` instead of duplicating it.

## Model

- `resource.booking.type` inherits `website.published.mixin`: the stored flag is
  `is_published`; `website_published` is the mixin's related field and the form keeps
  using it. `website_url` is computed as `/book/<slug>`.
- `website_slug` is a stored compute with `readonly=False`: filled from the name once,
  never overwritten afterwards, and normalised with the platform `slugify` on
  create/write so a hand-typed value is URL-safe. It is unique (SQL constraint) and
  mandatory to publish (Python constraint).
- `resource.booking._prepare_meeting_vals`: under the context key
  `website_appointment_booking_notes`, set by the confirm route, the meeting
  description is the type's advice followed by the booking's description (the
  visitor's notes, escaped with `plaintext2html`). Other bookings keep the advice
  only, since their description may hold internal text. A meeting created again
  later, from the back office, has the advice only.

## Controller

One controller class, `WebsiteAppointmentBooking`, with three routes:

| Route                           | Purpose                             |
| ------------------------------- | ----------------------------------- |
| `/book/<slug>[/<year>/<month>]` | booking page, in the sitemap        |
| `/book/<slug>/confirm` (POST)   | create + confirm the booking        |
| `/book/<slug>/success`          | thank-you page fed from the session |

Invariants:

- Everything runs `sudo()` on records looked up through the published slug; no ACL is
  granted to the public group.
- Slot computation uses a _phantom_ booking (`new()`), so nothing is written while
  browsing. The same computation validates a submitted time (`_is_available_slot`): a
  POST can only book a time the page would have offered, which also enforces the
  modification deadline and working hours.
- Submitted `when` values must carry an offset and are normalised to UTC; the success
  page is rendered from that canonical instant, never from client strings.
- Error feedback travels in the URL as a _code_ (`?error=slot_taken`), mapped to a
  translated message by `_get_error_message`. Unknown codes render nothing, so the page
  cannot be used to display arbitrary text.
- Public POSTs pass `_check_submission`: a honeypot field (`HONEYPOT_FIELD`, rendered by
  the `booking_form_guard` template) and reCAPTCHA v3 through
  `ir.http._verify_request_recaptcha_token`, which is a no-op until the website has a
  site key.
- The public user never owns records: the booking's `user_id` (and thus the meeting
  organizer) is set to the first human resource of the assigned combination
  (`_get_organizer`); contacts are reused by email and an existing contact is not
  renamed.

## Extension points

- `_prepare_booking_page_values(booking_type, year, month, **kw)` returns the rendering
  values; overrides add keys. `padded_slots` (tz-aware slots with one day of padding) is
  exposed for them.
- `_get_error_message(code)`: extend the code → message map.
- `_check_submission(kwargs, action)`,
  `_get_or_create_partner(name, email, company=None, phone=None)` and
  `_get_optional_contact_values(kwargs)` (the trimmed `company` and `phone` inputs):
  reusable by other public forms of the page.
- Template anchors: `.o_wab_alerts_row` (error alert) and `.o_wab_calendar_row`
  (calendar block) for `xpath` insertions; `booking_form_guard` for the hidden fields
  any new form must include.
- Frontend: `FormGuard` (`static/src/js/form_guard.esm.js`) attaches the reCAPTCHA token
  fetch to a form; other modules import it with their own action name.

These points exist so that flows needing extra dependencies — turning out-of-hours
visitors into CRM leads, for instance — can live in their own glue module instead of
here.
