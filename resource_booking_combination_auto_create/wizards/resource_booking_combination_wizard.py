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
        inverse="_inverse_resource_category_ids",
    )
    wizard_category_ids = fields.One2many(
        "rbc.wizard.category",
        "resource_booking_combination_wizard_id",
        "Resource Categories (Wizard)",
    )
    configuration_step = fields.Integer("Configuration Step", default=0)
    num_configuration_steps = fields.Integer(
        "Number of Configuration Steps",
        compute="_compute_num_configuration_steps",
    )
    # these "current" fields relate to the wizard category of the current
    # configuration step of the wizard.
    current_wizard_category_id = fields.Many2one(
        "rbc.wizard.category",
        "Current Resource Category",
        compute="_compute_current_wizard_category_id",
        store=True,
        ondelete="set null",
    )
    # this field is needed to set a domain in the view.
    current_wizard_category_id_id = fields.Integer(
        "Current Resource Category ID",
        related="current_wizard_category_id.id",
    )
    current_selected_resource_ids = fields.Many2many(
        "rbc.wizard.resource",
        related="current_wizard_category_id.selected_resource_ids",
        readonly=False,
    )
    current_configuration_step_message = fields.Char(
        "Current Configuration Step message",
        compute="_compute_current_configuration_step_message",
    )
    selected_resource_ids = fields.Many2many(
        "resource.resource",
        string="Selected Resources",
        compute="_compute_selected_resource_ids",
    )

    @api.depends("wizard_category_ids.resource_category_id")
    def _compute_resource_category_ids(self):
        for rec in self:
            rec.resource_category_ids = rec.wizard_category_ids.mapped(
                "resource_category_id"
            )

    def _inverse_resource_category_ids(self):
        for rec in self:
            resource_category_ids = set(rec.resource_category_ids.ids)
            commands = []
            for rbcwc in rec.wizard_category_ids:
                resource_category_id = rbcwc.resource_category_id.id
                if resource_category_id not in resource_category_ids:
                    commands.append((2, rbcwc.id, 0))
                else:
                    resource_category_ids.remove(resource_category_id)
            for resource_category in rec.resource_category_ids:
                if resource_category.id not in resource_category_ids:
                    continue
                commands.append((0, 0, {"resource_category_id": resource_category.id}))
            if commands:
                rec.wizard_category_ids = commands

    @api.depends("wizard_category_ids")
    def _compute_num_configuration_steps(self):
        for rec in self:
            rec.num_configuration_steps = len(rec.wizard_category_ids)

    @api.depends("state", "wizard_category_ids", "configuration_step")
    def _compute_current_wizard_category_id(self):
        for rec in self:
            if rec.state != "configuration":
                rec.current_wizard_category_id = False
            else:
                rec.current_wizard_category_id = rec.wizard_category_ids.sorted()[
                    rec.configuration_step
                ]
                rec._update_available_resources_for_current_step()

    @api.depends("current_wizard_category_id")
    def _compute_current_configuration_step_message(self):
        for rec in self:
            resource_category_name = (
                rec.current_wizard_category_id.resource_category_id.name
            )
            if rec.current_wizard_category_id.available_resource_ids:
                rec.current_configuration_step_message = _(
                    "Select resources for category {category}:".format(
                        category=resource_category_name
                    )
                )
            else:
                rec.current_configuration_step_message = _(
                    "No available resources found for category {category}.".format(
                        category=resource_category_name
                    )
                )

    @api.depends("wizard_category_ids.selected_resource_ids.resource_id")
    def _compute_selected_resource_ids(self):
        for rec in self:
            rec.selected_resource_ids = rec.mapped(
                "wizard_category_ids.selected_resource_ids.resource_id"
            )

    @api.model
    def _selection_state(self):
        return [
            ("start", "Start"),
            ("configuration", "Configuration"),
            ("final", "Final"),
        ]

    def _step_name(self):
        state = self.state
        if state == "start":
            # the title for the initial step is defined in the xml definition
            # of the act_window.
            return self.env.ref(
                "resource_booking_combination_auto_create."
                "resource_booking_combination_wizard_action"
            ).name
        if state == "configuration":
            return _(
                "Select resources ({current_step}/{step_count})".format(
                    current_step=self.configuration_step + 1,
                    step_count=self.num_configuration_steps,
                )
            )
        return _("Confirm")

    def _reopen_self(self):
        # this is overridden only to set the title of window from the current
        # step.
        act_window = super()._reopen_self()
        act_window["name"] = self._step_name()
        return act_window

    def _get_resources_selected_in_other_steps(self):
        return (
            self.env["rbc.wizard.resource"]
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
                        self.current_wizard_category_id.id,
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

    def _update_available_resources_for_current_step(self):
        commands = []
        current_rbcwc = self.current_wizard_category_id
        rbcwr_by_resource = {}
        for rbcwr in current_rbcwc.available_resource_ids:
            rbcwr_by_resource[rbcwr.resource_id.id] = rbcwr.id
        # resources currently assigned to the booking are considered as
        # available.
        current_resources = self.resource_booking_id.combination_id.resource_ids
        selected_resources = self._get_resources_selected_in_other_steps()
        start_dt = self.resource_booking_id.start.astimezone(pytz.utc)
        stop_dt = self.resource_booking_id.stop.astimezone(pytz.utc)
        for resource in current_rbcwc.resource_category_id.resource_ids:
            rbcwr_id = rbcwr_by_resource.get(resource.id, None)
            if not self._resource_is_available(
                resource, selected_resources, current_resources, start_dt, stop_dt
            ):
                if rbcwr_id is not None:
                    commands.append((2, rbcwr_id, 0))
                continue
            if rbcwr_id is None:
                commands.append(
                    (
                        0,
                        0,
                        {
                            "rbc_wizard_category_id": current_rbcwc.id,
                            "resource_id": resource.id,
                        },
                    )
                )
        if commands:
            current_rbcwc.available_resource_ids = commands

    def _select_resources_from_current_combination(self):
        resources = self.resource_booking_id.combination_id.resource_ids
        if not resources:
            return
        already_selected_resource_ids = set()
        for rbcwc in self.wizard_category_ids.sorted():
            resource_ids_to_select = []
            for resource in resources:
                if resource.id in already_selected_resource_ids:
                    continue
                if rbcwc.resource_category_id not in resource.resource_category_ids:
                    continue
                resource_ids_to_select.append(resource.id)
                already_selected_resource_ids.add(resource.id)
            if resource_ids_to_select:
                rbcwc.available_resource_ids = [
                    (0, 0, {"resource_id": resource_id})
                    for resource_id in resource_ids_to_select
                ]
                rbcwc.selected_resource_ids = [
                    (6, 0, [r.id for r in rbcwc.available_resource_ids])
                ]

    @api.model
    def create(self, vals):
        resource_booking_id = self.env.context["active_id"]
        vals["resource_booking_id"] = resource_booking_id
        wizard = super().create(vals)
        wizard._select_resources_from_current_combination()
        return wizard

    def state_exit_start(self):
        if not self.wizard_category_ids:
            # no categories are selected, jump directly to the final step.
            self.state = "final"
        else:
            self.state = "configuration"

    def state_previous_configuration(self):
        if self.configuration_step == 0:
            # the step before the first configuration step is the start step.
            self.state = "start"
        else:
            self.configuration_step -= 1

    def state_exit_configuration(self):
        if self.configuration_step == self.num_configuration_steps - 1:
            # the step after the last configuration step is the start step.
            self.state = "final"
        else:
            self.configuration_step += 1

    def state_previous_final(self):
        if not self.wizard_category_ids:
            # no categories are selected, jump directly to the start step.
            self.state = "start"
        else:
            self.state = "configuration"

    def create_combination(self):
        # search for an existing combination that matches the selected resources.
        resource_combination_model = self.env["resource.booking.combination"]
        resources = self.selected_resource_ids
        if not resources:
            self.resource_booking_id.combination_id = False
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
