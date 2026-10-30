import {Component, useProps} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";

/**
 * Rooms x days grid of room.reservation.summary.summary_data.
 * A free day opens the quick reservation dialog for that room and day,
 * a booked day opens its reservation or folio.
 */
export class RoomReservationSummary extends Component {
    static template = "hotel_reservation.RoomSummary";
    props = useProps({...standardFieldProps});

    setup() {
        this.action = useService("action");
    }

    get summary() {
        return this.props.record.data[this.props.name] || {days: [], rooms: []};
    }

    cellTitle(room, cell) {
        if (cell.state === "free") {
            return _t("Book %(room)s on %(date)s", {room: room.name, date: cell.date});
        }
        return cell.label;
    }

    onCellClick(room, cell) {
        if (cell.state === "free") {
            // Save opens the new reservation
            this.action.doAction({
                name: _t("Quick Reservation"),
                type: "ir.actions.act_window",
                res_model: "quick.room.reservation",
                views: [[false, "form"]],
                target: "new",
                context: {
                    default_room_id: room.id,
                    quick_reservation_date: cell.date,
                },
            });
        } else {
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: cell.res_model,
                res_id: cell.res_id,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }
}

export const roomReservationSummary = {
    component: RoomReservationSummary,
    supportedTypes: ["json"],
};

registry.category("fields").add("room_reservation_summary", roomReservationSummary);
