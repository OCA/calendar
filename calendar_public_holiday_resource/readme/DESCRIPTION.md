Public holidays configured in the *Public Holidays* calendar are materialised
as global time off (`resource.calendar.leaves` without a resource): one
company-wide record per company and public holiday, without working hours,
which standard Odoo applies to every working schedule of the company.

Standard Odoo already keys every public holiday behaviour on those records, so
generating them makes the whole standard stack pick the OCA configuration up
without any further glue:

- working time excludes the public holiday, so booking a leave over it does not
  consume an allocation day;
- the day is greyed out as an unusual day in calendar views and shows as
  unavailable in gantt views;
- leaves and their timesheets that were already approved are recomputed when a
  public holiday is added, moved or removed;
- with `project_timesheet_holidays` installed, a timesheet entry is generated on
  the public holiday for every employee working that day.
