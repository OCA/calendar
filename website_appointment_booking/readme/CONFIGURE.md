Before publishing a booking type, ensure you have configured the
``resource_booking`` module:

1. Create at least one **Resource** and **Resource Calendar** under
   **Resource Bookings > Configuration**.
2. Create one or more **Resource Combinations** under
   **Resource Bookings > Combinations**, linking resources to calendars.
3. Create a **Booking Type** under **Resource Bookings > Types** and
   assign the combinations to it.

To publish a booking type on the website:

4. Open the booking type you want to publish.
5. In the **Website** section, check **Visible on current website** (or use
   the **Go to Website** smart button).
6. Optionally customize the **Website Slug** (auto-generated from the name,
   normalised to lowercase letters, digits and dashes).
7. Optionally add a **Website Description** that will appear on the booking
   page.
8. The booking page is now accessible at ``/book/<slug>``.

To protect the public form against bots beyond the built-in honeypot,
configure a reCAPTCHA v3 site key and secret under **Website > Settings**.
The form is verified with the action name ``website_appointment_booking``.
