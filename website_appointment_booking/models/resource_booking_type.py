# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models


def _slugify(value):
    """Convert a string to a URL-friendly slug."""
    value = (value or "").lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value)
    return value.strip("-")


class ResourceBookingType(models.Model):
    _inherit = "resource.booking.type"

    website_published = fields.Boolean(
        copy=False,
        help="When checked, this booking type will be available on a public "
        "booking page accessible without login.",
    )
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

    @api.depends("name")
    def _compute_website_slug(self):
        for record in self:
            if not record.website_slug and record.name:
                record.website_slug = _slugify(record.name)
