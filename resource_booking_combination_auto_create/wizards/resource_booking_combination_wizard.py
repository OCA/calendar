# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytz

from odoo import _, api, fields, models


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
        string="Resource Categories",
        compute="_compute_resource_category_ids",
        inverse="_set_resource_category_ids",
    )
    resource_booking_category_selection_ids = fields.One2many(
        "resource.booking.category.selection",
        "resource_booking_combination_wizard_id",
        "Resource Category Selections",
    )
    current_resource_booking_category_selection_id = fields.Many2one(
        "resource.booking.category.selection",
        "Current Resource Category Selection",
        ondelete="set null",
    )
    current_resource_booking_category_selection_id_id = fields.Integer(
        "Current Resource Category Selection ID",
        related="current_resource_booking_category_selection_id.id",
    )
    current_selected_resource_ids = fields.Many2many(
        "resource.booking.category.selection.resource",
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

    @api.depends("resource_booking_category_selection_ids.resource_category_id")
    def _compute_resource_category_ids(self):
        self.resource_category_ids = (
            self.resource_booking_category_selection_ids.mapped("resource_category_id")
        )

    def _set_resource_category_ids(self):
        resource_category_ids = set(self.resource_category_ids.ids)
        commands = []
        for rbcs in self.resource_booking_category_selection_ids:
            resource_category_id = rbcs.resource_category_id.id
            if resource_category_id not in resource_category_ids:
                commands.append((2, rbcs.id, 0))
            else:
                resource_category_ids.remove(resource_category_id)
        for resource_category in self.resource_category_ids:
            if resource_category.id not in resource_category_ids:
                continue
            commands.append((0, 0, {"resource_category_id": resource_category.id}))
        if commands:
            self.resource_booking_category_selection_ids = commands

    @api.depends("resource_booking_category_selection_ids")
    def _compute_configure_step_count(self):
        self.configure_step_count = len(self.resource_booking_category_selection_ids)

    @api.depends("current_resource_booking_category_selection_id")
    def _compute_configure_step_message(self):
        resource_category_name = (
            self.current_resource_booking_category_selection_id.resource_category_id.name
        )
        if self.current_resource_booking_category_selection_id.available_resource_ids:
            self.configure_step_message = _(
                "Select resources for category {category}:".format(
                    category=resource_category_name
                )
            )
        else:
            self.configure_step_message = _(
                "No available resources found for category {category}.".format(
                    category=resource_category_name
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

    def _get_resources_selected_in_other_steps(self):
        return (
            self.env["resource.booking.category.selection.resource"]
            .search(
                [
                    (
                        "selected_from.resource_booking_combination_wizard_id",
                        "=",
                        self.id,
                    ),
                    (
                        "selected_from",
                        "!=",
                        self.current_resource_booking_category_selection_id.id,
                    ),
                ]
            )
            .mapped("resource_id")
        )

    def _resource_is_available(
        self, resource, selected_resources, current_resources, start_dt, stop_dt
    ):
        if resource in selected_resources:
            return False
        if resource in current_resources:
            return True
        if not resource.is_available(start_dt, stop_dt):
            return False
        return True

    def _find_available_resources_for_current_step(self):
        commands = []
        current_rbcs = self.current_resource_booking_category_selection_id
        rbcsr_by_resource = {}
        for rbcsr in current_rbcs.available_resource_ids:
            rbcsr_by_resource[rbcsr.resource_id.id] = rbcsr.id
        # resources currently assigned to the booking are considered as
        # available.
        current_resources = self.resource_booking_id.combination_id.resource_ids
        selected_resources = self._get_resources_selected_in_other_steps()
        start_dt = self.resource_booking_id.start.astimezone(pytz.utc)
        stop_dt = self.resource_booking_id.stop.astimezone(pytz.utc)
        for resource in current_rbcs.resource_category_id.resource_ids:
            rbcsr_id = rbcsr_by_resource.get(resource.id, None)
            if not self._resource_is_available(
                resource, selected_resources, current_resources, start_dt, stop_dt
            ):
                if rbcsr_id is not None:
                    commands.append((2, rbcsr_id, 0))
                continue
            if rbcsr_id is None:
                commands.append(
                    (
                        0,
                        0,
                        {
                            "resource_booking_category_selection_id": current_rbcs.id,
                            "resource_id": resource.id,
                        },
                    )
                )
        if commands:
            current_rbcs.available_resource_ids = commands

    def _update_configure_step(self):
        self.current_resource_booking_category_selection_id = (
            self.resource_booking_category_selection_ids.sorted()[self.configure_step]
        )
        self._find_available_resources_for_current_step()

    def _select_resources_from_current_combination(self):
        resources = self.resource_booking_id.combination_id.resource_ids
        if not resources:
            return
        already_selected_resource_ids = set()
        for rbcs in self.resource_booking_category_selection_ids.sorted():
            resource_ids_to_select = []
            for resource in resources:
                if resource.id in already_selected_resource_ids:
                    continue
                if rbcs.resource_category_id not in resource.resource_category_ids:
                    continue
                resource_ids_to_select.append(resource.id)
                already_selected_resource_ids.add(resource.id)
            if resource_ids_to_select:
                rbcs.available_resource_ids = [
                    (0, 0, {"resource_id": resource_id})
                    for resource_id in resource_ids_to_select
                ]
                rbcs.resource_ids = [
                    (6, 0, [r.id for r in rbcs.available_resource_ids])
                ]

    @api.model
    def create(self, vals):
        resource_booking_id = self.env.context["active_id"]
        vals["resource_booking_id"] = resource_booking_id
        wizard = super().create(vals)
        wizard._select_resources_from_current_combination()
        return wizard

    def state_exit_start(self):
        if not self.resource_booking_category_selection_ids:
            self.state = "final"
            return
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

    def create_combination(self):
        # search for an existing combination that matches the selected resources.
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
