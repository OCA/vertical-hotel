from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt


class RoomReservationSummary(models.Model):
    _name = "room.reservation.summary"
    _description = "Room reservation summary"

    name = fields.Char(
        "Reservation Summary", default="Reservations Summary", invisible=True
    )
    date_from = fields.Datetime("Date From")
    date_to = fields.Datetime("Date To")
    summary_header = fields.Text("Summary Header")
    room_summary = fields.Text("Room Summary")

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(RoomReservationSummary, self).default_get(fields)
        # Added default datetime as today and date to as today + 30.
        from_dt = datetime.today()
        dt_from = from_dt.strftime(dt)
        to_dt = from_dt + relativedelta(days=30)
        dt_to = to_dt.strftime(dt)
        res.update({"date_from": dt_from, "date_to": dt_to})

        if not self.date_from and self.date_to:
            date_today = datetime.datetime.today()
            first_day = datetime.datetime(
                date_today.year, date_today.month, 1, 0, 0, 0
            )
            first_temp_day = first_day + relativedelta(months=1)
            last_temp_day = first_temp_day - relativedelta(days=1)
            last_day = datetime.datetime(
                last_temp_day.year,
                last_temp_day.month,
                last_temp_day.day,
                23,
                59,
                59,
            )
            date_froms = first_day.strftime(dt)
            date_ends = last_day.strftime(dt)
            res.update({"date_from": date_froms, "date_to": date_ends})
        return res

    @api.multi
    def room_reservation(self):
        """
        @param self: object pointer
        """
        mod_obj = self.env["ir.model.data"]
        if self._context is None:
            self._context = {}
        model_data_ids = mod_obj.search(
            [
                ("model", "=", "ir.ui.view"),
                ("name", "=", "view_hotel_reservation_form"),
            ]
        )
        resource_id = model_data_ids.read(fields=["res_id"])[0]["res_id"]
        return {
            "name": _("Reconcile Write-Off"),
            "context": self._context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hotel.reservation",
            "views": [(resource_id, "form")],
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.onchange("date_from", "date_to")  # noqa: C901
    def get_room_summary(self):  # noqa: C901
        """
        @param self: object pointer
         """
        res = {}
        all_detail = []
        room_obj = self.env["hotel.room"]
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        folio_room_line_obj = self.env["folio.room.line"]
        user_obj = self.env["res.users"]
        date_range_list = []
        main_header = []
        summary_header_list = ["Rooms"]
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise UserError(
                    _(
                        "Please Check Time period Date From can't \
                                   be greater than Date To !"
                    )
                )
            if self._context.get("tz", False):
                timezone = pytz.timezone(self._context.get("tz", False))
            else:
                timezone = pytz.timezone("UTC")
            d_frm_obj = (
                datetime.strptime(self.date_from, dt)
                .replace(tzinfo=pytz.timezone("UTC"))
                .astimezone(timezone)
            )
            d_to_obj = (
                datetime.strptime(self.date_to, dt)
                .replace(tzinfo=pytz.timezone("UTC"))
                .astimezone(timezone)
            )
            temp_date = d_frm_obj
            while temp_date <= d_to_obj:
                val = ""
                val = (
                    str(temp_date.strftime("%a"))
                    + " "
                    + str(temp_date.strftime("%b"))
                    + " "
                    + str(temp_date.strftime("%d"))
                )
                summary_header_list.append(val)
                date_range_list.append(temp_date.strftime(dt))
                temp_date = temp_date + timedelta(days=1)
            all_detail.append(summary_header_list)
            room_ids = room_obj.search([])
            all_room_detail = []
            for room in room_ids:
                room_detail = {}
                room_list_stats = []
                room_detail.update({"name": room.name or ""})
                if (
                    not room.room_reservation_line_ids
                    and not room.room_line_ids
                ):
                    for chk_date in date_range_list:
                        room_list_stats.append(
                            {
                                "state": "Free",
                                "date": chk_date,
                                "room_id": room.id,
                            }
                        )
                else:
                    for chk_date in date_range_list:
                        ch_dt = chk_date[:10] + " 23:59:59"
                        ttime = datetime.strptime(ch_dt, dt)
                        c = ttime.replace(tzinfo=timezone).astimezone(
                            pytz.timezone("UTC")
                        )
                        chk_date = c.strftime(dt)
                        reserline_ids = room.room_reservation_line_ids.ids
                        reservline_ids = reservation_line_obj.search(
                            [
                                ("id", "in", reserline_ids),
                                ("check_in", "<=", chk_date),
                                ("check_out", ">=", chk_date),
                                ("state", "=", "assigned"),
                            ]
                        )
                        if not reservline_ids:
                            sdt = dt
                            chk_date = datetime.strptime(chk_date, sdt)
                            chk_date = datetime.strftime(
                                chk_date - timedelta(days=1), sdt
                            )
                            reservline_ids = reservation_line_obj.search(
                                [
                                    ("id", "in", reserline_ids),
                                    ("check_in", "<=", chk_date),
                                    ("check_out", ">=", chk_date),
                                    ("state", "=", "assigned"),
                                ]
                            )
                            for res_room in reservline_ids:
                                rrci = res_room.check_in
                                rrco = res_room.check_out
                                cid = datetime.strptime(rrci, dt)
                                cod = datetime.strptime(rrco, dt)
                                dur = cod - cid
                                if room_list_stats:
                                    count = 0
                                    for rlist in room_list_stats:
                                        cidst = datetime.strftime(cid, dt)
                                        codst = datetime.strftime(cod, dt)
                                        rm_id = res_room.room_id.id
                                        ci = rlist.get("date") >= cidst
                                        co = rlist.get("date") <= codst
                                        rm = rlist.get("room_id") == rm_id
                                        st = rlist.get("state") == "Reserved"
                                        if ci and co and rm and st:
                                            count += 1
                                    if count - dur.days == 0:
                                        c_id1 = user_obj.browse(self._uid)
                                        c_id = c_id1.company_id
                                        con_add = 0
                                        amin = 0.0
                                        if c_id:
                                            con_add = c_id.additional_hours
                                        # When configured_addition_hours is
                                        # greater than zero then we calculate
                                        # additional minutes
                                        if con_add > 0:
                                            amin = abs(con_add * 60)
                                        hr_dur = abs(dur.seconds / 60)
                                        # When additional minutes is greater
                                        # than zero then check duration with
                                        # extra minutes and give the room
                                        # reservation status is reserved or
                                        # free
                                        if amin > 0:
                                            if hr_dur >= amin:
                                                reservline_ids = True
                                            else:
                                                reservline_ids = False
                                        else:
                                            if hr_dur > 0:
                                                reservline_ids = True
                                            else:
                                                reservline_ids = False
                                    else:
                                        reservline_ids = False
                        fol_room_line_ids = room.room_line_ids.ids
                        chk_state = ["draft", "cancel"]
                        folio_resrv_ids = folio_room_line_obj.search(
                            [
                                ("id", "in", fol_room_line_ids),
                                ("check_in", "<=", chk_date),
                                ("check_out", ">=", chk_date),
                                ("status", "not in", chk_state),
                            ]
                        )
                        if reservline_ids or folio_resrv_ids:
                            room_list_stats.append(
                                {
                                    "state": "Reserved",
                                    "date": chk_date,
                                    "room_id": room.id,
                                    "is_draft": "No",
                                    "data_model": "",
                                    "data_id": 0,
                                }
                            )
                        else:
                            room_list_stats.append(
                                {
                                    "state": "Free",
                                    "date": chk_date,
                                    "room_id": room.id,
                                }
                            )

                room_detail.update({"value": room_list_stats})
                all_room_detail.append(room_detail)
            main_header.append({"header": summary_header_list})
            self.summary_header = str(main_header)
            self.room_summary = str(all_room_detail)
        return res
