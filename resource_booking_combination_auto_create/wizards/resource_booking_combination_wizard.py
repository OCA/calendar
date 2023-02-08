# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResourceBookingCombinationWizard(models.TransientModel):
    _name = "resource.booking.combination.wizard"
    _description = "Resource Booking Combination Wizard"
    _inherit = ["multi.step.wizard.mixin"]

    resource_booking_id = fields.Many2one(
        "resource.booking",
        "Resource Booking",
        required=True,
        ondelete="cascade",
    )
    resource_category_ids = fields.Many2many(
        "resource.category",
        relation="rb_category_selection",
        string="Resource Categories",
    )
    resource_booking_category_selection_ids = fields.One2many(
        "resource.booking.category.selection",
        "resource_booking_combination_wizard_id",
        "Resource Category Selections",
        compute="_compute_resource_booking_category_selection_ids",
    )
    current_resource_booking_category_selection_id = fields.Many2one(
        "resource.booking.category.selection",
        "Current Resource Category Selection",
        ondelete="cascade",
    )
    current_resource_booking_category_selection_id_id = fields.Integer(
        "Current Resource Category Selection ID",
        related="current_resource_booking_category_selection_id.id",
    )
    current_resource_category_name = fields.Char(
        related="current_resource_booking_category_selection_id"
        ".resource_category_id.name",
    )
    available_resource_ids = fields.Many2many(
        "resource.booking.category.selection.resource",
        string="Resources",
        related="current_resource_booking_category_selection_id.resource_ids",
        readonly=False,
    )
    configure_step = fields.Integer("Configuration Step", default=0)
    configure_step_count = fields.Integer(
        "Number of Configuration Steps",
        compute="_compute_configure_step_count",
        store=True,
    )
    configure_step_message = fields.Char(
        "Current Configure Step message",
        compute="_compute_configure_step_message",
    )
    selected_resource_ids = fields.Many2many(
        "resource.resource",
        string="Selected Resources",
        compute="_compute_selected_resource_ids",
    )

    @api.depends("resource_category_ids")
    def _compute_resource_booking_category_selection_ids(self):
        self.resource_booking_category_selection_ids = self.env[
            "resource.booking.category.selection"
        ].search([("resource_booking_combination_wizard_id", "=", self.id)])

    @api.depends("resource_category_ids")
    def _compute_configure_step_count(self):
        self.configure_step_count = len(self.resource_category_ids)

    @api.depends("current_resource_booking_category_selection_id")
    def _compute_configure_step_message(self):
        self.configure_step_message = _(
            "Select resources for category {category}:".format(
                category=self.current_resource_category_name
            )
        )

    @api.depends("resource_booking_category_selection_ids.resource_ids.resource_id")
    def _compute_selected_resource_ids(self):
        self.selected_resource_ids = self.mapped(
            "resource_booking_category_selection_ids.resource_ids.resource_id"
        )

    @api.model
    def _selection_state(self):
        return [
            ("start", "Start"),
            ("configure", "Configure"),
            ("final", "Final"),
        ]

    def _compute_step_name(self):
        state = self.state
        if state == "start":
            # the title for the initial step is defined in the xml definition
            # of the act_window.
            return self.env.ref(
                "resource_booking_combination_auto_create."
                "resource_booking_combination_wizard_action"
            ).name
        if state == "configure":
            return _(
                "Select resources ({current_step}/{step_count})".format(
                    current_step=self.configure_step + 1,
                    step_count=self.configure_step_count,
                )
            )
        return _("Confirm")

    def _reopen_self(self):
        act_window = super()._reopen_self()
        act_window["name"] = self._compute_step_name()
        return act_window

    def _update_configure_step(self):
        self.current_resource_booking_category_selection_id = (
            self.resource_booking_category_selection_ids[self.configure_step]
        )

    @api.model
    def create(self, vals):
        resource_booking_id = self.env.context["active_id"]
        resource_booking = self.env["resource.booking"].browse(resource_booking_id)
        if not resource_booking.start or not resource_booking.duration:
            raise ValidationError(
                "To select resources, the booking must have a start date and "
                "a duration."
            )
        vals["resource_booking_id"] = resource_booking_id
        return super().create(vals)

    def state_exit_start(self):
        if not self.resource_booking_category_selection_ids:
            self.state = "final"
            return
        self.find_available_resources()
        self._update_configure_step()
        self.state = "configure"

    def state_previous_configure(self):
        if self.configure_step == 0:
            self.state = "start"
        else:
            self.configure_step -= 1
            self._update_configure_step()

    def state_previous_final(self):
        if not self.resource_booking_category_selection_ids:
            self.state = "start"
        else:
            self.state = "configure"

    def state_exit_configure(self):
        if self.configure_step == self.configure_step_count - 1:
            self.state = "final"
        else:
            self.configure_step += 1
            self._update_configure_step()

    def resource_is_available(self, resource_id):
        # todo: implement this
        return True

    def find_available_resources(self):
        rb_category_selection_resource_model = self.env[
            "resource.booking.category.selection.resource"
        ]
        # fixme: don't delete all, to keep current selection?
        rb_category_selection_resource_model.search(
            [
                (
                    "resource_booking_category_selection_id"
                    ".resource_booking_combination_wizard_id",
                    "=",
                    self.id,
                )
            ]
        ).unlink()
        for rbcs in self.resource_booking_category_selection_ids:
            for resource_id in rbcs.resource_category_id.resource_ids:
                if not self.resource_is_available(resource_id):
                    continue
                rb_category_selection_resource_model.create(
                    {
                        "resource_booking_category_selection_id": rbcs.id,
                        "resource_id": resource_id.id,
                    }
                )

    def create_combination(self):
        # search for an existing combination that matched the selected resources.
        resource_combination_model = self.env["resource.booking.combination"]
        resources = self.selected_resource_ids
        if not resources:
            self.resource_booking_id.combination_id = (
                resource_combination_model.browse()
            )
            return
        domain = []
        for resource in resources:
            domain.append(("resource_ids", "=", resource.id))
        existing_combinations = resource_combination_model.search(domain)
        resource_combination = resource_combination_model.browse()
        for combination in existing_combinations:
            # use first matching combination
            if len(combination.resource_ids) == len(resources):
                resource_combination = combination
                break
        add_to_type = True
        if resource_combination:
            if (
                self.resource_booking_id.type_id
                in resource_combination.type_rel_ids.mapped("type_id")
            ):
                add_to_type = False
        else:
            resource_combination = resource_combination_model.create(
                {
                    "resource_ids": [(6, 0, [r.id for r in resources])],
                }
            )
        if add_to_type:
            self.env["resource.booking.type.combination.rel"].create(
                {
                    "type_id": self.resource_booking_id.type_id.id,
                    "combination_id": resource_combination.id,
                }
            )
        self.resource_booking_id.combination_id = resource_combination
