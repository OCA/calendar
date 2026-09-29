# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    public_holiday_line_id = fields.Many2one(
        "calendar.public.holiday.line",
        string="Source Public Holiday",
        readonly=True,
        index=True,
        copy=False,
        ondelete="cascade",
        help="Public holiday this global time off was generated from. Such "
        "records are maintained automatically and cannot be edited directly.",
    )

    # COALESCE, because a NULL calendar is the company-wide case and a NULL
    # resource the schedule-wide one, and Postgres would otherwise consider
    # every one of them distinct.
    _public_holiday_line_uniq = models.UniqueIndex(
        "(public_holiday_line_id, COALESCE(calendar_id, 0), company_id,"
        " COALESCE(resource_id, 0))"
        " WHERE public_holiday_line_id IS NOT NULL"
    )

    @api.depends("public_holiday_line_id.public_holiday_id.display_name")
    def _compute_display_name(self):
        """Name the public holiday calendar a generated record comes from.

        Global time off otherwise reads the same whether it was generated or
        entered by hand, which matters wherever these records are referenced
        from elsewhere, such as the timesheet entries of a public holiday. The
        calendar rather than the line carries the year and country; the line
        only carries the name, which the generated record already bears.
        """
        res = super()._compute_display_name()
        for leave in self.filtered("public_holiday_line_id"):
            source = leave.public_holiday_line_id.public_holiday_id.display_name
            if source:
                leave.display_name = f"[{source}] {leave.display_name}"
        return res

    @api.model_create_multi
    def create(self, vals_list):
        # The write/unlink guard alone would let RPC or imports smuggle in
        # records that look generated and then fight the synchronisation.
        if not self.env.context.get("public_holiday_sync") and any(
            vals.get("public_holiday_line_id") for vals in vals_list
        ):
            raise UserError(self._get_public_holiday_managed_error())
        leaves = super().create(vals_list)
        leaves._adapt_overlapping_leave_timesheets()
        return leaves

    def _get_timesheet_overlapping_leaves(self):
        """Approved leaves whose timesheets these records bear on.

        ``None`` when ``project_timesheet_holidays`` is not installed.
        """
        if "timesheet_ids" not in self._fields:
            return None
        overlapping = self.env["hr.leave"]
        for global_leave in self.filtered(lambda leave: not leave.resource_id):
            overlapping |= global_leave._get_overlapping_hr_leaves()
        return overlapping

    def _adapt_overlapping_leave_timesheets(self, previous=None):
        """Bring the timesheets of already approved leaves back in line.

        ``hr_holidays`` recomputes the duration of a leave a global time off
        falls into, and ``project_timesheet_holidays`` regenerates the
        timesheets of overlapping leaves when a global time off is removed --
        but not when one is created or moved. A public holiday added over an
        approved leave therefore left the leave costing a day less while
        still being timesheeted for it, and a moved one left the leave
        timesheeted for the new day and not for the old one.

        :param previous: the leaves overlapping the records before a move,
            which get their day back the same way.
        """
        overlapping = self._get_timesheet_overlapping_leaves()
        if overlapping is None:
            return  # project_timesheet_holidays is not installed
        if previous:
            overlapping |= previous
        if not overlapping:
            return
        overlapping.sudo()._generate_timesheets()
        global_leaves = self.filtered(lambda leave: not leave.resource_id)
        if not global_leaves:
            return
        # The day just freed on the leave is a public holiday, so it has to be
        # accounted as one. `_timesheet_create_lines` skipped it a moment ago
        # because the leave still spans it, and it always will: only the
        # duration of a leave shrinks, never the period it was requested for.
        global_leaves.sudo()._generate_public_time_off_timesheets(
            overlapping.employee_id
        )

    def _get_public_holiday_managed_error(self, managed=None):
        details = ""
        if managed:
            details = "\n" + "\n".join(
                f"- {leave.display_name} ({leave.public_holiday_line_id.display_name})"
                for leave in managed
            )
        return self.env._(
            "Time off entries generated from a public holiday cannot be "
            "created or modified directly. Edit the public holiday "
            "instead.%s",
            details,
        )

    def _check_public_holiday_managed(self):
        """Managed mirrors may only be touched by the synchronisation itself."""
        if self.env.context.get("public_holiday_sync"):
            return
        managed = self.filtered("public_holiday_line_id")
        if managed:
            raise UserError(self._get_public_holiday_managed_error(managed))

    def write(self, vals):
        self._check_public_holiday_managed()
        if "company_id" in vals:
            return super().write(vals)
        managed = (
            self
            if vals.get("public_holiday_line_id")
            else self.filtered("public_holiday_line_id")
        )
        if not managed:
            return super().write(vals)
        moved = managed if vals.keys() & {"date_from", "date_to"} else managed.browse()
        previous = moved._get_timesheet_overlapping_leaves() if moved else None
        # A generated record belongs to the company it was generated for.
        # Standard recomputes `company_id` whenever the dates change -- the
        # schedule is computed from the dates and the company from the
        # schedule -- and, without a company-owned schedule, falls back to the
        # current company. Moving a public holiday would therefore pull the
        # company-wide record of every other company over to the current one,
        # where it collides with that company's own record of the same line.
        # The synchronisation pins the company itself wherever it matters.
        with self.env.protecting([self._fields["company_id"]], managed):
            res = super().write(vals)
        if moved:
            moved._adapt_overlapping_leave_timesheets(previous)
        return res

    def unlink(self):
        self._check_public_holiday_managed()
        return super().unlink()
