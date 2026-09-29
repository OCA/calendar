A nationwide public holiday (one naming no region) is generated once per
company of the matching country, as a global time off without working hours,
which standard Odoo applies to every working schedule of that company.

A public holiday naming **regions** is generated for single resources
instead, so that people sharing a schedule can belong to different
regions. Resolving a region to the resources concerned needs to know
about people, which this module does not: `hr_holidays_public_resource`
resolves them from the public holiday region of each employee. On its own
this module only applies nationwide public holidays.

One aspect is configurable per working schedule, under *Configuration >
Working Schedules*:

- **Apply Employee Public Holidays** -- untick to leave the employees of a
  schedule without the personal entries of region-scoped public holidays.
  The company-wide entries reach the schedule either way.

A public holiday line can also name **additional working schedules**: it is
then generated as a time off entry carrying each listed schedule, so
everybody working by it gets the day -- a special day for one shift plan,
say. Such an entry is only created where no company-wide record already
applies: a nationwide public holiday on the same day covers every schedule
anyway.

The working schedule form shows a read-only overview of the public holidays
that reach it -- the nationwide ones of its companies, grouped by calendar
year with the newest days first. Only days the schedule actually works are
listed: a Friday holiday says nothing to a Monday-to-Thursday schedule. A
flexible schedule has no fixed days, so it lists every day. With
`hr_holidays_public_resource` installed, the region-scoped days of the
employees on the schedule are counted as well.

A disabled public holiday line (see `calendar_public_holiday`) generates no
time off at all; disabling one removes the time off it generated.

**Set the country on your companies.** A public holiday calendar with a country
only reaches schedules whose company is in that country. A company with no
country at all is not filtered out -- otherwise nothing would be generated at
all -- so in a multi-country database an unset country makes every public
holiday apply everywhere. The public holiday form reports any public holiday
that generates no time off, and why.

By default only public holidays from 1 January of the current year onwards are
materialised. Set the `calendar_public_holiday_resource.sync_year_from` system
parameter to a year to change that floor.

Time off already generated for years before the floor is history and is left
untouched: raising the floor stops the maintenance of earlier records but does
not delete them, since removing them would re-evaluate historical leaves and
delete timesheets in closed periods. Deleting a public holiday line removes
its generated time off regardless, as an explicit act.
