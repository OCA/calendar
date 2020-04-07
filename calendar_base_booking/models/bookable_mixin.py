# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.osv import expression

# Concept
# open_slot is the range of time where the ressource can be book
# available_slot is the range of time where the ressource is available for booking
# booked_slot is a slot already booked
# bookable_slot is a slot (with a size if slot_duration) that fit into
# an available slot


class BookableMixin(models.AbstractModel):
    _name = "bookable.mixin"
    _description = "Bookable Mixin"

    slot_duration = fields.Float()
    slot_capacity = fields.Integer()

    def _get_slot_duration(self):
        return self.slot_duration

    def _get_slot_capacity(self):
        return self.slot_capacity

    def _get_booked_slot(self, start, stop):
        domain = self._get_domain(start, stop)
        return self.env["calendar.event"].search(
            expression.AND([domain, [("booking_type", "=", "booked")]])
        )

    def _build_timeline_load(self, start, stop):
        timeline = defaultdict(int)
        timeline.update({start: 0, stop: 0})
        for booked_slot in self._get_booked_slot(start, stop):
            if booked_slot.start < start:
                timeline[start] += 1
            else:
                timeline[booked_slot.start] += 1
            if booked_slot.stop < stop:
                timeline[booked_slot.stop] -= 1

        timeline = list(timeline.items())
        timeline.sort()
        return timeline

    def _get_available_slot(self, start, stop):
        load_timeline = self._build_timeline_load(start, stop)

        load = 0
        slots = []
        slot = None
        capacity = self._get_slot_capacity()

        for dt, load_delta in load_timeline:
            load += load_delta
            if not slot and load < capacity:
                slot = [dt, None]
                slots.append(slot)
            elif slot and load >= capacity:
                slot = None
            else:
                slot[1] = dt
        return slots

    def _prepare_bookable_slot(self, open_slot, start, stop):
        # If need you can inject extra information from the open_slot
        return {"start": start, "stop": stop}

    def _build_bookable_slot(self, open_slot, start, stop):
        bookable_slots = []
        # now we have to care about datetime vs string
        delta = self._get_slot_duration()
        while True:
            slot_stop = start + relativedelta(minutes=delta)
            if slot_stop > stop:
                break
            bookable_slots.append(
                self._prepare_bookable_slot(open_slot, start, slot_stop)
            )
            start += relativedelta(minutes=delta)
        return bookable_slots

    def get_bookable_slot(self, start, stop):
        start = fields.Datetime.to_datetime(start)
        stop = fields.Datetime.to_datetime(stop)

        slots = []
        domain = self._get_domain(start, stop)
        available_domain = expression.AND([domain, [("booking_type", "=", "bookable")]])
        for open_slot in self.env["calendar.event"].search(
            available_domain, order="start_date"
        ):
            for slot_start, slot_stop in self._get_available_slot(
                max(open_slot.start, start), min(open_slot.stop, stop)
            ):
                slots += self._build_bookable_slot(open_slot, slot_start, slot_stop)
        return slots

    def _get_domain(self, start, stop):
        # be carefull we need to search for every slot (bookable and booked)
        # that exist in the range start/stop
        # This mean that we need the slot
        # - started before and finishing in the range
        # - started and finished in the range
        # - started in the range and fisnish after
        # In an other expression it's
        # - all slot that start in the range
        # - all slot that finish in the range
        return [
            ("res_model", "=", self._name),
            ("res_id", "=", self.id),
            "|",
            "&",
            ("start", ">=", start),
            ("start", "<", stop),
            "&",
            ("stop", ">", start),
            ("stop", "<=", stop),
        ]
