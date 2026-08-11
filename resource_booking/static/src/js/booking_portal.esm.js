import {PortalHomeCounters} from "@portal/interactions/portal_home_counters";
import {patch} from "@web/core/utils/patch";

// Extend the portal home counters to always display the booking counter
patch(PortalHomeCounters.prototype, {
    getCountersAlwaysDisplayed() {
        const base = super.getCountersAlwaysDisplayed();
        return [...base, "booking_count"];
    },
});
