/* global py */
odoo.define('hotel_reservation.hotel_room_summary', function (require) {
    'use strict';

    var core = require('web.core');
    var basicFields = require('web.basic_fields');
    var FieldText = basicFields.FieldText;
    var registry = require('web.field_registry');

    var QWeb = core.qweb;

    var MyWidget = FieldText.extend({

        init: function () {
            this._super.apply(this, arguments);
            if (this.mode === 'edit') {
                this.tagName = 'span';
            }
            this.set({
                summary_header: py.eval(this.recordData.summary_header),
                room_summary: py.eval(this.recordData.room_summary ),
            });
        },
        start: function () {
            var self = this;
            if (self.setting) {
                return;
            }

            if (! this.get("summary_header") || ! this.get("room_summary")) {
                return;
            }

            this.renderElement();
            this.view_loading();
        },
        view_loading: function (r) {
            return this.load_form(r);
        },
        load_form: function () {
            var self = this;
            this.$el.find(".table_free").bind("click", function () {
                self.do_action({
                    type: 'ir.actions.act_window',
                    res_model: "quick.room.reservation",
                    views: [[false, 'form']],
                    target: 'new',
                    context: {
                        "room_id": $(this).attr("data"),
                        'date': $(this).attr("date"),
                        'default_adults': 1,
                    },
                });
            });
        },
        renderElement: function () {
            this._super();
            this.$el.html(QWeb.render("RoomSummary", {widget: this}));
        },
        reset: function (record, event) {
            var res = this._super(record, event);
            this.set({
                "summary_header": py.eval(this.recordData.summary_header),
                "room_summary":py.eval(this.recordData.room_summary),
            });
            this.renderElement();
            this.view_loading();
            return res;
        },

    });

    registry.add(
        'Room_Reservation', MyWidget
    );
    return MyWidget;
});
