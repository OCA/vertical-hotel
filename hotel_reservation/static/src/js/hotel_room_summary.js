odoo.define('hotel_reservation.hotel_room_summary', function (require) {
'use strict';

var core = require('web.core');
var Widget= require('web.Widget');
var widgetRegistry = require('web.widget_registry');
var FieldManagerMixin = require('web.FieldManagerMixin');
var time = require('web.time');
var _t = core._t;
var QWeb = core.qweb;
var FormView = require('web.FormView');
var rpc = require('web.rpc');


var MyWidget = Widget.extend(FieldManagerMixin, {

	template: "hotel_template",
    view_type: "form",
    init: function (parent, model, state) {
        this._super(parent);
        FieldManagerMixin.init.call(this);
        // init code here
        var id = 1;
        rpc.query({
            model: 'room.reservation.summary',
            method: 'read',
            args: [[id],['name'],['date_from']],
        }).then(function(res) {
            });
        this.set({
            date_to: false,
            date_from: false,
            summary_header: false,
            room_summary: false,
        });
        this.summary_header = [];
        this.room_summary = [];
        this.on("_onFieldChanged:date_from", this, function() {
            this.set({"date_from": time.str_to_datetime(this.get_field_value("date_from"))});
        });
        this.on("_onFieldChanged:date_to", this, function() {
            this.set({"date_to": time.str_to_datetime(this.get_field_value("date_to"))});
        });
        this.on("_onFieldChanged:summary_header", this, function() {
            this.set({"summary_header": this.get_field_value("summary_header")});
        });
        this.on("_onFieldChanged:room_summary", this, function() {
            this.set({"room_summary":this.get_field_value("room_summary")});
        });
    },
    initialize_content: function() {
        var self = this;
        if (self.setting)
            return;
        
        if (!this.summary_header || !this.room_summary)
               return
        // don't render anything until we have summary_header and room_summary
               
        this.destroy_content();
        
        if (this.get("summary_header")) {
         this.summary_header = py.eval(this.get("summary_header"));
        }
        if (this.get("room_summary")) {
         this.room_summary = py.eval(this.get("room_summary"));
        }
        this.renderElement();
        this.view_loading();
     },
     initialize_field: function() {
         FormView.ReinitializeWidgetMixin.initialize_field.call(this);
         var self = this;
         self.on("change:summary_header", self, self.initialize_content);
         self.on("change:room_summary", self, self.initialize_content);
     },
     view_loading: function(r) {
         return this.load_form(r);
     },

     load_form: function(data) {
         self.action_manager = new ActionManager(self);
         this.$el.find(".table_free").bind("click", function(event){
             self.action_manager.do_action({
                     type: 'ir.actions.act_window',
                     res_model: "quick.room.reservation",
                     views: [[false, 'form']],
                     target: 'new',
                     context: {"room_id": $(this).attr("data"), 'date': $(this).attr("date")},
             });
         });
     },
     renderElement: function() {
//         this.destroy_content();
         this.$el.html(QWeb.render("RoomSummary", {widget: this}));
    },
    start: function () {
    },
});

widgetRegistry.add(
    'Room_Reservation', MyWidget
);
return MyWidget
});
