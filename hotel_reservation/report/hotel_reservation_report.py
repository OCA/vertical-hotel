# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ReportCheckin(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkin_qweb"
    _description = "Auxiliar to get the check in report"

    def _get_checkin_reservation(self, date_start, date_end):
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
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[
                :10
            ],
        )
        rm_act = self.with_context(data["form"].get("used_context", {}))
        _get_checkin_reservation = rm_act._get_checkin_reservation(
            date_start, date_end
        )
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_checkin": _get_checkin_reservation,
        }


class ReportCheckout(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkout_qweb"
    _description = "Auxiliar to get the check out report"

    def _get_checkout_reservation(self, date_start, date_end):
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
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[
                :10
            ],
        )
        rm_act = self.with_context(data["form"].get("used_context", {}))
        _get_checkout_reservation = rm_act._get_checkout_reservation(
            date_start, date_end
        )
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_checkout": _get_checkout_reservation,
        }


class ReportMaxroom(models.AbstractModel):
    _name = "report.hotel_reservation.report_maxroom_qweb"
    _description = "Auxiliar to get the room report"

    def _get_room_used_detail(self, date_start, date_end):
        room_used_details = []
        hotel_room_obj = self.env["hotel.room"]
        for room in hotel_room_obj.search([]):
            counter = 0
            details = {}
            if room.room_reservation_line_ids:
                end_date = datetime.strptime(
                    date_end, DEFAULT_SERVER_DATETIME_FORMAT
                )
                start_date = datetime.strptime(
                    date_start, DEFAULT_SERVER_DATETIME_FORMAT
                )
                counter = len(
                    room.room_reservation_line_ids.filtered(
                        lambda l: start_date <= l.check_in <= end_date
                    )
                )
            if counter >= 1:
                details.update(
                    {"name": room.name or "", "no_of_times_used": counter}
                )
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
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[
                :10
            ],
        )
        rm_act = self.with_context(data["form"].get("used_context", {}))
        _get_room_used_detail = rm_act._get_room_used_detail(
            date_start, date_end
        )
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_room_used_detail": _get_room_used_detail,
        }


class ReportRoomReservation(models.AbstractModel):
    _name = "report.hotel_reservation.report_room_reservation_qweb"
    _description = "Auxiliar to get the room report"

    def _get_reservation_data(self, date_start, date_end):
        reservation = self.env["hotel.reservation"].search(
            [("checkin", ">=", date_start), ("checkout", "<=", date_end)]
        )
        return reservation

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
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[
                :10
            ],
        )
        rm_act = self.with_context(data["form"].get("used_context", {}))
        _get_reservation_data = rm_act._get_reservation_data(
            date_start, date_end
        )
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_data": _get_reservation_data,
        }
