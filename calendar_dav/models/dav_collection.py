from odoo import models


class DavCollection(models.Model):
    _inherit = "dav.collection"

    def dav_list(self, collection, path_components):
        result = super().dav_list(collection, path_components)
        if self.model_id.model != "calendar.event":
            return result
        records = self.eval_domain_records()
        uuids_to_keep = set()
        for record in records:
            is_base = not record.follow_recurrence or (
                record.recurrence_id
                and record.recurrence_id.base_event_id.id == record.id
            )
            if is_base:
                uuid = (
                    str(record[self.field_uuid.name])
                    if self.field_uuid
                    else str(record.id)
                )
                uuids_to_keep.add(uuid)
        return list(
            dict.fromkeys(r for r in result if r.split("/")[-1] in uuids_to_keep)
        )

    def get_record(self, components):
        record = super().get_record(components)
        if not record or self.model_id.model != "calendar.event":
            return record
        if record.recurrence_id and record.recurrence_id.base_event_id:
            return record.recurrence_id.base_event_id
        return record

    def _get_write_vals(self, record, data):
        data = super()._get_write_vals(record, data)
        if self.model_id.model == "calendar.event" and record.recurrence_id:
            data["recurrence_update"] = "all_events"
        return data

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
                    if rec.recurrence_id:
                        # we update all recurring events
                        all_atts = rec.recurrence_id.calendar_event_ids.mapped(
                            "attendee_ids"
                        ).filtered(lambda a: a.partner_id.email == user_email)
                        all_atts.write({"state": state})
                    else:
                        att.write({"state": state})
            break
        return result
