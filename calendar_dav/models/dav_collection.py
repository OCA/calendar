# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class DavCollection(models.Model):
    _inherit = "dav.collection"

    def dav_upload(self, collection, href, item):
        result = super().dav_upload(collection, href, item)
        if self.model_id.model != "calendar.event":
            return result
        if not hasattr(item, "vevent"):
            return result
        user_email = self.env.user.partner_id.email
        for attendee_item in item.vevent.contents.get("attendee", []):
            email = attendee_item.value.replace("mailto:", "").strip()
            if email != user_email:
                continue
            partstat = attendee_item.params.get("PARTSTAT", ["NEEDS-ACTION"])[0]
            state = {
                "NEEDS-ACTION": "needsAction",
                "ACCEPTED": "accepted",
                "DECLINED": "declined",
                "TENTATIVE": "tentative",
            }.get(partstat, "needsAction")
            components = self._split_path(href)
            rec = self.get_record(components)
            if rec:
                att = rec.attendee_ids.filtered(
                    lambda a: a.partner_id.email == user_email
                )
                if att:
                    att.write({"state": state})
            break
        return result
