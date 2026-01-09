
This module allows sharing an Odoo calendar as a **read-only ICS feed** that can be
subscribed to in external calendar clients such as **Outlook**, **Google Calendar**,
and **Thunderbird**.

The calendar is exposed via a public URL protected by an **access token** and can be
added as a network calendar (ICS / webcal).

Odoo provides bidirectional calendar synchronisation with external providers such as
Outlook and Google Calendar. However, in practice this integration is not always mature
and can suffer from functional limitations or bugs, especially in complex setups.

This module offers a **simple and robust alternative** for one-directional use cases:

* Events are exported from Odoo as a **read-only ICS calendar**
* External calendar clients periodically refresh the feed
* No changes are ever written back into Odoo

Typical use cases include:

* Sharing planning or resource bookings with employees
* Giving customers or partners insight into scheduled events
* Avoiding conflicts or data corruption caused by two-way sync

⚠ **Security note**  
The calendar is protected by an access token embedded in the URL.
Anyone who obtains this URL can view the calendar.
Treat the link as a secret.
R