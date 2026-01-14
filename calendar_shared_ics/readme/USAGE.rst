
Only users with the *Shared ICS manager* role can create or modify
shared calendar feeds.

#. Go to *Calendar → Configuration → Shared ICS*
#. Create a new *Shared ICS calendar*
#. Configure the feed:
   
   * Select the **partner** whose events should be exported
   * Optionally restrict events further using **Additional Filtering**
   * Optionally limit the feed to **recent and future events only**
   * Adjust user-related filters to easily select internal or portal users

Each record represents one independent, read-only calendar feed.

Regular users can only **view their own feed** (if any) but cannot
create, modify, or delete shared calendars.

Generate a share link

#. Open the shared calendar feed record
#. Click **Share**
#. The standard Odoo *Share* wizard will open
#. Select one or more recipients and send the email

The email contains a link to a landing page where the recipient can
copy the actual subscription URL.

Subscribe from an external calendar

#. Open the link from the email
#. Copy either the **``webcal://``** or **``https://``** URL shown on the page
#. Add it as a network / public calendar in your calendar client

Examples:

* **Outlook**
  
  *Add calendar → Subscribe from web*

* **Google Calendar**
  
  *Settings → Add calendar → From URL*

* **Thunderbird**
  
  *New Calendar → On the Network → iCalendar (ICS)*

The external calendar will periodically refresh the feed.
All events are **read-only** and cannot be modified from the external client.

Rotate access token (optional)

If a subscription URL is compromised:

#. Open the shared calendar feed
#. Click **Rotate access token**
#. A new token is generated immediately

All previously issued URLs stop working at once, while the new URL
continues to function without further configuration.
