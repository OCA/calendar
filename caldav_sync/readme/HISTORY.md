## 0.8.2 (2024-11-28)

- Restructured module for OCA compliance:
  - Reordered Python imports per OCA guidelines.
  - Renamed XML view IDs to follow naming conventions.
  - Renamed data file to model-based naming.
  - Refactored test helpers to reduce complexity.
  - Updated manifest with OCA author and website.

## 0.8.0

- Disable sending of notification emails when events are created or
  updated in Odoo during a CalDAV server synchronization.
- General code cleanup with improved type hints.

## 0.7.0

- Stopped the import of past events when synchronizing from the CalDAV
  server. This should help with performance, timeouts and avoid
  importing events that are not relevant to the user.

## 0.6.0

- Fixed an issue where synchronizing events created duplicate events on
  every sync.
- Completely revamped and synchronization of recurring events in both
  directions.
  - Making a recurring event in Odoo correctly creates the recurring
    event on the server.
  - Modifying the base event of a recurrence with "all events" or
    "future events" in Odoo reflects correctly on the server.
  - Modifying a non-base event correctly updates on the server in all 3
    modes (this event only, all events, future events).
  - Modifying a base recurring event on the CalDAV server correctly
    updates the events on Odoo after a synchronization.
  - Deleting a whole recurring sequence from Odoo correctly deletes the
    sequence from the CalDAV server.
  - Deleting a single event or a whole recurring sequence on the CalDAV
    server correctly synchronizes to Odoo after a synchronization.
- CalDAV (iCalendar) UIDs are now correctly shared among events of a
  same recurrence in Odoo. This corrects a number of issues around
  updating and deleting events from both the Odoo and CalDAV server
  side.
