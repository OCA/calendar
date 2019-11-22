# Copyright 2018 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from caldav import davclient
from pytz import timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CalendarCaldav(models.Model):
    _name = 'calendar.caldav'

    @api.model
    def _get_client(self, user):
        return davclient.DAVClient(
            user.caldav_url,
            username=user.caldav_username,
            password=user.caldav_password,
            ssl_verify_cert=False
        )

    @api.model
    def sync_calendars(self, user):
        principal = self._get_client(user).principal()
        calendars = principal.calendars()
        existing_calendar_ids = []
        for calendar in calendars:
            domain = [('user_id', '=', user.id)]
            if calendar.id:
                domain.append(('caldav_id', '=', calendar.id))
            elif calendar.name:
                domain.append(('caldav_name', '=', calendar.name))
            else:
                raise Exception(_('Invalid calendar'))

            calendar_record = self.env['calendar.caldav.calendar'].search(domain)

            if not calendar_record:
                calendar_record = self.env['calendar.caldav.calendar'].create({
                    'user_id': user.id,
                    'caldav_id': calendar.id,
                    'caldav_name': calendar.name
                })
            existing_calendar_ids.append(calendar_record.id)

        self.env['calendar.caldav.calendar'].search([
            ('id', 'not in', existing_calendar_ids),
            ('user_id', '=', user.id)
        ]).unlink()

    @api.model
    def _prepare_caldav_event_for_odoo(self, vevent, user):
        allday = vevent.get('x-microsoft-cdo-alldayevent', 'FALSE') == 'TRUE'
        caldav_id = str(vevent['uid'])

        if vevent.get('recurrence-id'):
            caldav_id += fields.Datetime.to_string(vevent['recurrence-id'].dt)

        event = {
            'name': str(vevent.get('summary', '')),
            'description': str(vevent.get('description', '')),
            'privacy': str(vevent.get('class', 'private')).lower(),
            'allday': allday,
            'location': str(vevent.get('location', '')),
            'user_id': user.id,
            'caldav_id': caldav_id,
            'caldav_last_update': fields.Datetime.to_string(vevent['last-modified'].dt)
        }

        if allday:
            event.update({
                'start': fields.Date.to_string(vevent['dtstart'].dt),
                # Zimbra seems to return all day events with + 1 to end date
                'stop': fields.Date.to_string(vevent['dtend'].dt - timedelta(days=1))
            })
        else:
            offset = vevent['dtstart'].dt.utcoffset()
            event.update({
                'start': fields.Datetime.to_string(vevent['dtstart'].dt - offset),
                'stop': fields.Datetime.to_string(vevent['dtend'].dt - offset)
            })
        return event

    @api.model
    def _odoo_to_caldav(self, vevent, event_record):
        """ Sets the values of a caldav event
            using a odoo record

            @return: the updated vevent
        """
        vevent.add('x-microsoft-cdo-alldayevent', event_record.allday and 'TRUE' or 'FALSE')
        vevent.add('summary', event_record.name)
        vevent.add('description', event_record.description)
        vevent.add('location', event_record.location)
        vevent.add('last-modified',
                   fields.Datetime.from_string(event_record.caldav_odoo_last_update))

        if event_record.allday:
            vevent.add('dtstart', fields.Date.from_string(event_record.start))
            vevent.add('dtend', fields.Date.from_string(event_record.stop))
        else:
            user_tz = timezone(event_record.user_id.tz)
            offset = user_tz.utcoffset(fields.Datetime.from_string(event_record.start))
            vevent.add('dtstart', fields.Datetime.from_string(event_record.start) + offset)
            vevent.add('dtend', fields.Datetime.from_string(event_record.stop) + offset)
        return vevent

    @api.model
    def _get_caldav_event_components(self, dav_object):
        return list(filter(lambda s: s.name.lower() == 'vevent', dav_object.instance.subcomponents))

    @api.model
    def _get_caldav_events(self, user, start, end):
        calendar_records = self.env['calendar.caldav.calendar'].search([
            ('user_id', '=', user.id),
            ('sync', '=', True)
        ])
        principal = self._get_client(user).principal()
        calendars = principal.calendars()
        dav_objects = []

        def calendar_filter(calendar_odoo):
            if calendar_odoo.caldav_id:
                return lambda c: c.id == calendar_odoo.caldav_id
            else:
                return lambda c: c.name == calendar_odoo.caldav_name

        for calendar_record in calendar_records:
            calendar = list(filter(calendar_filter(calendar_record), calendars))
            if len(calendar) == 0:
                raise UserError(
                    _('Calendar not found, please synchronize '
                      'your calendars in the user preferences form')
                )
            calendar = calendar[0]
            caldav_events = calendar.date_search(
                fields.Datetime.from_string(start),
                fields.Datetime.from_string(end)
            )
            dav_objects.extend(caldav_events)
        return dav_objects

    @api.model
    def sync_events(self, user, start, end):
        user = isinstance(user, int) and self.env['res.users'].browse(user) or user
        if not user.caldav_calendar_ids:
            return {
                'status': 'setup'
            }
        caldav_events = self._get_caldav_events(user, start, end)
        all_event_components = []
        for caldav_event in caldav_events:
            components = self._get_caldav_event_components(caldav_event)
            for vevent_component in components:
                prepared_event = self._prepare_caldav_event_for_odoo(vevent_component, user)
                event = self.env['calendar.event'].search([
                    ('caldav_id', '=', prepared_event['caldav_id']),
                    ('user_id', '=', user.id)
                ])
                if event.caldav_odoo_last_update and \
                        event.caldav_odoo_last_update > prepared_event['caldav_last_update']:
                    # If event is last edited in Odoo then update caldav
                    self._odoo_to_caldav(vevent_component, event)
                    caldav_event.save()
                elif event:
                    event.write(prepared_event)
                else:
                    event.create(prepared_event)
            all_event_components.extend(components)
        # Remove in Odoo if not existing in caldav calendar
        self.env['calendar.event'].search([
            ('user_id', '=', 'user_id'),
            ('caldav_id', '!=', False),
            ('caldav_id', 'not in', [e['uid'] for e in all_event_components])
        ]).unlink()

        return {
            'status': 'success'
        }

    @api.model
    def sync_events_cron(self):
        users = self.env['res.users'].search([('caldav_calendar_ids', '!=', False)])

        now = datetime.now()
        start = now - timedelta(days=365)
        end = now + timedelta(days=365)

        for user in users:
            self.sync_events(
                user,
                fields.Datetime.to_string(start),
                fields.Datetime.to_string(end)
            )
