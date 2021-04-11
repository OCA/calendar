from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"
    _active_name = "active"

    active = fields.Boolean(default=True)
    recurrence_id = fields.Many2one("calendar.recurrence", "Event recurrence")
    follow_recurrence = fields.Boolean(default=False)
    rrule = fields.Char(related="recurrence_id.rrule", store=True, readonly=False)
    byday = fields.Selection(related="recurrence_id.byday", store=True, readonly=False)
    final_date = fields.Date(related="recurrence_id.until", store=True, readonly=False)
    rrule_type = fields.Selection(
        related="recurrence_id.rrule_type", store=True, readonly=False
    )
    month_by = fields.Selection(
        related="recurrence_id.month_by", store=True, readonly=False
    )
    interval = fields.Integer(
        related="recurrence_id.interval", store=True, readonly=False
    )
    count = fields.Integer(related="recurrence_id.count", store=True, readonly=False)
    end_type = fields.Selection(
        related="recurrence_id.end_type", store=True, readonly=False
    )
    mo = fields.Boolean(related="recurrence_id.mo", store=True, readonly=False)
    tu = fields.Boolean(related="recurrence_id.tu", store=True, readonly=False)
    we = fields.Boolean(related="recurrence_id.we", store=True, readonly=False)
    th = fields.Boolean(related="recurrence_id.th", store=True, readonly=False)
    fr = fields.Boolean(related="recurrence_id.fr", store=True, readonly=False)
    sa = fields.Boolean(related="recurrence_id.sa", store=True, readonly=False)
    su = fields.Boolean(related="recurrence_id.su", store=True, readonly=False)
    day = fields.Integer(related="recurrence_id.day", store=True, readonly=False)
    week_list = fields.Selection(
        related="recurrence_id.weekday", store=True, readonly=False
    )

    def _range(self):
        self.ensure_one()
        return (self.start, self.stop)

    @api.model
    def _get_time_fields(self):
        return {"start", "stop", "start_date", "stop_date"}

    def _create_recurrence_from_vals(self, vals):
        recurrence_vals = {
            self._fields.get(name).related[1]: value
            for name, value in vals.items()
            if self._fields.get(name)
            and self._fields.get(name).related
            and self._fields.get(name).related[0] == "recurrence_id"
        }
        if (
            recurrence_vals
            and "recurrence_id" not in vals
            and any(recurrence_vals.values())
        ):
            # writing recurrence vals needs a recurrence_id set, so we
            # create them for records that dont have one
            default_vals = self.env["calendar.recurrence"].default_get(
                self.env["calendar.recurrence"]._fields
            )
            default_vals["rrule_type"] = "daily"
            for this in self:
                if this.recurrence_id:
                    continue

                recurrence = self.env["calendar.recurrence"].create(
                    dict(default_vals, **recurrence_vals, base_event_id=this.id,),
                )
                this.write({"recurrence_id": recurrence.id})
        return recurrence_vals

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        result = super(CalendarEvent, self.with_context(_apply_recurrence=True)).create(
            vals_list
        )
        if not self.env.context.get("_apply_recurrence"):
            for vals, this in zip(vals_list, result):
                if not vals.get("recurrence_id"):
                    recurrence_vals = this._create_recurrence_from_vals(vals)
                    if recurrence_vals:
                        this.recurrence_id.write(recurrence_vals)
                    detached_events = (
                        this.recurrence_id.with_context()._apply_recurrence()
                    )
                    detached_events.write({"active": False})
        return result

    def write(self, vals):
        recurrence_update = vals.pop("recurrence_update", None)
        if "recurrency" in vals and not vals["recurrency"]:
            vals["recurrence_id"] = False

        if not self.env.context.get("_apply_recurrence"):
            self._create_recurrence_from_vals(vals)

        result = super(CalendarEvent, self.with_context(_apply_recurrence=True)).write(
            vals
        )

        if (
            not self.env.context.get("_apply_recurrence")
            and recurrence_update != "self_only"
        ):
            recurrences = self.mapped("recurrence_id").with_context(
                _apply_recurrence=True
            )
            cleaned_vals = {
                key: value
                for key, value in vals.items()
                if key not in self._get_recurrent_fields()
                and key not in self._get_time_fields()
            }
            for recurrence in recurrences:
                recurrence._write_events(cleaned_vals)
                detached_events = recurrence._apply_recurrence()
                detached_events.write({"active": False})
        return result

    def detach_recurring_event(self, values=None):
        return self.mapped("recurrence_id")._detach_events(self)

    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        # disable virtual ids entirely, we do v14 style event duplication
        return super(CalendarEvent, self.with_context(virtual_id=False),)._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
            access_rights_uid=access_rights_uid,
        )
