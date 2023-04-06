# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ReportTestCheckin(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkin_qweb"
    _description = "Auxiliar to get the check in report"

    def _get_room_type(self, date_start, date_end):
        reservations = self.env["hotel.reservation"].search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return reservations

    def _get_room_nos(self, date_start, date_end):
        reservations = self.env["hotel.reservation"].search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return reservations

    def get_checkin(self, date_start, date_end):
        reservations = self.env["hotel.reservation"].search(
            [("checkin", ">=", date_start), ("checkin", "<=", date_end)]
        )
        return reservations

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.reservation"].browse(docids)
        date_start = data.get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],
        )
        rm_act = self.with_context(**data["form"].get("used_context", {}))
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        get_checkin = rm_act.get_checkin(date_start, date_end)
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_room_type": _get_room_type,
            "get_room_nos": _get_room_nos,
            "get_checkin": get_checkin,
        }


class ReportTestCheckout(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkout_qweb"
    _description = "Auxiliar to get the check out report"

    def _get_room_type(self, date_start, date_end):
        reservations = self.env["hotel.reservation"].search(
            [("checkout", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return reservations

    def _get_room_nos(self, date_start, date_end):
        reservations = self.env["hotel.reservation"].search(
            [("checkout", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return reservations

    def _get_checkout(self, date_start, date_end):
        reservations = self.env["hotel.reservation"].search(
            [("checkout", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return reservations

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.reservation"].browse(docids)
        date_start = data.get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],
        )
        rm_act = self.with_context(**data["form"].get("used_context", {}))
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        _get_checkout = rm_act._get_checkout(date_start, date_end)
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_room_type": _get_room_type,
            "get_room_nos": _get_room_nos,
            "get_checkout": _get_checkout,
        }


class ReportTestMaxroom(models.AbstractModel):
    _name = "report.hotel_reservation.report_maxroom_qweb"
    _description = "Auxiliar to get the room report"

    def _get_room_type(self, date_start, date_end):
        res = self.env["hotel.reservation"].search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return res

    def _get_room_nos(self, date_start, date_end):
        res = self.env["hotel.reservation"].search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return res

    def _get_data(self, date_start, date_end):
        res = self.env["hotel.reservation"].search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return res

    def _get_room_used_detail(self, date_start, date_end):
        room_used_details = []
        hotel_room_obj = self.env["hotel.room"]
        for room in hotel_room_obj.search([]):
            counter = 0
            details = {}
            if room.room_reservation_line_ids:
                end_date = datetime.strptime(date_end, DEFAULT_SERVER_DATETIME_FORMAT)
                start_date = datetime.strptime(
                    date_start, DEFAULT_SERVER_DATETIME_FORMAT
                )
                counter = len(
                    room.room_reservation_line_ids.filtered(
                        lambda l: start_date <= l.check_in <= end_date
                    )
                )
            if counter >= 1:
                details.update({"name": room.name or "", "no_of_times_used": counter})
                room_used_details.append(details)
        return room_used_details

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.reservation"].browse(docids)
        date_start = data["form"].get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],
        )
        rm_act = self.with_context(**data["form"].get("used_context", {}))
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        _get_data = rm_act._get_data(date_start, date_end)
        _get_room_used_detail = rm_act._get_room_used_detail(date_start, date_end)
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_room_type": _get_room_type,
            "get_room_nos": _get_room_nos,
            "get_data": _get_data,
            "get_room_used_detail": _get_room_used_detail,
        }


class ReportRoomReservation(models.AbstractModel):
    _name = "report.hotel_reservation.report_room_reservation_qweb"
    _description = "Auxiliar to get the room report"

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env["hotel.reservation"]
        tids = reservation_obj.search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        res = reservation_obj.browse(tids)
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env["hotel.reservation"]
        tids = reservation_obj.search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        res = reservation_obj.browse(tids)
        return res

    def _get_data(self, date_start, date_end):
        reservation_obj = self.env["hotel.reservation"]
        res = reservation_obj.search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return res

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.reservation"].browse(docids)
        date_start = data.get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],
        )
        rm_act = self.with_context(**data["form"].get("used_context", {}))
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        _get_data = rm_act._get_data(date_start, date_end)
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_room_type": _get_room_type,
            "get_room_nos": _get_room_nos,
            "get_data": _get_data,
        }
