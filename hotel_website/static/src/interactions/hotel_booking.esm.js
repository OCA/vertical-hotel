/**
 * Conveniences for the hotel booking forms. Every form still submits and is
 * validated by the server without them; they only make dates and the guest
 * list easier to fill in.
 */
import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";

/**
 * @param {String} isoDate "YYYY-MM-DD"
 * @param {Number} days
 * @returns {String} "YYYY-MM-DD"
 */
function addDays(isoDate, days) {
    const [year, month, day] = isoDate.split("-").map(Number);
    return new Date(Date.UTC(year, month - 1, day + days)).toISOString().slice(0, 10);
}

function localToday() {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 10);
}

export class HotelStayDates extends Interaction {
    static selector = ".o_hotel_stay_dates";
    dynamicContent = {
        "input[name='checkin']": {"t-on-change": this.syncCheckoutMin},
    };

    setup() {
        this.checkinEl = this.el.querySelector("input[name='checkin']");
        this.checkoutEl = this.el.querySelector("input[name='checkout']");
    }

    start() {
        if (this.checkinEl && !this.checkinEl.min) {
            this.checkinEl.min = localToday();
        }
        this.syncCheckoutMin();
    }

    /**
     * Departure can never be before the day after arrival.
     */
    syncCheckoutMin() {
        if (!this.checkinEl?.value || !this.checkoutEl) {
            return;
        }
        const minCheckout = addDays(this.checkinEl.value, 1);
        this.checkoutEl.min = minCheckout;
        if (this.checkoutEl.value && this.checkoutEl.value < minCheckout) {
            this.checkoutEl.value = minCheckout;
        }
    }
}

export class HotelGuestRows extends Interaction {
    static selector = ".o_hotel_guests";
    dynamicContent = {
        ".o_hotel_add_guest": {"t-on-click": this.addGuest},
        _root: {"t-on-click": this.onRootClick},
    };

    addGuest() {
        const template = this.el.querySelector(".o_hotel_guest_row_template");
        const rows = this.el.querySelector(".o_hotel_guest_rows");
        if (!template || !rows) {
            return;
        }
        const row = template.cloneNode(true);
        row.classList.remove("d-none", "o_hotel_guest_row_template");
        // The template row is disabled so it is never submitted on its own.
        row.querySelectorAll("input, select").forEach((field) => {
            field.removeAttribute("disabled");
        });
        rows.appendChild(row);
        row.querySelector("input")?.focus();
    }

    /**
     * Remove buttons live in rows added after start, so they are handled by
     * delegation from the root instead of dynamicContent.
     *
     * @param {MouseEvent} ev
     */
    onRootClick(ev) {
        const button = ev.target.closest(".o_hotel_remove_guest");
        const row = button?.closest(".o_hotel_guest_rows .o_hotel_guest_row");
        if (!row) {
            return;
        }
        const rows = this.el.querySelectorAll(".o_hotel_guest_rows .o_hotel_guest_row");
        if (rows.length > 1) {
            row.remove();
        } else {
            row.querySelector("input").value = "";
            row.querySelector("select").value = "adult";
        }
    }
}

registry
    .category("public.interactions")
    .add("hotel_website.stay_dates", HotelStayDates);
registry
    .category("public.interactions")
    .add("hotel_website.guest_rows", HotelGuestRows);
