# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(env):
    env.cr.execute(
        """
        ALTER TABLE resource_booking RENAME partner_id TO old_partner_id
        """,
    )
