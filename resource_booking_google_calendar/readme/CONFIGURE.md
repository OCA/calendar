Nothing to configure. The module installs itself as soon as both
`resource_booking` and `google_calendar` are installed.

Each human resource that should let Google send the invitations connects
their Google account from **Calendar > Sync with Google**. The connection is
considered active while the user keeps a refresh token, has not stopped the
synchronization and the synchronization is not paused globally.
