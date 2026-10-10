/* Copyright 2025 Ledo Enterprises LLC - Don Kendall
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

/**
 * Public booking page interactivity.
 *
 * Uses Odoo's publicWidget system so that the widget initializes correctly
 * with deferred/lazy asset loading in Odoo 18.  Reads slot data from a
 * hidden data attribute rendered server-side and handles day/slot
 * selection without additional network requests.
 *
 * Timezone handling: slot ISO instants are absolute (carry an offset). The
 * server renders day-buckets and time strings in the booking type's
 * resource calendar timezone. If the visitor's browser timezone differs,
 * this widget re-buckets the slots into visitor-local days and reformats
 * the time strings — entirely client-side, no round-trip. An optional
 * ``?tz=`` query param lets the server bucket in an explicit timezone
 * (overrides browser detection); a dropdown lets the visitor pick.
 */

/* eslint-env browser */
import publicWidget from "@web/legacy/js/public/public_widget";

/** Build an ``Intl.DateTimeFormat`` keyed in the given timezone. */
function _dateFormatterFor(tz) {
    return new Intl.DateTimeFormat("en-CA", {
        timeZone: tz,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    });
}

function _timeFormatterFor(tz) {
    return new Intl.DateTimeFormat(undefined, {
        timeZone: tz,
        hour: "numeric",
        minute: "2-digit",
    });
}

/** Return the IANA timezone the browser thinks it's in. */
function _detectBrowserTz() {
    try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    } catch {
        return "";
    }
}

/**
 * Out-of-hours request banner — the "Request a custom slot" CTA on the
 * booking page when the visitor's timezone has no overlap with the
 * published booking hours. Lives as a sibling of the main calendar
 * widget so its toggle state is independent.
 */
publicWidget.registry.WebsiteAppointmentRequestBanner = publicWidget.Widget.extend({
    selector: ".o_wab_request_banner",
    events: {
        "click .o_wab_request_toggle": "_onToggle",
    },

    _onToggle(ev) {
        const form = this.el.querySelector("#o_wab_request_form");
        const toggleBtn = ev.currentTarget;
        if (!form) {
            return;
        }
        const willShow = form.classList.contains("d-none");
        form.classList.toggle("d-none", !willShow);
        // Disable the toggle button when the form is open so a second click
        // doesn't collapse the form while the user is mid-fill.
        toggleBtn.setAttribute("disabled", "disabled");
        toggleBtn.classList.add("d-none");
        // Move focus to the name field so keyboard users land in the form.
        const nameInput = form.querySelector("#o_wab_request_name");
        if (nameInput) {
            nameInput.focus();
        }
    },
});

