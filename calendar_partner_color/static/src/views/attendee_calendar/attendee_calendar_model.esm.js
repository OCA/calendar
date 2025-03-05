/** @odoo-module **/

import {AttendeeCalendarModel} from "@calendar/views/attendee_calendar/attendee_calendar_model";
import {patch} from "@web/core/utils/patch";

patch(AttendeeCalendarModel.prototype, "calendar_partner_color", {
    /**
     * @override
     * Set color to the partner color
     */
    async updateAttendeeData(data) {
        const res = await this._super(...arguments);
        const attendees = data.attendees;

        // Map attendees by event_id and attendee_id
        const attendeeMap = new Map();
        for (const attendee of attendees) {
            if (!attendeeMap.has(attendee.event_id)) {
                attendeeMap.set(attendee.event_id, new Map());
            }
            attendeeMap
                .get(attendee.event_id)
                .set(attendee.attendee_id, attendee.color);
        }

        const missingColors = new Set();
        // Assign colorIndex based on matching attendee
        for (const event of Object.values(data.records)) {
            if (attendeeMap.has(event.id)) {
                const eventAttendees = attendeeMap.get(event.id);
                if (eventAttendees.has(event.calendarAttendeeId)) {
                    event.colorIndex = eventAttendees.get(event.calendarAttendeeId);
                }
            } else if (event.rawRecord.privacy === "private") {
                if (!missingColors.has(event.rawRecord.partner_id[0])) {
                    event.colorIndex = await this.getColorPrivateEvent(
                        event.rawRecord.partner_id[0],
                        missingColors
                    );
                } else {
                    event.colorIndex = missingColors.get(event.rawRecord.partner_id[0]);
                }
            }
        }

        // Update filter colors
        const filterSection = data.filterSections.partner_ids;
        for (const filter of filterSection.filters) {
            if (typeof filter.value === "number") {
                let color = null;
                for (const attendee of attendees) {
                    if (attendee.id == filter.value) {
                        color = attendee.color;
                        break;
                    }
                }
                filter.colorIndex = color;
            }
        }
        return res;
    },

    async getColorPrivateEvent(partner_id, missingColors) {
        const colorIndex = await this.orm.searchRead(
            "res.partner",
            [["id", "=", partner_id]],
            ["color"]
        );
        if (colorIndex.length) {
            missingColors.add(partner_id[0], colorIndex[0].color);
            return colorIndex[0].color;
        }
        return null; // Return a default value if no color is found
    },
});
