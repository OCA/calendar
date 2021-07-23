# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


def remove_start_stop_together_constraint(cr):
    """Remove old unnecessary constraint.

    This one is no longer needed because `stop` is now computed and readonly,
    so it will always have or not have value automatically.
    """
    openupgrade.logged_query(
        cr,
        """
            ALTER TABLE resource_booking
            DROP CONSTRAINT IF EXISTS resource_booking_start_stop_together
        """,
    )


def fill_resource_booking_duration(env):
    """Pre-create and pre-fill resource.booking duration."""
    openupgrade.add_fields(
        env,
        [
            (
                "duration",
                "resource.booking",
                "resource_booking",
                "float",
                None,
                "resource_booking",
                None,
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE resource_booking rb
            SET duration = COALESCE(
                -- See https://stackoverflow.com/a/952600/1468388
                EXTRACT(EPOCH FROM rb.stop - rb.start) / 3600,
                rbt.duration
            )
            FROM resource_booking_type rbt
            WHERE rb.type_id = rbt.id
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    remove_start_stop_together_constraint(env.cr)
    fill_resource_booking_duration(env)
