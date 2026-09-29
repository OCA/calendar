# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestPublicHolidayResourceCommon


class TestLineActive(TestPublicHolidayResourceCommon):
    """A disabled public holiday line generates no time off.

    The guard for a line whose scope is gone: one assigned to regions that
    no longer exist would fall back to applying to everybody, so it can be
    switched off entirely instead. The flag itself lives in
    ``calendar_public_holiday``; what is asserted here is its effect on the
    generated time off.
    """

    def test_deactivating_removes_the_mirrors(self):
        line = self._create_line(date(self.year, 10, 3))
        self.assertTrue(self._mirrors(line))
        line.active = False
        self.assertFalse(self._mirrors(line))

    def test_reactivating_recreates_the_mirrors(self):
        line = self._create_line(date(self.year, 10, 3))
        line.active = False
        line.active = True
        self.assertTrue(self._company_mirror(line))

    def test_deactivating_removes_the_resource_mirrors(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertTrue(self._mirrors(line, self.cal_by))
        line.active = False
        self.assertFalse(self._mirrors(line))

    def test_deactivating_a_national_line_restores_the_regional_rival(self):
        day = date(self.year, 10, 3)
        regional = self._create_line(day, name="Regional", regions=self.region_by)
        national = self._create_line(day, name="National")
        self.assertFalse(self._mirrors(regional))
        national.active = False
        self.assertTrue(self._mirrors(regional, self.cal_by))

    def test_a_disabled_line_is_not_reported_as_an_issue(self):
        line = self._create_line(date(self.year, 10, 3))
        line.active = False
        summary = line._sync_global_leaves(dry_run=True)
        self.assertFalse(summary["issues"])

    def test_the_cron_cleans_up_a_stale_disabled_line(self):
        """Self-healing must reach disabled lines too.

        A line disabled while the module was not installed keeps its mirrors
        until the next synchronisation looks at it; the cron therefore walks
        the lines regardless of their active flag.
        """
        line = self._create_line(date(self.year, 10, 3))
        mirrors = self._mirrors(line)
        self.assertTrue(mirrors)
        # Straight through SQL, as if the sync had never seen the change.
        self.env.cr.execute(
            "UPDATE calendar_public_holiday_line SET active = FALSE WHERE id = %s",
            (line.id,),
        )
        line.invalidate_recordset(["active"])
        self.line_model._cron_sync_global_leaves()
        self.assertFalse(self._mirrors(line))
