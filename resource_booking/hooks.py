# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def uninstall_hook(env):
    # Remove new activity type resource booking and all activities associated'
    activiy_resource_booking = env.ref(
        "resource_booking.mail_activity_data_resource_booking", raise_if_not_found=False
    )
    if activiy_resource_booking:
        booking_activiy_ids = env["mail.activity"].search([("booking_id", "!=", False)])
        booking_activiy_ids.unlink()
        activiy_resource_booking.unlink()
