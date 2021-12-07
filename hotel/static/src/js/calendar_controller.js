odoo.define('hotel.CalendarController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController');
var config = require('web.config');
var core = require('web.core');
var Dialog = require('web.Dialog');
var dialogs = require('web.view_dialogs');
var QuickCreate = require('web.CalendarQuickCreate');

var CalendarController = require("web.CalendarController")

var _t = core._t;

function dateToServer (date) {
    return date.clone().utc().locale('en').format('YYYY-MM-DD HH:mm:ss');
}

var HotelCalendarController = CalendarController.include({

    custom_events: _.extend({}, CalendarController.prototype.custom_events, {
        openCreate: '_onCustomOpenCreate',
    }),

    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
    },

    _onCustomOpenCreate: function (event) {
        var self = this;
        if (this.model.get().scale === "month") {
            event.data.allDay = true;
        }
        var data = this.model.calendarEventToRecord(event.data);

        /* special for hotel */
        if (this.modelName == "folio.room.line") {
            if (data.check_in.isBefore()){
                if (data.check_in.format("YYYY-MM-DD") != moment().format("YYYY-MM-DD")) {
                    return this.do_warn(_t("Old date !"));
                }
            };
        }
        /* ----------------- */

        var context = _.extend({}, this.context, event.options && event.options.context);
        context.default_name = data.name || null;
        context['default_' + this.mapping.date_start] = data[this.mapping.date_start] || null;
        if (this.mapping.date_stop) {
            context['default_' + this.mapping.date_stop] = data[this.mapping.date_stop] || null;
        }
        if (this.mapping.date_delay) {
            context['default_' + this.mapping.date_delay] = data[this.mapping.date_delay] || null;
        }
        if (this.mapping.all_day) {
            context['default_' + this.mapping.all_day] = data[this.mapping.all_day] || null;
        }

        for (var k in context) {
            if (context[k] && context[k]._isAMomentObject) {
                context[k] = dateToServer(context[k]);
            }
        }

        var options = _.extend({}, this.options, event.options, {
            context: context,
            title: _.str.sprintf(_t('Create: %s'), (this.displayName || this.renderer.arch.attrs.string))
        });

        if (this.quick != null) {
            this.quick.destroy();
            this.quick = null;
        }

        if (!options.disableQuickCreate && !event.data.disableQuickCreate && this.quickAddPop) {
            this.quick = new QuickCreate(this, true, options, data, event.data);
            this.quick.open();
            this.quick.opened(function () {
                self.quick.focus();
            });
            return;
        }

        var title = _t("Create");
        if (this.renderer.arch.attrs.string) {
            title += ': ' + this.renderer.arch.attrs.string;
        }
        if (this.eventOpenPopup) {
            if (this.previousOpen) { this.previousOpen.close(); }
            this.previousOpen = new dialogs.FormViewDialog(self, {
                res_model: this.modelName,
                context: context,
                title: title,
                view_id: this.formViewId || false,
                disable_multiple_selection: true,
                on_saved: function () {
                    if (event.data.on_save) {
                        event.data.on_save();
                    }
                    self.reload();
                },
            });
            this.previousOpen.open();
        } else {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: this.modelName,
                views: [[this.formViewId || false, 'form']],
                target: 'current',
                context: context,
            });
        }
    },
});
return HotelCalendarController;
});
