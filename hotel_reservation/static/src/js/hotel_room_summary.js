/* @odoo-module */

import {TextField} from "@web/views/fields/text/text_field";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {useState} from "@odoo/owl";
var FormView = require("web.FormView");
var py = window.py;
const {onWillUpdateProps} = owl;

export class MyWidget extends TextField {
    setup() {
        super.setup();
        console.log(this);
        this.actionService = useService("action");
        this.state = useState({
            date_to: false,
            date_from: false,
            summary_header: py.eval(this.props.record.data.summary_header),
            room_summary: py.eval(this.props.record.data.room_summary),
        });

        onWillUpdateProps(() => {
            this.state.summary_header = py.eval(this.props.record.data.summary_header);
            this.state.room_summary = py.eval(this.props.record.data.room_summary);
            console.log(FormView.ReinitializeWidgetMixin);
        });
    }
    resize() {
        return this; //overide the resize
    }
    async load_form(room_id, date) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "quick.room.reservation",
            views: [[false, "form"]],
            target: "new",
            context: {
                room_id: room_id,
                date: date,
                default_adults: 1,
            },
        });
    }
}

MyWidget.template = "RoomSummary";
MyWidget.components = {...TextField.components};
MyWidget.additionalClasses = [...(TextField.additionalClasses || []), "o_field_text"];
registry.category("fields").add("Room_Reservation", MyWidget);
