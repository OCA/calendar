The CalDAV Synchronization module for Odoo allows users to synchronize
their calendar events with CalDAV servers. This enables seamless
integration of Odoo calendar with external applications like Apple
Calendar or Thunderbird.

## Features

- Synchronize Odoo calendar events with CalDAV servers.
- Create, update, and delete events in Odoo and reflect changes on the
  CalDAV server.
- Poll CalDAV server for changes and update Odoo calendar accordingly.

## Technical Details

- The module extends the `calendar.event` model to add CalDAV
  synchronization functionality.
- It uses the `icalendar` library to format events and the `caldav`
  library to interact with CalDAV servers.
- Polling for changes on the CalDAV server can be triggered manually by
  triggering the scheduled action in Odoo.
