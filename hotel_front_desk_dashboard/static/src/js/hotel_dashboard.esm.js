import {
    Component,
    markup,
    onWillStart,
    onWillUnmount,
    proxy,
    useProps,
} from "@odoo/owl";
import {KeepLast} from "@web/core/utils/concurrency";
import {_t} from "@web/core/l10n/translation";
import {formatCurrency} from "@web/core/currency";
import {registry} from "@web/core/registry";
import {standardActionServiceProps} from "@web/webclient/actions/action_plugin";
import {useDebounced} from "@web/core/utils/timing";
import {useService} from "@web/core/utils/hooks";

// The screen is meant to sit open on the front desk all shift, so it
// re-reads itself rather than waiting to be told the world moved on.
const AUTO_REFRESH_MS = 60 * 1000;
// Wait for the receptionist to stop typing before searching.
const SEARCH_DELAY_MS = 300;

export class HotelFrontDeskDashboard extends Component {
    static template = "hotel_front_desk_dashboard.Dashboard";
    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({
            loading: true,
            error: false,
            data: null,
            autoRefresh: true,
            search: "",
            searching: false,
            results: null,
        });
        // Only the answer to the latest search is shown: a slow answer to
        // an older search must not overwrite a newer one.
        this.searchKeepLast = new KeepLast();
        this.debouncedSearch = useDebounced(() => this.runSearch(), SEARCH_DELAY_MS);
        onWillStart(() => this.loadData());
        this.refreshTimer = setInterval(() => this.onAutoRefresh(), AUTO_REFRESH_MS);
        onWillUnmount(() => clearInterval(this.refreshTimer));
    }

    async loadData() {
        this.state.loading = true;
        this.state.error = false;
        try {
            this.state.data = await this.orm.call(
                "hotel.dashboard",
                "get_dashboard_data",
                []
            );
        } catch {
            this.state.error = true;
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Silent reload on the timer: no spinner, and a transient failure
     * leaves the last good figures on screen rather than blanking a
     * dashboard nobody is currently looking at.
     */
    async onAutoRefresh() {
        if (!this.state.autoRefresh || this.state.loading) {
            return;
        }
        try {
            this.state.data = await this.orm.call(
                "hotel.dashboard",
                "get_dashboard_data",
                []
            );
            this.state.error = false;
        } catch {
            // Keep showing the previous data; the next tick may succeed.
        }
    }

    toggleAutoRefresh() {
        this.state.autoRefresh = !this.state.autoRefresh;
    }

    async onRefresh() {
        await this.loadData();
    }

    /**
     * @param {Number} amount
     * @returns {String} amount in the company currency
     */
    formatAmount(amount) {
        return formatCurrency(amount, this.state.data?.currency_id);
    }

    /**
     * Drill a figure down to the records it was counted from. The domain
     * is rebuilt server-side so the list always matches the tile, even if
     * the dashboard has been sitting open for a while.
     *
     * @param {String} tile key understood by hotel.dashboard._get_tile_records
     */
    async openTile(tile) {
        const action = await this.orm.call("hotel.dashboard", "get_tile_action", [
            tile,
        ]);
        await this.action.doAction(action);
    }

    /**
     * Same as openTile, for a figure nested inside another clickable tile.
     *
     * @param {MouseEvent} ev
     * @param {String} tile
     */
    async openSubTile(ev, tile) {
        // The sub-figure sits inside a clickable tile; without this the
        // parent tile's own drill-down would fire too.
        ev.stopPropagation();
        ev.preventDefault();
        await this.openTile(tile);
    }

    /**
     * Keyboard equivalent of clicking a tile, so the dashboard stays
     * usable without a mouse.
     *
     * @param {KeyboardEvent} ev
     * @param {String} tile
     */
    async onTileKeydown(ev, tile) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            await this.openTile(tile);
        }
    }

    /**
     * Keyboard equivalent of clicking a sub-figure.
     *
     * @param {KeyboardEvent} ev
     * @param {String} tile
     */
    async onSubTileKeydown(ev, tile) {
        if (ev.key === "Enter" || ev.key === " ") {
            await this.openSubTile(ev, tile);
        }
    }

    onSearchInput(ev) {
        this.state.search = ev.target.value;
        if (!this.state.search.trim()) {
            this.debouncedSearch.cancel();
            // Drop the answer of a search still running
            this.searchKeepLast.add(Promise.resolve());
            this.state.results = null;
            this.state.searching = false;
            return;
        }
        this.state.searching = true;
        this.debouncedSearch();
    }

    async runSearch() {
        let results = [];
        try {
            results = await this.searchKeepLast.add(
                this.orm.call("hotel.dashboard", "search_guests", [this.state.search])
            );
        } catch {
            // A failed search shows no result; a newer one may still come
        }
        // KeepLast never resolves a superseded search, so this is the
        // answer to the text in the box
        this.state.results = results;
        this.state.searching = false;
    }

    clearSearch() {
        this.debouncedSearch.cancel();
        this.searchKeepLast.add(Promise.resolve());
        this.state.search = "";
        this.state.results = null;
        this.state.searching = false;
    }

    openFolio(folioId) {
        this.action.doAction({
            name: _t("Folio"),
            res_model: "hotel.folio",
            type: "ir.actions.act_window",
            views: [[false, "form"]],
            res_id: folioId,
        });
    }

    openRoom(roomId) {
        this.action.doAction({
            name: _t("Room"),
            res_model: "hotel.room",
            type: "ir.actions.act_window",
            views: [[false, "form"]],
            res_id: roomId,
        });
    }

    /**
     * @param {String} readiness
     * @returns {Object} badge class and label for a turnover row
     */
    turnoverBadge(readiness) {
        switch (readiness) {
            case "ready":
                return {class: "bg-success", label: _t("Ready")};
            case "not_ready":
                return {class: "bg-danger", label: _t("Needs cleaning")};
            case "stale":
                return {class: "bg-warning text-dark", label: _t("Not confirmed")};
            case "occupied":
                return {class: "bg-warning text-dark", label: _t("Guest still in")};
            default:
                return {class: "bg-secondary", label: _t("Not tracked")};
        }
    }

    // Sentences built from figures: one translatable string each (with the
    // singular apart), so they can be translated as a whole.

    inHouseStaysText() {
        const count = this.state.data.in_house_stays;
        return count === 1
            ? _t("right now, across %s stay", count)
            : _t("right now, across %s stays", count);
    }

    departuresOverdueText() {
        return _t("%s overdue", this.state.data.departures_overdue);
    }

    departuresTodayText() {
        return _t("of %s departures today", this.state.data.departures.length);
    }

    turnoversNotReadyText() {
        return _t("%s not ready yet", this.state.data.turnovers_at_risk);
    }

    unassignedReservationsText() {
        const count = this.state.data.unassigned_reservations;
        const values = {count: markup`<strong>${count}</strong>`};
        return count === 1
            ? _t(
                  "%(count)s confirmed reservation has no folio yet - nobody has been given a room.",
                  values
              )
            : _t(
                  "%(count)s confirmed reservations have no folio yet - nobody has been given a room.",
                  values
              );
    }
}

registry
    .category("actions")
    .add("hotel_front_desk_dashboard_action", HotelFrontDeskDashboard);
