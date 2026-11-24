# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ReportReservationBase(models.AbstractModel):
    """Common part of the reservation reports printed from the wizard: the
    period (``data["form"]``, default: today to the end of the month) and
    the reservations it selects."""

    _name = "report.hotel_reservation.report_base"
    _description = "Hotel reservation report base"

    @api.model
    def _get_period(self, data):
        form = (data or {}).get("form") or {}
        today = datetime.combine(fields.Date.context_today(self), time.min)
        date_start = fields.Datetime.to_datetime(form.get("date_start")) or today
        date_end = fields.Datetime.to_datetime(form.get("date_end")) or (
            today + relativedelta(day=1, months=1, seconds=-1)
        )
        return date_start, date_end

    @api.model
    def _get_reservations(self, date_start, date_end):
        """Reservations shown by the report; overridden per report."""
        return self.env["hotel.reservation"]

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start, date_end = self._get_period(data)
        return {
            "doc_ids": docids,
            "doc_model": "hotel.reservation",
            "docs": self.env["hotel.reservation"],
            "data": {"date_start": date_start, "date_end": date_end},
            "reservations": self._get_reservations(date_start, date_end),
        }


class ReportTestCheckin(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkin_qweb"
    _inherit = "report.hotel_reservation.report_base"
    _description = "Auxiliar to get the check in report"

    @api.model
    def _get_reservations(self, date_start, date_end):
        return self.env["hotel.reservation"].search(
            [
                ("checkin", ">=", date_start),
                ("checkin", "<=", date_end),
                ("state", "!=", "cancel"),
            ],
            order="checkin, id",
        )


class ReportTestCheckout(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkout_qweb"
    _inherit = "report.hotel_reservation.report_base"
    _description = "Auxiliar to get the check out report"

    @api.model
    def _get_reservations(self, date_start, date_end):
        return self.env["hotel.reservation"].search(
            [
                ("checkout", ">=", date_start),
                ("checkout", "<=", date_end),
                ("state", "!=", "cancel"),
            ],
            order="checkout, id",
        )


class ReportRoomReservation(models.AbstractModel):
    _name = "report.hotel_reservation.report_room_reservation_qweb"
    _inherit = "report.hotel_reservation.report_base"
    _description = "Auxiliar to get the room report"

    @api.model
    def _get_reservations(self, date_start, date_end):
        """Reservations with a stay overlapping the period."""
        return self.env["hotel.reservation"].search(
            [
                ("checkin", "<", date_end),
                ("checkout", ">", date_start),
                ("state", "!=", "cancel"),
            ],
            order="checkin, id",
        )


class ReportTestMaxroom(models.AbstractModel):
    _name = "report.hotel_reservation.report_maxroom_qweb"
    _inherit = "report.hotel_reservation.report_base"
    _description = "Auxiliar to get the room report"

    @api.model
    def _get_room_used_detail(self, date_start, date_end):
        """Rooms booked in the period with their number of bookings, most
        used first."""
        groups = self.env["hotel.room.reservation.line"]._read_group(
            [
                ("check_in", ">=", date_start),
                ("check_in", "<=", date_end),
                ("room_id", "!=", False),
            ],
            ["room_id"],
            ["__count"],
        )
        return [
            {"name": room.name or "", "no_of_times_used": count}
            for room, count in sorted(groups, key=lambda g: (-g[1], g[0].name or ""))
        ]

    @api.model
    def _get_report_values(self, docids, data=None):
        values = super()._get_report_values(docids, data)
        values["get_room_used_detail"] = self._get_room_used_detail(
            values["data"]["date_start"], values["data"]["date_end"]
        )
        return values
