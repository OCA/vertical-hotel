# Copyright (C) 2023-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ReportUtils(models.AbstractModel):
    _name = "report.hotel_reservation.report_utils"
    _description = "Utility methods for report generation"

    def _convert_to_ist(self, utc_dt):
        user_tz = self._context.get("tz", "UTC")
        local_tz = pytz.timezone(user_tz)
        utc_tz = pytz.timezone("UTC")
        return utc_tz.localize(utc_dt).astimezone(local_tz)

    def _get_reservations(self, field_name, date_start, date_end):
        return self.env["hotel.reservation"].search(
            [(field_name, ">=", date_start), (field_name, "<=", date_end)]
        )

    def _prepare_date_range(self, date_start_str, date_end_str):
        if not date_start_str:
            date_start_str = fields.Date.today().strftime("%Y-%m-%d 00:00:00")
        if not date_end_str:
            date_end_str = (
                datetime.now() + relativedelta(months=+1, day=1, days=-1)
            ).strftime("%Y-%m-%d 23:59:59")

        date_start_utc = datetime.strptime(date_start_str, "%Y-%m-%d %H:%M:%S")
        date_end_utc = datetime.strptime(date_end_str, "%Y-%m-%d %H:%M:%S")
        date_start_ist = self._convert_to_ist(date_start_utc)
        date_end_ist = self._convert_to_ist(date_end_utc)

        date_start_server = fields.Datetime.to_string(
            date_start_ist - timedelta(hours=5, minutes=30)
        )
        date_end_server = fields.Datetime.to_string(
            date_end_ist - timedelta(hours=5, minutes=30)
        )

        return date_start_ist, date_end_ist, date_start_server, date_end_server


class ReportTestCheckin(ReportUtils):
    _name = "report.hotel_reservation.report_checkin_qweb"
    _description = "Auxiliary to get the check-in report"

    def get_checkin(self, date_start, date_end):
        return self._get_reservations("checkin", date_start, date_end)

    @api.model
    def _get_report_values(self, docids, data):
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")

        folio_profile = self.env["hotel.reservation"].browse(docids)
        (
            date_start_ist,
            date_end_ist,
            date_start_server,
            date_end_server,
        ) = self._prepare_date_range(
            data["form"].get("date_start"), data["form"].get("date_end")
        )

        reservations = self.get_checkin(date_start_server, date_end_server)

        return {
            "doc_ids": docids,
            "doc_model": self.env.context.get("active_model"),
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_checkin": reservations,
            "start_time": fields.Datetime.to_string(date_start_ist),
            "end_time": fields.Datetime.to_string(date_end_ist),
        }


class ReportTestCheckout(ReportUtils):
    _name = "report.hotel_reservation.report_checkout_qweb"
    _description = "Auxiliary to get the checkout report"

    def get_checkout(self, date_start, date_end):
        return self._get_reservations("checkout", date_start, date_end)

    @api.model
    def _get_report_values(self, docids, data):
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")

        folio_profile = self.env["hotel.reservation"].browse(docids)
        (
            date_start_ist,
            date_end_ist,
            date_start_server,
            date_end_server,
        ) = self._prepare_date_range(
            data["form"].get("date_start"), data["form"].get("date_end")
        )

        reservations = self.get_checkout(date_start_server, date_end_server)

        return {
            "doc_ids": docids,
            "doc_model": self.env.context.get("active_model"),
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_checkout": reservations,
            "start_time": fields.Datetime.to_string(date_start_ist),
            "end_time": fields.Datetime.to_string(date_end_ist),
        }


class ReportTestMaxroom(ReportUtils):
    _name = "report.hotel_reservation.report_maxroom_qweb"
    _description = "Auxiliary to get the room report"

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
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")

        folio_profile = self.env["hotel.reservation"].browse(docids)
        (
            date_start_ist,
            date_end_ist,
            date_start_server,
            date_end_server,
        ) = self._prepare_date_range(
            data["form"].get("date_start"), data["form"].get("date_end")
        )

        room_used_details = self._get_room_used_detail(
            date_start_server, date_end_server
        )

        return {
            "doc_ids": docids,
            "doc_model": self.env.context.get("active_model"),
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_room_used_detail": room_used_details,
            "start_time": fields.Datetime.to_string(date_start_ist),
            "end_time": fields.Datetime.to_string(date_end_ist),
        }


class ReportRoomReservation(ReportUtils):
    _name = "report.hotel_reservation.report_room_reservation_qweb"
    _description = "Auxiliary to get the room reservation report"

    @api.model
    def _get_report_values(self, docids, data):
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")

        folio_profile = self.env["hotel.reservation"].browse(docids)
        (
            date_start_ist,
            date_end_ist,
            date_start_server,
            date_end_server,
        ) = self._prepare_date_range(
            data["form"].get("date_start"), data["form"].get("date_end")
        )

        reservations = self._get_reservations(
            "checkin", date_start_server, date_end_server
        )

        return {
            "doc_ids": docids,
            "doc_model": self.env.context.get("active_model"),
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "get_data": reservations,
            "start_time": fields.Datetime.to_string(date_start_ist),
            "end_time": fields.Datetime.to_string(date_end_ist),
        }
