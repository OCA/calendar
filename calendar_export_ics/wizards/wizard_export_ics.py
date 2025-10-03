# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import base64
from datetime import date

import vobject

from odoo import api, fields, models


class CalendarExportIcs(models.TransientModel):
    """
    This wizard is used to export odoo calendar to ics file
    """

    _name = "calendar.export.ics"
    _description = "Calendar Export Ics"

    export_ics_file = fields.Binary("Ics Exported File")
    export_ics_filename = fields.Char(readonly=True)
    export_end_date = fields.Date("End Export Date")
    partner_id = fields.Many2one("res.partner", string="Partner")

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)
        user = self.env.user
        if user.partner_id:
            defaults["partner_id"] = user.partner_id.id
        return defaults

    def button_export(self):
        today_date = date.today()
        self.export_ics_filename = today_date.strftime("%Y-%m-%d") + "_calendar.ics"
        self.export_ics_file = self.generate_ics_content()

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "calendar.export.ics",
            "name": "Export to Ics File",
            "target": "new",
            "res_id": self.id,
        }

    def generate_ics_content(self):
        domain = []
        if self.export_end_date:
            domain.append(("start", "<=", self.export_end_date))
        domain.append(("start", ">=", date.today()))
        domain.append(("partner_ids", "in", [self.partner_id.id]))
        events = self.env["calendar.event"].search(domain)

        individual_ics_files = events._get_ics_file()
        combined_cal = vobject.iCalendar()

        for ics_content in individual_ics_files.values():
            cal = vobject.readOne(ics_content.decode("utf-8"))
            for event in cal.vevent_list:
                combined_cal.add(event)

        combined_ics_content = combined_cal.serialize().encode("utf-8")
        return base64.b64encode(combined_ics_content)
