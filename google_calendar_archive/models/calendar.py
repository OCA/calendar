# Copyright 2021 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Meeting(models.Model):
    _inherit = "calendar.event"

    def unlink(self):
        if self.env.context.get("guard_unlink_recursion"):
            return super().unlink()
        synced = self.filtered("google_id")
        not_synced = self - synced
        super(Meeting, synced).with_context(
            archive_on_error=True, guard_unlink_recursion=True
        ).unlink()
        super(Meeting, not_synced).with_context(guard_unlink_recursion=True).unlink()
