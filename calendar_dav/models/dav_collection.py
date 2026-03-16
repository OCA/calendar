from odoo import models


class DavCollection(models.Model):
    _inherit = "dav.collection"

    def from_vobject(self, item):
        result = super().from_vobject(item)
        if result and self.model_id.model == "calendar.event":
            if (
                "start" in result
                and result["start"]
                and " " not in str(result["start"])
            ):
                result["allday"] = True
        return result
