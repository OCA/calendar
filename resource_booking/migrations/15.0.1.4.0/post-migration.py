# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def convert_resource_booking_partners(env):
    openupgrade.m2o_to_x2m(
        env.cr,
        env["resource.booking"],
        "resource_booking",
        "partner_ids",
        "old_partner_id",
    )


@openupgrade.migrate()
def migrate(env, version):
    """Put partner_id in partner_ids"""
    convert_resource_booking_partners(env)
