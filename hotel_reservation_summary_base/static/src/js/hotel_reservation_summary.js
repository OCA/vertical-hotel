/* global py */
odoo.define('hotel_reservation_summary_base.hotel_reservation_summary', function (require) {
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
                room_summary: py.eval(this.recordData.room_summary),
            });
        },
        start: function () {
            var self = this;
            if (self.setting) {
                return;
            }

            if (!this.get("room_summary")) {
                return;
            }

            this.renderElement();
            this.view_loading();
        },
        view_loading: function (r) {
            return this.load_form(r);
        },
        load_form: function () {
            this.bind_quick_room_reservation_action();
            this.bind_room_action();
        },
        bind_quick_room_reservation_action: function () {
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
        bind_room_action: function () {
            var self = this;
            this.$el.find(".table_room").bind("click", function () {
                var room_id = Number($(this).attr("room_id"));
                self.do_action({
                    name: 'Hotel Room',
                    res_model: 'hotel.room',
                    res_id: room_id,
                    views: [[false, 'form']],
                    type: 'ir.actions.act_window',
                    target: 'new',
                    context: self.context,
                });
            });
        },
        renderElement: function () {
            this._super();
            this.$el.html(
                QWeb.render("hotel_room_reservation_summary_table_template",
                    {widget: this}));
        },
        reset: function (record, event) {
            var res = this._super(record, event);
            this.set({
                "room_summary": py.eval(this.recordData.room_summary),
            });
            this.renderElement();
            this.view_loading();
            return res;
        },

    });

    registry.add(
        'room_reservation_widget', MyWidget
    );
    return MyWidget;
});