publicWidget.registry.WebsiteAppointmentBooking = publicWidget.Widget.extend({
    selector: ".o_wab_calendar",
    events: {
        "click .o_wab_day_available": "_onDayClick",
        "keydown .o_wab_day_available": "_onDayKeydown",
        "click .o_wab_slot_btn": "_onSlotClick",
        "change #o_wab_tz_select": "_onTzSelectChange",
        "toggle .o_wab_description details": "_onDetailsToggle",
    },

    /**
     * @override
     */
    start() {
        const dataEl = this.el.querySelector("#o_wab_slot_data");
        if (!dataEl) {
            return this._super(...arguments);
        }
        this.allSlots = JSON.parse(dataEl.dataset.slots || "[]");
        this.panel = this.el.querySelector("#o_wab_slots_panel");
        this.slotsTitle = this.panel
            ? this.panel.querySelector(".o_wab_slots_title")
            : null;
        this.slotsList = this.panel
            ? this.panel.querySelector(".o_wab_slots_list")
            : null;
        this.form = this.el.querySelector("#o_wab_form");
        this.whenInput = this.el.querySelector("#o_wab_when");
        this.displayTzInput = this.el.querySelector("#o_wab_display_tz");
        this.selectedDisplay = this.el.querySelector("#o_wab_selected_display");
        this.slotsEmpty = this.el.querySelector("#o_wab_slots_empty");
        this.tzSelect = this.el.querySelector("#o_wab_tz_select");
        this.tzLabel = this.el.querySelector("#o_wab_tz_label");
        this.tzSecondary = this.el.querySelector("#o_wab_tz_secondary");

        this.resourceTz = this.el.dataset.resourceTz || "UTC";
        this.effectiveTz = this.el.dataset.effectiveTz || this.resourceTz;
        this.visitorTz = _detectBrowserTz();

        // The tz the booking page actually displays. Either the server
        // already bucketed in it (explicit ?tz=), or JS is about to
        // re-bucket into the visitor's tz, or it's the resource tz fallback.
        let displayTz = this.effectiveTz;
        const hasExplicitTz = new URLSearchParams(window.location.search).has("tz");
        if (!hasExplicitTz && this.visitorTz && this.visitorTz !== this.effectiveTz) {
            this._rebucketSlots(this.visitorTz);
            this._updateTzLabel(this.visitorTz);
            displayTz = this.visitorTz;
        }
        if (this.displayTzInput) {
            this.displayTzInput.value = displayTz;
        }
        if (this.tzSelect) {
            this._ensureOptionPresent(this.tzSelect, displayTz);
            this.tzSelect.value = displayTz;
        }

        // Build lookup: date string -> [{time, iso}]
        this.slotsByDate = {};
        for (const slot of this.allSlots) {
            (this.slotsByDate[slot.date] = this.slotsByDate[slot.date] || []).push(
                slot
            );
        }
        return this._super(...arguments);
    },

    // -------------------------------------------------------------------------
    // Timezone re-bucketing
    // -------------------------------------------------------------------------

    /**
     * Reassign each slot's ``date`` and ``time`` to the visitor's tz, then
     * walk the calendar DOM to flip availability marks to match.
     *
     * Server padded the slot list by ±1 day so this re-bucket can pull in
     * neighbouring-month edge slots without going off the rendered grid.
     *
     * @param {String} visitorTz IANA tz
     */
    _rebucketSlots(visitorTz) {
        const dfmt = _dateFormatterFor(visitorTz);
        const tfmt = _timeFormatterFor(visitorTz);
        for (const slot of this.allSlots) {
            const instant = new Date(slot.iso);
            slot.date = dfmt.format(instant);
            slot.time = tfmt.format(instant);
        }
        // Rebuild date → slots map after the mutation
        const byDate = {};
        for (const slot of this.allSlots) {
            (byDate[slot.date] = byDate[slot.date] || []).push(slot);
        }
        // Walk every day cell; toggle availability + role/tabindex.
        //
        // We mark availability based on bucketed-date membership even on
        // "out of month" cells (trailing days from prev/next month that
        // render muted in the grid). Without this, padded slots that
        // re-bucket onto an adjacent-month edge — e.g. a 23:30 ET Mar 31
        // slot landing on Apr 1 for an NZ visitor viewing the March page —
        // get silently dropped because the original server template only
        // set the availability class on in-month days. Also strip the
        // ``text-muted`` styling when an adjacent cell gains availability
        // so it doesn't look greyed-out to the visitor.
        const dayCells = this.el.querySelectorAll(".o_wab_day[data-date]");
        for (const cell of dayCells) {
            const hasSlots = Boolean(byDate[cell.dataset.date]);
            cell.classList.toggle("o_wab_day_available", hasSlots);
            const isInMonth = cell.dataset.inMonth === "1";
            if (hasSlots && !isInMonth) {
                cell.classList.remove("text-muted");
            } else if (!hasSlots && !isInMonth) {
                cell.classList.add("text-muted");
            }
            if (hasSlots) {
                cell.setAttribute("role", "button");
                cell.setAttribute("tabindex", "0");
            } else {
                cell.removeAttribute("role");
                cell.removeAttribute("tabindex");
            }
        }
    },

    _updateTzLabel(tz) {
        if (this.tzLabel) {
            this.tzLabel.textContent = tz;
        }
        if (this.tzSecondary && tz !== this.resourceTz) {
            this.tzSecondary.classList.remove("d-none");
        }
    },

    _ensureOptionPresent(select, value) {
        if (!value) {
            return;
        }
        const exists = Array.from(select.options).some((o) => o.value === value);
        if (!exists) {
            const opt = select.ownerDocument.createElement("option");
            opt.value = value;
            opt.textContent = value;
            // Insert at the top so it's the first thing users see.
            select.insertBefore(opt, select.firstChild);
        }
    },

    // -------------------------------------------------------------------------
    // Handlers
    // -------------------------------------------------------------------------

    /**
     * Handle click on an available calendar day.
     *
     * @param {Event} ev
     */
    _onDayClick(ev) {
        const td = ev.currentTarget;
        const date = td.dataset.date;
        if (!date) {
            return;
        }
        // After re-bucket the lookup may be stale — recompute on demand
        if (!this.slotsByDate[date]) {
            const fresh = this.allSlots.filter((s) => s.date === date);
            if (!fresh.length) {
                return;
            }
            this.slotsByDate[date] = fresh;
        }

        // Highlight selected day
        this.el.querySelectorAll(".o_wab_day_selected").forEach((el) => {
            el.classList.remove("o_wab_day_selected");
        });
        td.classList.add("o_wab_day_selected");

        // Format the date for the slots panel header. Build the Date from
        // an iso so the active tz applies; if no slots, fall back to the
        // bare date string interpreted as local midnight.
        const slotsForDay = this.slotsByDate[date];
        const activeTz = this.displayTzInput
            ? this.displayTzInput.value
            : this.effectiveTz;
        let dateStr = "";
        if (slotsForDay && slotsForDay.length) {
            dateStr = new Date(slotsForDay[0].iso).toLocaleDateString(undefined, {
                weekday: "long",
                month: "long",
                day: "numeric",
                timeZone: activeTz || undefined,
            });
        } else {
            const dateObj = new Date(date + "T00:00:00");
            dateStr = dateObj.toLocaleDateString(undefined, {
                weekday: "long",
                month: "long",
                day: "numeric",
            });
        }

        // Populate the slots panel
        if (this.slotsTitle) {
            this.slotsTitle.textContent = dateStr;
        }
        if (this.slotsList) {
            this.slotsList.innerHTML = "";
            for (const slot of slotsForDay) {
                const btn = this.el.ownerDocument.createElement("button");
                btn.type = "button";
                btn.className = "o_wab_slot_btn";
                btn.textContent = slot.time;
                btn.dataset.iso = slot.iso;
                btn.dataset.display = dateStr + " at " + slot.time;
                this.slotsList.appendChild(btn);
            }
        }
        if (this.panel) {
            this.panel.classList.remove("d-none");
        }
        // Hide the empty-state placeholder
        if (this.slotsEmpty) {
            this.slotsEmpty.classList.add("d-none");
        }
        // Hide the booking form until a slot is picked
        if (this.form) {
            this.form.classList.add("d-none");
        }
        // Scroll to the slots panel
        if (this.panel) {
            this.panel.scrollIntoView({behavior: "smooth", block: "nearest"});
        }
    },

    /**
     * Keyboard activation on day cells — Enter or Space mirrors a click.
     *
     * @param {KeyboardEvent} ev
     */
    _onDayKeydown(ev) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            this._onDayClick(ev);
        }
    },

    /**
     * Handle click on a time slot button.
     *
     * @param {Event} ev
     */
    _onSlotClick(ev) {
        const btn = ev.currentTarget;

        // Highlight selected slot
        if (this.panel) {
            this.panel.querySelectorAll(".o_wab_slot_btn").forEach((el) => {
                el.classList.remove("active");
            });
        }
        btn.classList.add("active");

        // Fill form hidden input
        if (this.whenInput) {
            this.whenInput.value = btn.dataset.iso;
        }
        if (this.selectedDisplay) {
            this.selectedDisplay.textContent = btn.dataset.display;
        }
        if (this.form) {
            this.form.classList.remove("d-none");
            this.form.scrollIntoView({behavior: "smooth", block: "nearest"});
        }
    },

    /**
     * Tz dropdown change — reload with ``?tz=<value>`` so the server
     * buckets explicitly. ``URL`` preserves the current path (incl. the
     * optional ``/year/month`` segments).
     *
     * @param {Event} ev
     */
    _onDetailsToggle(ev) {
        const opened = ev.currentTarget;
        if (!opened.open) return;
        this.el.querySelectorAll(".o_wab_description details").forEach((d) => {
            if (d !== opened) d.removeAttribute("open");
        });
    },

    _onTzSelectChange(ev) {
        const tz = ev.currentTarget.value;
        if (!tz) {
            return;
        }
        const url = new URL(window.location.href);
        url.searchParams.set("tz", tz);
        window.location.assign(url.toString());
    },
});
