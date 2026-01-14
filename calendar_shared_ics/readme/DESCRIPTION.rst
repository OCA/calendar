This module allows sharing an Odoo calendar as a read-only ICS feed that can be
subscribed to in external calendar clients such as Outlook, Google Calendar,
and Thunderbird.

The calendar is exposed via a public URL protected by an access token and can be
added as a network calendar (ICS / ``webcal://``). External calendar clients periodically
refresh the feed, providing near-real-time visibility of Odoo events without any
write-back capability.

Odoo includes bidirectional calendar synchronisation with external providers such as
Outlook and Google Calendar. In practice, however, this integration is not always
sufficiently robust and can suffer from functional limitations, data inconsistencies,
or bugs—especially in environments with complex recurrence rules, shared resources,
or high event volumes.

This module provides a simple, reliable, and intentionally one-directional
alternative:

* Events are exported from Odoo as a **read-only ICS calendar**
* External clients periodically fetch the feed
* No changes are ever written back into Odoo
* Old events can be excluded by default to improve synchronisation performance

Typical use cases include:

* Sharing planning or resource bookings with internal employees
* Providing customers or partners with insight into scheduled events
* Publishing operational calendars without exposing the Odoo backend
* Avoiding conflicts or data corruption caused by two-way synchronisation

Each shared calendar feed can be configured individually, including:

* Restricting events to a specific attendee (partner)
* Applying additional custom event filters
* Limiting exports to recent and future events only
* Generating and rotating access tokens
* Sharing the feed via the standard Odoo portal share wizard

**Security notice**

The calendar feed is protected solely by an **access token embedded in the URL**.
Anyone in possession of this URL can view the calendar contents.

The token grants **read-only access** and does **not** allow modification of data or
configuration of the feed. Nevertheless, the URL should be treated as confidential and
shared only with trusted recipients.
