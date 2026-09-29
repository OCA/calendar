Half-day public holidays such as Christmas Eve cannot be expressed yet, because
a public holiday line only carries a date. The times covered by the generated
time off are computed in `_prepare_resource_leave_hours`, so adding a day period
to the line only requires overriding that method.

Changing the working schedule of an employee does not recompute leaves that were
already validated under the previous schedule.
