# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResourceBookingType(models.Model):
    _name = "resource.booking.type"
    _inherit = ["resource.booking.type", "website.published.mixin"]

    website_slug = fields.Char(
        compute="_compute_website_slug",
        store=True,
        readonly=False,
        copy=False,
        help="URL-friendly identifier used in the public booking page URL. "
        "Auto-generated from the name, but can be customized.",
    )
    website_description = fields.Html(
        translate=True,
        sanitize_attributes=False,
        help="Introductory text displayed on the public booking page.",
    )

    _sql_constraints = [
        (
            "website_slug_unique",
            "UNIQUE(website_slug)",
            "The website slug must be unique.",
        ),
    ]

    def _slugify(self, value):
        """URL-safe version of ``value`` (platform rules: ascii, lowercase, dashes)."""
        return self.env["ir.http"]._slugify(value or "")

    @api.depends("name")
    def _compute_website_slug(self):
        for record in self:
            if not record.website_slug and record.name:
                record.website_slug = self._slugify(record.name)

    @api.depends("website_slug")
    def _compute_website_url(self):
        result = super()._compute_website_url()
        for record in self.filtered("website_slug"):
            record.website_url = f"/book/{record.website_slug}"
        return result

    @api.constrains("is_published", "website_slug")
    def _check_published_has_slug(self):
        for record in self:
            if record.is_published and not record.website_slug:
                raise ValidationError(
                    self.env._(
                        "A website slug is required to publish '%(name)s'.",
                        name=record.display_name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("website_slug"):
                vals["website_slug"] = self._slugify(vals["website_slug"])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("website_slug"):
            vals = dict(vals, website_slug=self._slugify(vals["website_slug"]))
        return super().write(vals)
