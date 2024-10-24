# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class CalendarEventLinkMixin(models.AbstractModel):

    _name = "calendar.event.link.mixin"
    _description = "Calendar Event Link Mixin"

    event_count = fields.Integer(compute="_compute_event_count")

    def _compute_event_count(self):
        mapped_data = self.env["calendar.event"].read_group(
            [("res_model", "=", self._name), ("res_id", "in", self.ids)],
            ["id"],
            ["res_id"],
        )
        data = {x["res_id"]: x for x in mapped_data}
        for record in self:
            record.event_count = data.get(record.id, {}).get("res_id_count", 0)

    def action_show_events(self):
        self.ensure_one()
        context = {
            "default_res_id": self.id,
            "default_res_model": self._name,
            "default_name": self.name_get()[0][1],
        }
        context.update(self.env.context)
        return {
            "type": "ir.actions.act_window",
            "name": _("Calendar"),
            "res_model": "calendar.event",
            "domain": [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
            ],
            "view_mode": "calendar,tree,form",
            "context": context,
        }
