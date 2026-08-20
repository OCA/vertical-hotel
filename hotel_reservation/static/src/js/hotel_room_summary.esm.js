import {TextField, textField} from "@web/views/fields/text/text_field";
import {onPatched, useState} from "@odoo/owl";
import {evaluateExpr} from "@web/core/py_js/py";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class RoomReservation extends TextField {
    static template = "hotel_reservation.RoomSummary";
    static components = {...TextField.components};

    setup() {
        super.setup();
        this.actionService = useService("action");
        this.state = useState({
            date_to: false,
            date_from: false,
            summary_header: evaluateExpr(this.props.record.data.summary_header),
            room_summary: evaluateExpr(this.props.record.data.room_summary),
        });
        onPatched(() => {
            this.state.summary_header = evaluateExpr(
                this.props.record.data.summary_header
            );
            this.state.room_summary = evaluateExpr(this.props.record.data.room_summary);
        });
    }

    loadForm(ev, roomId, statusDate) {
        ev.stopPropagation();
        ev.preventDefault();
        if (!roomId || !statusDate) {
            return;
        }
        this.actionService.doAction({
            name: "Room Reservation",
            res_model: "quick.room.reservation",
            views: [[false, "form"]],
            type: "ir.actions.act_window",
            view_mode: "form",
            target: "new",
            context: {
                default_room_id: roomId,
                default_check_in: statusDate,
                default_adults: 1,
            },
        });
    }
}
export const myWidgetadditionClasses = {
    ...textField,
    component: RoomReservation,
    additionalClasses: [...(textField.additionalClasses || []), "o_field_text"],
};
registry.category("fields").add("room_reservation_summary", myWidgetadditionClasses);
