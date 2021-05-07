# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class CalendarEventLinkMixin(models.AbstractModel):

    _name = "calendar.event.link.mixin"
    _description = "Calendar Event Link Mixin"

    event_count = fields.Integer(compute="_compute_event_count")

    @api.multi
    def _compute_event_count(self):
        for x in self.env["calendar.event"].read_group(
            [("res_model", "=", self._name), ("res_id", "in", self.ids)],
            ["id"],
            ["res_id"],
        ):
            self.browse(x["res_id"]).update({"event_count": x["res_id_count"]})

    @api.multi
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
