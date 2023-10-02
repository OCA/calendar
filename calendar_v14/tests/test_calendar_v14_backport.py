from datetime import datetime, timedelta

from odoo.tests import common


class TestV13Backport(common.TransactionCase):
    def test_invitation_mail(self):
        """ Test invitation is only sent once """
        user = self.env.ref("base.user_demo")
        vals = {
            "active": True,
            "alarm_ids": [[6, False, []]],
            "allday": False,
            "byday": False,
            "categ_ids": [[6, False, []]],
            "count": 0,
            "day": 0,
            "description": "<p><br></p>",
            "duration": 1,
            "end_type": False,
            "event_tz": False,
            "final_date": False,
            "fr": False,
            "interval": 0,
            "location": False,
            "message_attachment_count": 0,
            "mo": False,
            "month_by": False,
            "name": "test2",
            "partner_ids": [[6, False, user.partner_id.ids]],
            "privacy": "public",
            "recurrency": False,
            "recurrent_id": 0,
            "res_id": 0,
            "rrule_type": False,
            "sa": False,
            "show_as": "busy",
            "start": datetime.now() + timedelta(hours=4),
            "start_date": False,
            "start_datetime": datetime.now() + timedelta(hours=4),
            "stop": datetime.now() + timedelta(hours=5),
            "stop_date": False,
            "stop_datetime": datetime.now() + timedelta(hours=5),
            "su": False,
            "th": False,
            "tu": False,
            "user_id": user.id,
            "we": False,
            "week_list": False,
        }
        last_message = self.env["mail.message"].search([], order="id desc", limit=1)
        self.env["mail.template"].search(
            [("model_id.model", "=", "calendar.attendee")]
        ).write({"auto_delete": False})
        self.env["calendar.event"].with_user(user).create(vals)
        new = self.env["mail.message"].search([("id", ">", last_message.id)])
        # the create message, the invitation
        self.assertEqual(len(new), 2)
