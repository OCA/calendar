# Copyright 2020 Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def pre_init_hook(cr):
    """The objective of this hook is to set a color to existing partners"""
    cr.execute(
        """UPDATE res_partner SET color = id % 30
        WHERE color = 0;"""
    )
