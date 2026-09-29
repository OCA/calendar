# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

SYNC_TRIGGER_FIELDS = {"year", "country_id"}


class CalendarPublicHoliday(models.Model):
    _inherit = "calendar.public.holiday"

    global_leave_count = fields.Integer(compute="_compute_global_leave_count")
    resource_calendar_count = fields.Integer(
        compute="_compute_resource_calendar_count",
        help="Working schedules these public holidays apply to.",
    )
    sync_warning = fields.Text(
        compute="_compute_sync_warning",
        help="Why some of these public holidays generate no time off.",
    )

    def _get_applicable_resource_calendars(self):
        """Working schedules at least one of these public holidays reaches.

        Only the nationwide public holidays count, since a scoped one belongs
        to the people of its regions rather than to a schedule.
        A nationwide public holiday is generated company-wide, which standard
        applies to every schedule of the company, so the reach is every
        schedule of a matching company.
        """
        self.ensure_one()
        nationwide = self.line_ids.filtered(
            lambda line: line.active and not line._has_public_holiday_scope()
        )
        listed = self.line_ids.filtered(
            lambda line: line.active
            and line._has_public_holiday_scope()
            and line.additional_resource_calendar_ids
        )
        if not nationwide and not listed:
            return self.env["resource.calendar"]
        candidates = self.env[
            "calendar.public.holiday.line"
        ]._get_public_holiday_calendars()
        matching = self.env["resource.calendar"]
        for calendar in candidates:
            companies = calendar._public_holiday_companies()
            reaching = nationwide | listed.filtered(
                lambda line, calendar=calendar: calendar
                in line.additional_resource_calendar_ids
            )
            if any(
                calendar._matches_public_holiday_country(line, company)
                for company in companies
                for line in reaching
            ):
                matching |= calendar
        return matching

    @api.depends(
        "country_id",
        "line_ids",
        "line_ids.region_ids",
        "line_ids.active",
        "line_ids.additional_resource_calendar_ids",
    )
    def _compute_resource_calendar_count(self):
        for record in self:
            record.resource_calendar_count = len(
                record._get_applicable_resource_calendars()
            )

    def action_view_resource_calendars(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Working Schedules"),
            "res_model": "resource.calendar",
            "view_mode": "list,form",
            "domain": [("id", "in", self._get_applicable_resource_calendars().ids)],
        }

    @api.depends(
        "line_ids",
        "line_ids.date",
        "line_ids.region_ids",
        "line_ids.active",
        "line_ids.additional_resource_calendar_ids",
        "country_id",
    )
    def _compute_sync_warning(self):
        for record in self:
            lines = record.line_ids._get_lines_to_sync()
            if not lines:
                record.sync_warning = False
                continue
            desired = lines._get_desired_global_leaves()
            issues = lines._public_holiday_sync_issues(desired)
            record.sync_warning = "\n".join(issues) or False

    def _compute_global_leave_count(self):
        data = self.env["resource.calendar.leaves"]._read_group(
            [("public_holiday_line_id.public_holiday_id", "in", self.ids)],
            ["public_holiday_line_id"],
            ["__count"],
        )
        counts = {}
        for line, count in data:
            counts[line.public_holiday_id.id] = (
                counts.get(line.public_holiday_id.id, 0) + count
            )
        for record in self:
            record.global_leave_count = counts.get(record.id, 0)

    def write(self, vals):
        res = super().write(vals)
        if SYNC_TRIGGER_FIELDS.intersection(vals):
            self.line_ids._sync_global_leaves()
        return res

    def action_sync_global_leaves(self):
        """Regenerate the time off of the selected public holiday calendars."""
        if not self.line_ids:
            return self._public_holiday_sync_notification(
                None,
                self.env._("There is no public holiday to synchronise."),
            )
        summary = self.line_ids._sync_global_leaves()
        return self._public_holiday_sync_notification(summary)

    def _public_holiday_sync_notification(self, summary, message=None):
        """Report the outcome, because a list action gives no other feedback."""
        problems = []
        if summary:
            message = self.env._(
                "%(created)s created, %(adopted)s adopted, %(updated)s updated, "
                "%(removed)s removed.",
                created=summary["created"],
                adopted=summary["adopted"],
                updated=summary["updated"],
                removed=summary["removed"],
            )
            problems = list(summary["issues"]) + [
                self.env._(
                    "%(line)s (%(date)s): %(reason)s",
                    line=conflict["line"],
                    date=conflict["date"],
                    reason=conflict["reason"],
                )
                for conflict in summary["conflicts"]
            ]
        if problems:
            message = "\n".join([message, ""] + problems)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Public holidays synchronised"),
                "message": message,
                "type": "warning" if problems else "success",
                "sticky": bool(problems),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_view_global_leaves(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Generated Time Off"),
            "res_model": "resource.calendar.leaves",
            "view_mode": "list,form",
            "domain": [("public_holiday_line_id", "in", self.line_ids.ids)],
        }
