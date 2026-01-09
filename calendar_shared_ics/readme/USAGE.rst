1. **Create a shared calendar feed**
   * Go to *Calendar → Configuration → Shared ICS*
   * Create a new *Shared ICS calendar*
   * Select the partner whose events should be exported
   * Optionally define extra domain filters

2. **Generate a share link**
   * Click *Share*
   * Use the standard Odoo sharing wizard
   * An email will be sent containing a link to a landing page

3. **Subscribe from an external calendar**
   * Open the link from the email
   * Copy the **webcal://** or **https://** URL
   * Add it as a network / public calendar in your client

   Examples:
   * **Outlook**: *Add calendar → Subscribe from web*
   * **Google Calendar**: *Settings → Add calendar → From URL*
   * **Thunderbird**: *New Calendar → On the Network → iCalendar (ICS)*

4. **Rotate access token (optional)**
   * If the link is compromised, use *Rotate access token*
   * Old subscription URLs will stop working immediately
