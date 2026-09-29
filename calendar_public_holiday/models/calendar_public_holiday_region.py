# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CalendarPublicHolidayRegion(models.Model):
    """A place of work, as far as public holidays are concerned.

    Public holidays only need a label to assign days by -- the Catholic
    municipalities of Bavaria, one plant, one shop. A public holiday line
    names the regions it applies to; a line naming none is nationwide.
    Which people belong to a region is left to the modules that know
    about people.
    """

    _name = "calendar.public.holiday.region"
    _description = "Public Holiday Region"
    _order = "name"

    name = fields.Char(required=True)
    country_id = fields.Many2one(
        "res.country",
        help="The public holiday calendars of this country apply to the "
        "region. Leave empty to apply the calendars of every country.",
    )
    company_id = fields.Many2one(
        "res.company",
        help="Leave empty for a region shared by every company.",
    )
    active = fields.Boolean(default=True)
    public_holiday_line_ids = fields.Many2many(
        "calendar.public.holiday.line",
        "calendar_public_holiday_line_region_rel",
        "region_id",
        "line_id",
        string="Public Holidays",
        help="Public holidays everybody at this region gets, on top of "
        "the nationwide ones.",
    )
    public_holiday_overview_line_ids = fields.Many2many(
        "calendar.public.holiday.line",
        string="Public Holiday Overview",
        compute="_compute_public_holiday_overview_line_ids",
        help="Every public holiday somebody at this region gets: the "
        "nationwide ones and the ones assigned to the region directly.",
    )

    def _matches_public_holiday_country(self, line):
        """Whether the public holiday calendar of ``line`` applies here.

        The country of the region decides, not the one of its company. An
        unknown country cannot rule a calendar out -- refusing it there
        would silently apply nothing at all, which is the far worse
        failure -- and a calendar without a country applies everywhere.
        """
        self.ensure_one()
        holiday_country = line.public_holiday_id.country_id
        if not holiday_country or not self.country_id:
            return True
        return holiday_country == self.country_id

    @api.depends("country_id", "public_holiday_line_ids")
    def _compute_public_holiday_overview_line_ids(self):
        line_model = self.env["calendar.public.holiday.line"]
        # The always-true leaf keeps the no-search-all check quiet.
        lines = line_model.search([("id", "!=", 0)])
        nationwide = lines.filtered(lambda line: not line._has_public_holiday_scope())
        for region in self:
            reachable = nationwide | region.public_holiday_line_ids
            region.public_holiday_overview_line_ids = reachable.filtered(
                region._matches_public_holiday_country
            )
