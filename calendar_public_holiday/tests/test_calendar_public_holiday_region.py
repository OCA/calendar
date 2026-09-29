# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext, mute_logger

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.calendar_public_holiday.hooks import (
    assign_regions_from_legacy_states,
    disable_lines_with_legacy_states,
)


class TestCalendarPublicHolidayRegion(BaseCommon):
    """Public holidays scoped to regions rather than country states."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.holiday_model = cls.env["calendar.public.holiday"]
        cls.line_model = cls.env["calendar.public.holiday.line"]
        cls.region_model = cls.env["calendar.public.holiday.region"]
        cls.line_model.search([]).unlink()
        cls.holiday_model.search([]).unlink()
        cls.country = cls.env["res.country"].create({"name": "Country A", "code": "XA"})
        cls.other_country = cls.env["res.country"].create(
            {"name": "Country B", "code": "XB"}
        )
        cls.year = 2025
        cls.holiday = cls.holiday_model.create(
            {"year": cls.year, "country_id": cls.country.id}
        )
        cls.region = cls.region_model.create({"name": "Augsburg"})
        cls.region_other = cls.region_model.create({"name": "Munich"})
        cls.national = cls._create_line(date(cls.year, 10, 3), "Nationwide")
        cls.scoped = cls._create_line(
            date(cls.year, 8, 8), "Friedensfest", regions=cls.region
        )

    @classmethod
    def _create_line(cls, day, name, regions=None, holiday=None):
        return cls.line_model.create(
            {
                "name": name,
                "date": day,
                "public_holiday_id": (holiday or cls.holiday).id,
                "region_ids": [Command.set(regions.ids)] if regions else False,
            }
        )

    # ------------------------------------------------------------------
    # Scope
    # ------------------------------------------------------------------

    def test_nationwide_lines_apply_without_a_region(self):
        lines = self.holiday_model.get_holidays_list(self.year)
        self.assertIn(self.national, lines)
        self.assertNotIn(self.scoped, lines)

    def test_scoped_lines_apply_at_their_regions(self):
        lines = self.holiday_model.get_holidays_list(
            self.year, region_ids=self.region.ids
        )
        self.assertIn(self.national, lines, "nationwide lines always apply")
        self.assertIn(self.scoped, lines)
        elsewhere = self.holiday_model.get_holidays_list(
            self.year, region_ids=self.region_other.ids
        )
        self.assertNotIn(self.scoped, elsewhere)

    def test_is_public_holiday_honours_the_region(self):
        day = date(self.year, 8, 8)
        self.assertFalse(self.holiday_model.is_public_holiday(day))
        self.assertTrue(
            self.holiday_model.is_public_holiday(day, region_ids=self.region.ids)
        )

    def test_a_scoped_line_is_no_nationwide_duplicate(self):
        # Must not raise: the scoped line is not a duplicate of the
        # nationwide one on the same date.
        self._create_line(date(self.year, 10, 3), "Regional", regions=self.region)

    def test_duplicate_region_on_one_date_raises(self):
        with self.assertRaises(ValidationError):
            self._create_line(date(self.year, 8, 8), "Doubled", regions=self.region)

    def test_clearing_the_regions_makes_the_duplicate_visible(self):
        regional = self._create_line(
            date(self.year, 10, 3), "Regional", regions=self.region
        )
        with self.assertRaises(ValidationError):
            regional.region_ids = [Command.clear()]

    def test_has_public_holiday_scope(self):
        self.assertFalse(self.national._has_public_holiday_scope())
        self.assertTrue(self.scoped._has_public_holiday_scope())

    def test_meeting_describes_the_regions(self):
        self.assertEqual(html2plaintext(self.scoped.meeting_id.description), "Augsburg")
        self.scoped.region_ids = [Command.link(self.region_other.id)]
        self.assertEqual(
            html2plaintext(self.scoped.meeting_id.description), "Augsburg, Munich"
        )

    # ------------------------------------------------------------------
    # Region overview
    # ------------------------------------------------------------------

    def _overview(self, region):
        region.invalidate_recordset(["public_holiday_overview_line_ids"])
        return region.public_holiday_overview_line_ids

    def test_overview_lists_nationwide_and_assigned_lines(self):
        self.assertIn(self.national, self._overview(self.region))
        self.assertIn(self.scoped, self._overview(self.region))
        self.assertIn(self.national, self._overview(self.region_other))
        self.assertNotIn(self.scoped, self._overview(self.region_other))

    def test_overview_rules_out_another_country(self):
        region = self.region_model.create(
            {"name": "B plant", "country_id": self.other_country.id}
        )
        self.assertNotIn(self.national, self._overview(region))
        worldwide = self._create_line(
            date(self.year, 1, 1),
            "Worldwide",
            holiday=self.holiday_model.create({"year": self.year}),
        )
        self.assertIn(worldwide, self._overview(region))

    def test_overview_follows_the_region_country_not_the_company(self):
        """The company's country says nothing once the region has its own."""
        self.env.company.country_id = self.other_country
        region = self.region_model.create(
            {
                "name": "A plant",
                "country_id": self.country.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertIn(self.national, self._overview(region))

    def test_matches_public_holiday_country(self):
        here = self.region_model.create({"name": "Here", "country_id": self.country.id})
        there = self.region_model.create(
            {"name": "There", "country_id": self.other_country.id}
        )
        anywhere = self.region_model.create({"name": "Anywhere"})
        self.assertTrue(here._matches_public_holiday_country(self.national))
        self.assertFalse(there._matches_public_holiday_country(self.national))
        self.assertTrue(anywhere._matches_public_holiday_country(self.national))
        worldwide = self._create_line(
            date(self.year, 1, 1),
            "Worldwide",
            holiday=self.holiday_model.create({"year": self.year}),
        )
        self.assertTrue(there._matches_public_holiday_country(worldwide))

    def test_get_holidays_list_country_wins_over_the_partner(self):
        partner = self.env["res.partner"].create(
            {"name": "Abroad", "country_id": self.other_country.id}
        )
        self.assertNotIn(
            self.national,
            self.holiday_model.get_holidays_list(self.year, partner_id=partner.id),
        )
        self.assertIn(
            self.national,
            self.holiday_model.get_holidays_list(
                self.year, partner_id=partner.id, country_id=self.country.id
            ),
        )
        self.assertTrue(
            self.holiday_model.is_public_holiday(
                date(self.year, 10, 3),
                partner_id=partner.id,
                country_id=self.country.id,
            )
        )

    def test_overview_is_readonly(self):
        field = self.region_model._fields["public_holiday_overview_line_ids"]
        self.assertTrue(field.compute)
        self.assertTrue(field.readonly)
        self.assertFalse(field.store)

    # ------------------------------------------------------------------
    # Disabled lines
    # ------------------------------------------------------------------

    def test_a_disabled_line_is_ignored(self):
        self.national.active = False
        self.assertNotIn(self.national, self.holiday_model.get_holidays_list(self.year))

    def test_a_disabled_line_stays_on_the_holiday_form(self):
        """The one2many keeps archived lines, or nobody could re-enable them."""
        self.national.active = False
        self.assertIn(self.national, self.holiday.line_ids)

    def test_the_next_year_copy_carries_regions_and_the_disabled_flag(self):
        self.national.active = False
        self.env["calendar.public.holiday.next.year"].create(
            {"public_holiday_ids": [Command.set(self.holiday.ids)]}
        ).create_public_holidays()
        copies = self.line_model.with_context(active_test=False).search(
            [("public_holiday_id.year", "=", self.year + 1)]
        )
        national_copy = copies.filtered(lambda line: line.name == "Nationwide")
        scoped_copy = copies.filtered(lambda line: line.name == "Friedensfest")
        self.assertEqual(len(national_copy), 1)
        self.assertFalse(
            national_copy.active,
            "a disabled line must not come back to life in the new year",
        )
        self.assertEqual(scoped_copy.region_ids, self.region)

    # ------------------------------------------------------------------
    # Display name
    # ------------------------------------------------------------------

    def test_line_names_year_and_country(self):
        self.assertEqual(
            self.national.display_name, f"Nationwide ({self.year} - Country A)"
        )

    def test_line_without_a_country_names_the_year_only(self):
        line = self._create_line(
            date(self.year, 1, 2),
            "Plain",
            holiday=self.holiday_model.create({"year": self.year}),
        )
        self.assertEqual(line.display_name, f"Plain ({self.year})")

    def test_line_tells_years_apart(self):
        next_year = self.holiday_model.create(
            {"year": self.year + 1, "country_id": self.country.id}
        )
        next_one = self._create_line(
            date(self.year + 1, 10, 3), "Nationwide", holiday=next_year
        )
        self.assertNotEqual(self.national.display_name, next_one.display_name)
        self.assertNotIn("((", self.national.display_name)

    def test_empty_regions_show_their_placeholder(self):
        """While editing, an empty cell reads as "applies everywhere"."""
        arch = self.env.ref(
            "calendar_public_holiday.view_calendar_public_holiday_form"
        ).get_combined_arch()
        self.assertIn('placeholder="All Regions"', arch)


class TestLegacyStateAssignment(BaseCommon):
    """Upgrading gives the lines once scoped to states the regions of those states.

    Regions only exist for the places people work at, which this module
    does not know: it disables a line whose states no region stands for,
    and a module knowing those places hands it the regions lying in its
    states. The legacy relation is a table no model owns any more, so it
    is planted by SQL the way an upgraded database carries it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.holiday_model = cls.env["calendar.public.holiday"]
        cls.line_model = cls.env["calendar.public.holiday.line"]
        cls.region_model = cls.env["calendar.public.holiday.region"]
        cls.line_model.search([]).unlink()
        cls.holiday_model.search([]).unlink()
        cls.country = cls.env["res.country"].create({"name": "Country C", "code": "XC"})
        cls.other_country = cls.env["res.country"].create(
            {"name": "Country D", "code": "XD"}
        )
        cls.state_by = cls.env["res.country.state"].create(
            {"name": "Bayern", "code": "BY", "country_id": cls.country.id}
        )
        cls.state_nw = cls.env["res.country.state"].create(
            {"name": "Nordrhein", "code": "NW", "country_id": cls.country.id}
        )
        # A third state, so that Bayern and Nordrhein together are not the
        # whole country.
        cls.state_he = cls.env["res.country.state"].create(
            {"name": "Hessen", "code": "HE", "country_id": cls.country.id}
        )
        # A state of another country sharing a name with one of this one --
        # and a second state there, so that it is not the whole country.
        cls.state_twin = cls.env["res.country.state"].create(
            {"name": "Bayern", "code": "BY", "country_id": cls.other_country.id}
        )
        cls.env["res.country.state"].create(
            {"name": "Elsewhere", "code": "EW", "country_id": cls.other_country.id}
        )
        cls.holiday = cls.holiday_model.create(
            {"year": 2025, "country_id": cls.country.id}
        )
        cls.line_by = cls._create_line(date(2025, 6, 19), "Fronleichnam")
        cls.line_both = cls._create_line(date(2025, 11, 1), "Allerheiligen")
        cls.line_national = cls._create_line(date(2025, 10, 3), "Nationwide")
        cls.line_twin = cls._create_line(
            date(2025, 8, 15),
            "Twin",
            holiday=cls.holiday_model.create(
                {"year": 2025, "country_id": cls.other_country.id}
            ),
        )
        cls.munich = cls._create_region("Munich office", cls.country)
        cls.nuremberg = cls._create_region("Nuremberg office", cls.country)
        cls.cologne = cls._create_region("Cologne office", cls.country)
        cls.twin_office = cls._create_region("Twin office", cls.other_country)

    def setUp(self):
        super().setUp()
        # The hooks report what they did as an upgrade would; the tests
        # assert it instead.
        self.enterContext(mute_logger("odoo.addons.calendar_public_holiday.hooks"))

    @classmethod
    def _create_line(cls, day, name, holiday=None):
        return cls.line_model.create(
            {
                "name": name,
                "date": day,
                "public_holiday_id": (holiday or cls.holiday).id,
            }
        )

    @classmethod
    def _create_region(cls, name, country):
        return cls.region_model.create({"name": name, "country_id": country.id})

    def _regions_by_state(self):
        """What a module knowing the places of work would resolve."""
        return {
            self.state_by.id: self.munich | self.nuremberg,
            self.state_nw.id: self.cologne,
            self.state_twin.id: self.twin_office,
        }

    def _plant_legacy_states(self, pairs):
        # The table may still exist on an upgraded database, constraints and
        # all; it is rebuilt bare so that a dangling row can be planted. The
        # DDL is rolled back with the test transaction like the rows.
        self.env.cr.execute("DROP TABLE IF EXISTS public_holiday_state_rel")
        self.env.cr.execute(
            "CREATE TABLE public_holiday_state_rel "
            "(public_holiday_line_id integer, state_id integer)"
        )
        for line, state in pairs:
            self.env.cr.execute(
                "INSERT INTO public_holiday_state_rel VALUES (%s, %s)",
                (line.id, state.id),
            )

    def test_no_legacy_table_is_a_noop(self):
        self.env.cr.execute("DROP TABLE IF EXISTS public_holiday_state_rel")
        self.assertFalse(disable_lines_with_legacy_states(self.env))
        self.assertFalse(
            assign_regions_from_legacy_states(self.env, self._regions_by_state())
        )
        self.assertFalse(self.line_by.region_ids)
        self.assertTrue(self.line_by.active)

    def test_a_state_scoped_line_is_disabled_until_it_has_a_region(self):
        self._plant_legacy_states([(self.line_by, self.state_by)])
        before = self.region_model.search_count([])
        disabled = disable_lines_with_legacy_states(self.env)
        self.assertEqual(disabled, self.line_by)
        self.assertEqual(self.region_model.search_count([]), before, "none created")
        self.assertFalse(self.line_by.active, "disabled rather than nationwide")
        self.assertTrue(self.line_national.active, "untouched")
        self.assertFalse(disable_lines_with_legacy_states(self.env), "already disabled")

    def test_a_line_that_already_has_a_region_is_not_disabled(self):
        self.line_by.region_ids = [Command.link(self.munich.id)]
        self._plant_legacy_states([(self.line_by, self.state_by)])
        self.assertFalse(disable_lines_with_legacy_states(self.env))
        self.assertTrue(self.line_by.active)

    def test_lines_get_the_regions_of_their_states(self):
        self._plant_legacy_states(
            [
                (self.line_by, self.state_by),
                (self.line_both, self.state_by),
                (self.line_both, self.state_nw),
            ]
        )
        assigned = assign_regions_from_legacy_states(self.env, self._regions_by_state())
        self.assertEqual(assigned, self.line_by | self.line_both)
        self.assertEqual(self.line_by.region_ids, self.munich | self.nuremberg)
        self.assertEqual(
            self.line_both.region_ids, self.munich | self.nuremberg | self.cologne
        )
        self.assertFalse(self.line_national.region_ids, "left nationwide")

    def test_a_disabled_line_is_enabled_once_it_receives_a_region(self):
        self._plant_legacy_states([(self.line_by, self.state_by)])
        disable_lines_with_legacy_states(self.env)
        self.assertFalse(self.line_by.active)
        assign_regions_from_legacy_states(self.env, {})
        self.assertFalse(self.line_by.active, "still nothing stands for it")
        assign_regions_from_legacy_states(self.env, self._regions_by_state())
        self.assertTrue(self.line_by.active)

    def test_the_assignment_is_idempotent(self):
        self._plant_legacy_states([(self.line_by, self.state_by)])
        first = assign_regions_from_legacy_states(self.env, self._regions_by_state())
        self.assertEqual(first, self.line_by)
        self.assertFalse(
            assign_regions_from_legacy_states(self.env, self._regions_by_state()),
            "nothing new",
        )
        self.assertEqual(self.line_by.region_ids, self.munich | self.nuremberg)

    def test_a_state_name_shared_across_countries_is_told_apart(self):
        """The state itself matches, not its name."""
        self._plant_legacy_states(
            [(self.line_by, self.state_by), (self.line_twin, self.state_twin)]
        )
        assign_regions_from_legacy_states(self.env, self._regions_by_state())
        self.assertEqual(self.line_by.region_ids, self.munich | self.nuremberg)
        self.assertEqual(self.line_twin.region_ids, self.twin_office)

    def test_every_state_of_the_country_means_nationwide(self):
        """Selecting all states was the same as selecting none."""
        self._plant_legacy_states(
            [
                (self.line_by, self.state_by),
                (self.line_both, self.state_by),
                (self.line_both, self.state_nw),
                (self.line_both, self.state_he),
            ]
        )
        disable_lines_with_legacy_states(self.env)
        self.assertTrue(self.line_both.active, "the whole country")
        assign_regions_from_legacy_states(self.env, self._regions_by_state())
        self.assertFalse(self.line_both.region_ids)
        self.assertEqual(self.line_by.region_ids, self.munich | self.nuremberg)

    def test_a_dangling_legacy_row_is_skipped(self):
        gone = self._create_line(date(2025, 1, 6), "Gone")
        gone_id = gone.id
        gone.unlink()
        self._plant_legacy_states(
            [
                (self.line_by, self.state_by),
                (self.line_by.browse(gone_id), self.state_by),
            ]
        )
        assigned = assign_regions_from_legacy_states(self.env, self._regions_by_state())
        self.assertEqual(assigned, self.line_by)
