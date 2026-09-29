# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict
from datetime import date, datetime, time

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

SYNC_TRIGGER_FIELDS = {
    "date",
    "name",
    "region_ids",
    "public_holiday_id",
    "active",
    "additional_resource_calendar_ids",
}


class CalendarPublicHolidayLine(models.Model):
    _inherit = "calendar.public.holiday.line"

    additional_resource_calendar_ids = fields.Many2many(
        "resource.calendar",
        "calendar_public_holiday_line_resource_calendar_rel",
        "line_id",
        "calendar_id",
        string="Additional Working Schedules",
        help="Working schedules a region-scoped public holiday is generated "
        "on as a time off entry carrying the schedule, so everybody working "
        "by it gets the day as well. Only a scoped public holiday needs this: "
        "a nationwide one is generated company-wide, which already reaches "
        "every working schedule of the company.",
    )
    global_leave_ids = fields.One2many(
        "resource.calendar.leaves",
        "public_holiday_line_id",
        string="Generated Time Off",
    )
    global_leave_count = fields.Integer(compute="_compute_global_leave_count")

    def _check_date_region_one(self):
        res = super()._check_date_region_one()
        if self.additional_resource_calendar_ids:
            others = self.search(
                [
                    ("date", "=", self.date),
                    ("public_holiday_id", "=", self.public_holiday_id.id),
                    ("additional_resource_calendar_ids", "!=", False),
                    ("id", "!=", self.id),
                ]
            )
            for other in others:
                if (
                    self.additional_resource_calendar_ids
                    & other.additional_resource_calendar_ids
                ):
                    raise ValidationError(
                        self.env._(
                            "You can't create duplicate public holiday per "
                            "date %s and one of the working schedules.",
                            self.date,
                        )
                    )
        return res

    @api.constrains("date", "additional_resource_calendar_ids")
    def _check_date_additional_calendar(self):
        # Listing a schedule two lines of one day both carry has to be caught
        # whichever of them is edited.
        for line in self:
            line._check_date_region_one()

    def _compute_global_leave_count(self):
        data = self.env["resource.calendar.leaves"]._read_group(
            [("public_holiday_line_id", "in", self.ids)],
            ["public_holiday_line_id"],
            ["__count"],
        )
        counts = {line.id: count for line, count in data}
        for record in self:
            record.global_leave_count = counts.get(record.id, 0)

    # ------------------------------------------------------------------
    # Sync window
    # ------------------------------------------------------------------

    @api.model
    def _get_sync_date_from(self):
        """Public holidays before this date are never materialised.

        Creating a mirror in the past makes ``hr_holidays`` re-evaluate
        historical leaves (possibly refusing them) and makes
        ``project_timesheet_holidays`` write timesheets into closed periods,
        so the default floor is the first day of the current year.
        """
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("calendar_public_holiday_resource.sync_year_from")
        )
        year = fields.Date.context_today(self).year
        if param:
            try:
                year = int(param)
            except ValueError:
                _logger.warning(
                    "Ignoring invalid calendar_public_holiday_resource."
                    "sync_year_from parameter %r",
                    param,
                )
        return date(year, 1, 1)

    def _get_lines_to_sync(self):
        date_from = self._get_sync_date_from()
        if self:
            return self.filtered(lambda line: line.date and line.date >= date_from)
        # Disabled lines are part of the sync scope on purpose: their mirrors
        # have to be removed, which `_get_desired_global_leaves` arranges by
        # desiring nothing for them.
        return self.with_context(active_test=False).search([("date", ">=", date_from)])

    # ------------------------------------------------------------------
    # Value preparation
    # ------------------------------------------------------------------

    def _prepare_resource_leave_hours(self):
        """Hook returning the ``(start, end)`` local times covered by the line.

        Kept separate so that half-day public holidays only have to override
        this method once the model grows a day period.
        """
        self.ensure_one()
        # Second precision, like the standard public holiday form, rather than
        # time.max which would store a 23:59:59.999999 end.
        return time.min, time(23, 59, 59)

    def _prepare_resource_leave_datetimes(
        self, calendar=None, resource=None, company=None
    ):
        """UTC-naive ``(date_from, date_to)`` spanning the line locally.

        The values are final: they place the day on the local midnight of the
        timezone the interval engine will interpret the record in -- the
        resource's for a personal record, the calendar's for a record carrying
        one, and the main schedule of the company for a company-wide one. The
        ``hr_holidays`` create hook that re-localises user-timezone input is
        cancelled out at create time by ``_compensate_native_tz_shift``;
        building the values in the user's timezone instead, as before, left
        the stored values depending on which user's sync ran last -- the hook
        never runs on write or for personal records -- and made every run
        rewrite the records again.
        """
        self.ensure_one()
        hour_from, hour_to = self._prepare_resource_leave_hours()
        tz_name = "UTC"
        if resource:
            tz_name = resource.tz or tz_name
        elif calendar:
            tz_name = calendar.tz or tz_name
        elif company:
            tz_name = company.resource_calendar_id.tz or tz_name
        build_tz = pytz.timezone(tz_name)
        return (
            build_tz.localize(datetime.combine(self.date, hour_from))
            .astimezone(pytz.utc)
            .replace(tzinfo=None),
            build_tz.localize(datetime.combine(self.date, hour_to))
            .astimezone(pytz.utc)
            .replace(tzinfo=None),
        )

    @api.model
    def _has_native_public_holiday_tz_shift(self):
        return hasattr(
            self.env["resource.calendar.leaves"], "_prepare_public_holidays_values"
        )

    @api.model
    def _compensate_native_tz_shift(self, vals):
        """Pre-shift create values so the ``hr_holidays`` create hook lands them.

        ``_prepare_public_holidays_values`` re-interprets the wall clock of a
        company-wide record from the creating user's timezone into the
        calendar's, and only on create. The desired values are already final,
        so the create values are shifted the opposite way here; the two shifts
        cancel out and the stored record carries the final values whichever
        user runs the sync. This cannot be done by overriding the hook: this
        module does not depend on ``hr_holidays`` and sits below it in the
        method resolution order, so the native hook runs first regardless.
        Personal records and calendar-less records are never touched by the
        hook and need no compensation.
        """
        if not self._has_native_public_holiday_tz_shift():
            return vals
        if not vals.get("calendar_id") or vals.get("resource_id"):
            return vals
        user_tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
        calendar = self.env["resource.calendar"].browse(vals["calendar_id"])
        calendar_tz = pytz.timezone(calendar.tz or "UTC")
        if user_tz == calendar_tz:
            return vals
        vals = dict(vals)
        for field in ("date_from", "date_to"):
            local_wall = pytz.utc.localize(vals[field]).astimezone(calendar_tz)
            vals[field] = (
                user_tz.localize(local_wall.replace(tzinfo=None))
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
        return vals

    def _prepare_global_leave_vals(self, calendar=None, resource=None, company=None):
        self.ensure_one()
        date_from, date_to = self._prepare_resource_leave_datetimes(
            calendar=calendar, resource=resource, company=company
        )
        return {
            "name": self.name,
            "calendar_id": calendar.id if calendar else False,
            "resource_id": resource.id if resource else False,
            "time_type": "leave",
            "date_from": date_from,
            "date_to": date_to,
            "public_holiday_line_id": self.id,
        }

    # ------------------------------------------------------------------
    # Synchronisation
    # ------------------------------------------------------------------

    @api.model
    def _with_public_holiday_companies(self, leaves, extra_company_ids=None):
        """Have the companies of ``leaves`` selected on its environment.

        Removing or rewriting a mirror makes ``project_timesheet_holidays``
        regenerate the timesheets of the employee leaves it overlaps, and the
        timesheet machinery refuses an employee outside ``env.companies``.
        The synchronisation legitimately touches companies beyond the user's
        current selection -- saving the first employee of a new company, say,
        also cleans up another company's mirrors on a shared schedule -- so
        the companies it acts on are added to the selection for its own
        writes. ``leaves`` is expected to be sudo'ed, like every mirror
        mutation.
        """
        wanted = set(leaves.company_id.ids) | set(extra_company_ids or [])
        current = leaves.env.companies.ids
        missing = wanted - set(current)
        if not missing:
            return leaves
        return leaves.with_context(allowed_company_ids=list(current) + sorted(missing))

    @api.model
    def _sync_leave_context(self):
        """Context the synchronisation touches global time off under.

        ``leave_skip_date_check`` is what standard itself uses wherever it
        rewrites leaves on the user's behalf, changing a working schedule
        included. The synchronisation never moves a leave; it only makes
        standard recompute the ones a public holiday falls into. A conflict
        already sitting in the data -- two overlapping requests, say -- would
        otherwise surface as "An employee already booked time off which
        overlaps with this period" and block the public holiday or the working
        schedule from being saved at all.

        ``tracking_disable`` keeps the leave re-evaluation from emailing:
        rewriting a leave's state on the user's behalf would otherwise send
        the usual approval and refusal notifications for a change nobody
        made by hand.
        """
        return {
            "public_holiday_sync": True,
            "leave_skip_date_check": True,
            "tracking_disable": True,
        }

    @api.model
    def _get_public_holiday_calendars(self):
        """Working schedules the synchronisation has to look at.

        Every schedule takes part: own entries and employee entries are each
        gated by their flag inside ``_get_desired_global_leaves``; the
        company-wide entries do not depend on schedules at all. The
        always-true leaf keeps the no-search-all check quiet.
        """
        return self.env["resource.calendar"].sudo().search([("id", "!=", 0)])

    @api.model
    def _get_public_holiday_companies(self):
        # The always-true leaf keeps the no-search-all check quiet.
        return self.env["res.company"].sudo().search([("id", "!=", 0)])

    def _public_holiday_sync_issues(self, desired, calendars=None):
        """Explain why lines produced no global time off.

        Silence is the worst outcome here: a country left blank on every
        company generates nothing at all, and without this there is nothing
        anywhere to say so.
        """
        issues = []
        if calendars is not None:
            # Saving one working schedule, or moving an employee, synchronises
            # a subset. Whether a public holiday reaches anything at all is
            # still a question about every schedule, so it is asked again here
            # rather than answered from the subset at hand.
            desired = self._get_desired_global_leaves()
        matched_lines = {key[0] for key in desired}
        countries = self._get_public_holiday_companies().country_id
        for line in self.filtered("active") - self.browse(matched_lines):
            holiday_country = line.public_holiday_id.country_id
            if holiday_country and countries and holiday_country not in countries:
                reason = self.env._("no company is located in %s", holiday_country.name)
            elif line._has_public_holiday_scope():
                reason = line._public_holiday_scope_description()
            else:
                reason = self.env._("no company matches")
            issues.append(
                self.env._(
                    "%(name)s (%(date)s): %(reason)s",
                    name=line.name,
                    date=fields.Date.to_string(line.date),
                    reason=reason,
                )
            )
        return issues

    def _public_holiday_scope_description(self):
        """Why a scoped line reached nobody, for the sync warning."""
        self.ensure_one()
        names = self.region_ids.mapped("name")
        return self.env._(
            "nobody works at %s (a region-scoped public holiday is given to "
            "the people assigned to one of its regions)",
            ", ".join(names),
        )

    def _get_public_holiday_resource_targets(self, calendars):
        """Resources a region-scoped public holiday has to be generated for.

        A working schedule is one scope, so a scoped public holiday cannot be
        generated on it without giving it to everybody sharing the schedule.
        Scoped lines are therefore generated per resource instead, which
        ``hr_holidays_public_resource`` resolves from the public holiday
        region of the employees. Nothing here knows about people, so
        nothing matches.

        :return: list of ``(line, resource, calendar, company)``
        """
        return []

    def _get_desired_global_leaves(self, calendars=None):
        """Return ``{(line_id, company_id, calendar_id, resource_id): vals}``.

        Nationwide public holidays become one company-wide record each,
        without a working schedule, which standard applies to every schedule
        of the company. The working schedules a line lists get a record
        carrying the schedule -- unless a company-wide record already covers
        the day there. Scoped ones become one record per resource, so that
        colleagues sharing a schedule keep their own regions; a resource on
        a schedule the line lists is covered through the schedule already.

        The company-wide entries come first in the mapping: adoption walks it
        in order, and a hand-maintained company-wide record belongs to the
        company-wide entry, not to the entry of one schedule.
        """
        if calendars is None:
            calendars = self._get_public_holiday_calendars()
        lines = self.filtered("active")
        nationwide = lines.filtered(lambda line: not line._has_public_holiday_scope())
        desired, covered_days = nationwide._get_desired_company_leaves()
        calendar_desired = lines._get_desired_calendar_leaves(calendars, covered_days)
        desired.update(calendar_desired)
        covered_calendar_days = {
            (company_id, calendar_id, self.browse(line_id).date)
            for line_id, company_id, calendar_id, _resource_id in calendar_desired
        }
        desired.update(
            lines._get_desired_resource_leaves(
                calendars, covered_days, covered_calendar_days
            )
        )
        return desired

    def _get_desired_company_leaves(self):
        """One company-wide record per matching company and nationwide line.

        Also returns the ``(company_id, date)`` pairs those records cover, so
        the resource entries can skip the days already given to everybody.
        """
        winner = {}
        for company in self._get_public_holiday_companies():
            for line in self:
                if not company._matches_public_holiday_line(line):
                    continue
                day_key = (company.id, line.date)
                current = winner.get(day_key)
                if current is None or line.id < current.id:
                    winner[day_key] = line
        desired = {}
        covered_days = set()
        for (company_id, day), line in winner.items():
            company = self.env["res.company"].browse(company_id)
            desired[(line.id, company_id, False, False)] = (
                line._prepare_global_leave_vals(company=company)
            )
            covered_days.add((company_id, day))
        return desired, covered_days

    def _get_desired_calendar_leaves(self, calendars, covered_days):
        """The entries of the working schedules a scoped line lists.

        A schedule-wide entry is only generated where no company-wide record
        already applies: standard puts a company-wide record on every
        schedule of the company, so a second record for one schedule would
        have everybody on it off twice. A nationwide line therefore needs
        none, whatever it lists; only a scoped one gives its listed
        schedules a day they would not get otherwise.
        """
        winner = {}
        for line in self:
            if not line._has_public_holiday_scope():
                continue
            for calendar in line.additional_resource_calendar_ids:
                if calendar not in calendars:
                    # A schedule outside the requested subset stays untouched
                    # by this run.
                    continue
                for company in calendar._public_holiday_companies():
                    if (company.id, line.date) in covered_days:
                        continue
                    if not calendar._matches_public_holiday_country(line, company):
                        continue
                    day_key = (company.id, calendar.id, line.date)
                    current = winner.get(day_key)
                    if current is None or line.id < current.id:
                        winner[day_key] = line
        return {
            (line.id, company_id, calendar_id, False): line._prepare_global_leave_vals(
                calendar=calendars.browse(calendar_id)
            )
            for (company_id, calendar_id, _day), line in winner.items()
        }

    def _get_desired_resource_leaves(
        self, calendars, covered_days, covered_calendar_days
    ):
        """One record per resource a scoped line resolves to."""
        winner = {}
        for (
            line,
            resource,
            calendar,
            company,
        ) in self._get_public_holiday_resource_targets(
            calendars.filtered("public_holiday_employee_sync")
        ):
            # A nationwide public holiday already gives everybody the day,
            # and a schedule-wide entry everybody on the schedule, so a
            # personal one on top would have the resource off twice and be
            # timesheeted twice.
            if (company.id, line.date) in covered_days:
                continue
            if (company.id, calendar.id, line.date) in covered_calendar_days:
                continue
            day_key = (company.id, calendar.id, resource.id, line.date)
            current = winner.get(day_key)
            if current is None or line.id < current[0].id:
                winner[day_key] = (line, resource, calendar, company)
        return {
            (line.id, company.id, calendar.id, resource.id): (
                line._prepare_global_leave_vals(calendar=calendar, resource=resource)
            )
            for line, resource, calendar, company in winner.values()
        }

    def _sync_global_leaves(self, calendars=None, dry_run=False):
        """Materialise the public holiday lines as global time off.

        Returns a summary dict so that the wizard can report a dry run.
        """
        Leave = (
            self.env["resource.calendar.leaves"]
            .sudo()
            .with_context(**self._sync_leave_context())
        )
        lines = self._get_lines_to_sync()
        summary = {
            "created": 0,
            "adopted": 0,
            "updated": 0,
            "removed": 0,
            "conflicts": [],
            "issues": [],
        }

        # Mirrors of lines outside the sync window are history and are left
        # alone entirely: removing them would re-evaluate historical leaves
        # and delete timesheets in closed periods. The year constraint on the
        # lines guarantees a line only leaves the window when its whole
        # calendar year does, so nothing current is ever missed this way.
        desired = lines._get_desired_global_leaves(calendars=calendars)
        summary["issues"] = lines._public_holiday_sync_issues(desired, calendars)

        existing_domain = [("public_holiday_line_id", "in", lines.ids)]
        if calendars is not None:
            # The company-wide mirrors carry no schedule but are part of every
            # subset sync: their desired counterparts are always computed, so
            # leaving them out here would orphan the existing records into the
            # adoption path.
            existing_domain.append(("calendar_id", "in", calendars.ids + [False]))
        existing = self._with_public_holiday_companies(
            Leave.search(existing_domain),
            extra_company_ids=[key[1] for key in desired],
        )

        desired_all = dict(desired)
        existing_by_key = {}
        # Built from `existing` so the company-extended environment is kept --
        # a recordset union takes the environment of its left operand.
        to_unlink = existing.browse()
        for leave in existing:
            key = (
                leave.public_holiday_line_id.id,
                leave.company_id.id,
                leave.calendar_id.id,
                leave.resource_id.id,
            )
            if key in desired and key not in existing_by_key:
                existing_by_key[key] = leave
            else:
                to_unlink |= leave

        to_write = []
        for key, leave in existing_by_key.items():
            vals = desired.pop(key)
            changed = {
                field: value
                for field, value in vals.items()
                if field in ("name", "date_from", "date_to") and leave[field] != value
            }
            if changed:
                to_write.append((leave, changed))

        # Whatever is left in `desired` has no mirror yet: adopt a manually
        # maintained record where one exists, create the rest.
        to_adopt, to_create = self._split_adoptable_global_leaves(
            desired, summary, desired_all
        )

        summary["removed"] = len(to_unlink)
        summary["updated"] = len(to_write)
        summary["adopted"] = len(to_adopt)
        summary["created"] = len(to_create)
        if dry_run:
            return summary

        # Order matters: dropping obsolete mirrors first keeps a moved holiday
        # from transiently overlapping its own previous record.
        if to_unlink:
            to_unlink.unlink()
        for leave, changed in to_write:
            leave.write(changed)
        for leave, vals, company_id in to_adopt:
            # Under the sync context: the record is managed from the first
            # write on, which would make the second one trip the guard.
            leave = self._with_public_holiday_companies(
                leave.with_context(**self._sync_leave_context()),
                extra_company_ids=[company_id],
            )
            leave.write(vals)
            # `company_id` is a stored compute that falls back to the current
            # company on a calendar-less record, so adoption has to pin it
            # again, exactly like `_create_global_leaves` does.
            leave.write({"company_id": company_id})
        self._create_global_leaves(to_create)
        return summary

    def _create_global_leaves(self, to_create):
        """Create mirrors grouped per company and year.

        ``_check_compare_dates`` scans the whole span of a batch and
        ``project_timesheet_holidays._work_time_per_day`` expands attendance
        rules across it, so batches are kept to a single year per company.
        """
        Leave = (
            self.env["resource.calendar.leaves"]
            .sudo()
            .with_context(**self._sync_leave_context())
        )
        grouped = defaultdict(list)
        for company_id, vals in to_create:
            grouped[(company_id, vals["date_from"].year)].append(vals)
        for (company_id, _year), vals_list in sorted(grouped.items()):
            company = self.env["res.company"].browse(company_id)
            # `company_id` is a readonly stored compute falling back to
            # `self.env.company`, and an explicit value in the create values is
            # discarded. `with_company` alone is not enough either: the compute
            # is batched and may be flushed while a later company is active, so
            # the value is pinned right after the batch.
            vals_list = [self._compensate_native_tz_shift(vals) for vals in vals_list]
            leaves = Leave.with_company(company).create(vals_list)
            leaves.write({"company_id": company.id})

    def _split_adoptable_global_leaves(self, desired, summary, desired_all=None):
        """Split missing mirrors into records to adopt and records to create.

        Replacing a manually maintained public holiday would re-evaluate every
        overlapping leave twice and risk auto-refusing them in between, so an
        existing single-day record is adopted in place instead. Its id is kept,
        which also preserves the timesheets already linked to it.

        A conflicting record blocks the creation of the mirror as well: two
        public time off entries on the same day for the same schedules would
        trip the standard overlap constraint, so the conflict is reported and
        the day is left to a human.

        :param desired_all: the full desired mapping, including the keys that
            already have a mirror; used to tell whether every schedule covered
            by a company-wide record keeps its day when the record is adopted
            for a single schedule.
        """
        Leave = self.env["resource.calendar.leaves"].sudo()
        if desired_all is None:
            desired_all = desired
        to_adopt = []
        to_create = []
        claimed = set()
        for (line_id, company_id, calendar_id, resource_id), vals in desired.items():
            line = self.browse(line_id)
            if resource_id:
                # Only company-wide time off was ever maintained by hand; a
                # record belonging to one resource has nothing to adopt.
                to_create.append((company_id, vals))
                continue
            candidate = Leave.browse()
            # Prefer a record already scoped to this schedule over a
            # company-wide one, and never let two entries claim the same
            # record -- a company-wide record can only be adopted once.
            calendar_domains = [[("calendar_id", "=", False)]]
            if calendar_id:
                calendar_domains.insert(0, [("calendar_id", "=", calendar_id)])
            else:
                # A hand-made record scoped to one schedule blocks the
                # company-wide mirror through the standard overlap constraint,
                # so it has to be looked at too: a matching one is adopted and
                # widened -- everybody it covered keeps the day and the rest
                # of the company gains it, which is what the public holiday
                # means -- and anything else is reported as a conflict.
                calendar_domains.append([("calendar_id", "!=", False)])
            for calendar_domain in calendar_domains:
                found = Leave.search(
                    line._get_adoption_domain(company_id, calendar_id, vals)
                    + calendar_domain
                )
                candidate = found.filtered(lambda leave: leave.id not in claimed)[:1]
                if candidate:
                    break
            if not candidate:
                to_create.append((company_id, vals))
                continue
            reason = line._get_adoption_conflict_reason(
                candidate, company_id, calendar_id, desired_all
            )
            if reason:
                summary["conflicts"].append(
                    {
                        "line": line.display_name,
                        "date": fields.Date.to_string(line.date),
                        "leave_id": candidate.id,
                        "leave": candidate.display_name,
                        "reason": reason,
                    }
                )
                continue
            claimed.add(candidate.id)
            to_adopt.append((candidate, vals, company_id))
        return to_adopt, to_create

    def _get_adoption_conflict_reason(
        self, candidate, company_id, calendar_id, desired_all
    ):
        """Why ``candidate`` cannot be adopted for this line, or ``None``."""
        self.ensure_one()
        if candidate.date_from.date() != candidate.date_to.date():
            # A multi-day record (a Christmas shutdown, say) must not be
            # split or absorbed; leave it to a human.
            return "multi-day time off overlapping the public holiday"
        if (candidate.name or "").strip().casefold() != self.name.strip().casefold():
            # A same-day record under another name (a bridge day, an event) is
            # not this public holiday entered by hand.
            return "time off under a different name on the same day"
        if not candidate.calendar_id and calendar_id:
            # Adopting a company-wide record as the own entry of one schedule
            # narrows its coverage. That is only harmless when the company-wide
            # entry of the same day exists as well, so nobody silently loses
            # the day.
            covered_company_wide = any(
                key[1] == company_id
                and not key[2]
                and not key[3]
                and self.browse(key[0]).date == self.date
                for key in desired_all
            )
            if not covered_company_wide:
                return (
                    "company-wide time off also covers working schedules the "
                    "public holiday does not apply to"
                )
        return None

    def _get_adoption_domain(self, company_id, calendar_id, vals):
        self.ensure_one()
        domain = [
            ("resource_id", "=", False),
            ("public_holiday_line_id", "=", False),
            ("company_id", "=", company_id),
            ("date_from", "<=", vals["date_to"]),
            ("date_to", ">=", vals["date_from"]),
        ]
        if "holiday_id" in self.env["resource.calendar.leaves"]._fields:
            # Never adopt the mirror of an approved employee leave.
            domain.append(("holiday_id", "=", False))
        return domain

    # ------------------------------------------------------------------
    # Triggers
    # ------------------------------------------------------------------

    def _get_sync_scope(self):
        """Extend a recordset with every line sharing one of its dates.

        Deduplication picks a single winner per day, so a line can only be
        given up or taken back by looking at its rivals as well: adding a
        nationwide holiday has to drop the scoped mirror of the same day, and
        removing it has to bring that mirror back.
        """
        dates = [line.date for line in self if line.date]
        if not dates:
            return self
        return self | self.search([("date", "in", dates)])

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._get_sync_scope()._sync_global_leaves()
        return lines

    @api.model
    def _get_public_holiday_sync_trigger_fields(self):
        """Fields whose change has to regenerate the mirrored time off."""
        return SYNC_TRIGGER_FIELDS

    def write(self, vals):
        dates_before = [line.date for line in self if line.date]
        res = super().write(vals)
        if self._get_public_holiday_sync_trigger_fields().intersection(vals):
            scope = self._get_sync_scope()
            if dates_before:
                scope |= self.search([("date", "in", dates_before)])
            scope._sync_global_leaves()
        return res

    def unlink(self):
        # Delete the mirrors through the ORM: the database-level cascade would
        # bypass `_reevaluate_leaves` and the timesheet cleanup, leaving stale
        # leave durations and orphaned analytic lines behind.
        dates = [line.date for line in self if line.date]
        self._with_public_holiday_companies(
            self.global_leave_ids.sudo().with_context(**self._sync_leave_context())
        ).unlink()
        res = super().unlink()
        if dates:
            self.search([("date", "in", dates)])._sync_global_leaves()
        return res

    def action_view_global_leaves(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Generated Time Off"),
            "res_model": "resource.calendar.leaves",
            "view_mode": "list,form",
            "domain": [("public_holiday_line_id", "=", self.id)],
        }

    @api.model
    def _cron_sync_global_leaves(self):
        """Keep the mirrors of the near future in step, idempotently.

        This is a self-healing net for schedules or companies changed while the
        module was uninstalled; a normal edit syncs through the write triggers.
        """
        date_from = self._get_sync_date_from()
        # Disabled lines included: their stale mirrors have to go too.
        lines = self.with_context(active_test=False).search(
            [
                ("date", ">=", date_from),
                ("date", "<=", date(date_from.year + 2, 12, 31)),
            ]
        )
        if lines:
            lines._sync_global_leaves()
