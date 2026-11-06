# Copyright 2026 Thierry Leblanc
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PortalEntry(models.Model):
    _inherit = "portal.entry"

    def _filter_visible_portal_cards(self):
        """Show the bookings card to users allowed to read bookings.

        Odoo 20 hides business cards by default; only configuration cards are
        visible unless a module explicitly adds its own entry.
        """
        visible_entries = super()._filter_visible_portal_cards()
        bookings_entry = self.env.ref(
            "resource_booking.portal_entry_bookings", raise_if_not_found=False
        )
        if bookings_entry and bookings_entry in self:
            if self.env["resource.booking"].has_access("read"):
                visible_entries |= bookings_entry
            else:
                visible_entries -= bookings_entry
        return visible_entries
