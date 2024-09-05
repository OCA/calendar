# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.mail.tests.common import MailCommon, mail_new_test_user


class TestPortalWizardUser(MailCommon):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "Testing Partner",
                "email": "testing_partner@example.com",
            }
        )

        self.portal_user = mail_new_test_user(
            self.env,
            name="Portal user",
            login="portal_user",
            email="portal_user@example.com",
            groups="base.group_portal",
        )

    def test_portal_wizard_create_user(self):
        portal_wizard = (
            self.env["portal.wizard"]
            .with_context(active_ids=[self.partner.id])
            .create({})
        )

        self.assertEqual(len(portal_wizard.user_ids), 1)

        portal_user = portal_wizard.user_ids

        self.assertFalse(portal_user.user_id)
        self.assertFalse(portal_user.in_portal)
        self.assertFalse(portal_user.booking_from_portal)

        portal_user.email = "first_email@example.com"
        portal_user.booking_from_portal = True
        new_user = portal_user._create_user()

        self.assertTrue(new_user)
        self.assertTrue(new_user.create_booking_from_portal)
