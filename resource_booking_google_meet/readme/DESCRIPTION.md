When a `resource.booking` is confirmed it creates a `calendar.event`. This module
ensures the `google_calendar` integration auto-generates a unique Google Meet URL per
booking — with recording, "Take notes for me" Gemini summaries, and transcripts on
Google Workspace Business Standard and above.

**How it works:** `google_calendar` adds conferencing to an event when both
`videocall_location` and `location` are empty on the event at sync time. If the booking
type has a physical address set, this module clears `location` from the meeting vals so
the conferencing condition is always satisfied for bookings without a custom videocall
URL.

If the booking type has an explicit `videocall_location` (e.g. a static Zoom personal
room), the module leaves everything unchanged — the static URL is preserved and Google
won't add conferencing.

> **Note:** The Meet URL only appears after the first `google_calendar` cron sync.
> The `videocall_location` field on the calendar event is updated automatically once
> Google returns the conferencing details.
