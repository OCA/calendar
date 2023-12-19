The ``number_of_attendees`` field is defined directly on the resource booking.
While it makes sense to have it there, it would make more sense and be more
useful to store it in the meeting, in the same way as the location field.

However, calendar events already have a list of attendees, so it could be
confusing if the two fields are not related.

Adding this field to ``calendar.event`` could be done in a separate module
that does not depend on ``resource.booking``.
