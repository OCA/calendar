# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResourceBooking(models.Model):
    _name = "resource.booking"
    _inherit = ["resource.booking", "utm.mixin"]

    lead_id = fields.Many2one(
        comodel_name="crm.lead",
        string="Lead/Opportunity",
        copy=False,
        index="btree_not_null",
        ondelete="set null",
        tracking=True,
        groups="sales_team.group_sale_salesman",
    )

    @api.model_create_multi
    def create(self, vals_list):
        bookings = super().create(vals_list)
        bookings._crm_create_leads()
        return bookings

    def write(self, vals):
        res = super().write(vals)
        if "meeting_id" in vals:
            self._crm_create_leads()
        return res

    def _crm_create_leads(self):
        bookings = self.sudo().filtered(
            lambda b: b.meeting_id and not b.lead_id and b.type_id.crm_lead_type
        )
        if not bookings:
            return
        reusable = bookings._crm_find_reusable_leads()
        to_create = bookings.filtered(lambda b: b.id not in reusable)
        leads = (
            self.env["crm.lead"]
            .sudo()
            .with_context(mail_create_nosubscribe=True)
            .create([booking._prepare_crm_lead_vals() for booking in to_create])
        )
        for booking, lead in zip(to_create, leads, strict=True):
            booking._crm_link_lead(lead, created=True)
        for booking in bookings - to_create:
            booking._crm_link_lead(reusable[booking.id], created=False)

    def _crm_find_reusable_leads(self):
        """Map booking ids to the open lead they should reuse."""
        bookings = self.filtered(lambda b: b.type_id.crm_lead_reuse and b.partner_id)
        if not bookings:
            return {}
        commercial_partners = bookings.partner_id.commercial_partner_id
        leads = (
            self.env["crm.lead"]
            .sudo()
            .search(
                [
                    ("partner_id", "child_of", commercial_partners.ids),
                    ("stage_id.is_won", "=", False),
                ],
                order="create_date desc, id desc",
            )
        )
        lead_by_partner = {}
        for lead in leads:
            lead_by_partner.setdefault(lead.partner_id.commercial_partner_id.id, lead)
        result = {}
        for booking in bookings:
            lead = lead_by_partner.get(booking.partner_id.commercial_partner_id.id)
            if lead:
                result[booking.id] = lead
        return result

    def _crm_get_lead_user(self):
        self.ensure_one()
        users = (
            self.type_id.crm_user_id
            | self.user_id
            | self.combination_id.resource_ids.filtered(
                lambda res: res.resource_type == "user"
            ).user_id
        )
        return users.filtered(lambda user: not user.share)[:1]

    def _prepare_crm_lead_vals(self):
        self.ensure_one()
        booking_type = self.type_id
        vals = {
            "name": self.name
            or self._get_name_formatted(self.partner_ids[:1], booking_type),
            "type": booking_type.crm_lead_type,
            "partner_id": self.partner_id.id,
            "user_id": self._crm_get_lead_user().id,
            "tag_ids": [fields.Command.set(booking_type.crm_tag_ids.ids)],
            "description": self.description,
            "campaign_id": self.campaign_id.id,
            "source_id": self.source_id.id,
            "medium_id": self.medium_id.id,
        }
        if booking_type.crm_team_id:
            vals["team_id"] = booking_type.crm_team_id.id
        if booking_type.company_id:
            vals["company_id"] = booking_type.company_id.id
        return vals

    def _crm_link_lead(self, lead, created):
        self.ensure_one()
        self.lead_id = lead
        if (
            not self.env.context.get("resource_booking_crm_creating_event")
            and not self.meeting_id.opportunity_id
        ):
            self.meeting_id.opportunity_id = lead
        if created:
            lead.message_post_with_source(
                "mail.message_origin_link",
                render_values={"self": lead, "origin": self},
                subtype_xmlid="mail.mt_note",
            )
        else:
            lead.message_post(
                body=self.env._(
                    "New booking linked: %(booking)s", booking=self._get_html_link()
                ),
                subtype_xmlid="mail.mt_note",
            )

    def action_view_crm_lead(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "crm.lead",
            "res_id": self.lead_id.id,
            "view_mode": "form",
        }
