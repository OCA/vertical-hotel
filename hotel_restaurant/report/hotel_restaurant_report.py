# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class RestaurantPeriodReport(models.AbstractModel):
    """Common part of the reports printed from a wizard: the period of
    ``data["form"]`` (default: today to the end of the month)."""

    _name = "report.hotel_restaurant.report_period"
    _description = "Hotel restaurant period report"

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
    def _get_folios(self, date_start, date_end, orders_field):
        """Folios with a stay overlapping the period and restaurant orders
        in ``orders_field``."""
        return (
            self.env["hotel.folio"]
            .search(
                [
                    ("checkin_date", "<", date_end),
                    ("checkout_date", ">", date_start),
                ],
                order="checkin_date, id",
            )
            .filtered(orders_field)
        )


class HotelRestaurantReport(models.AbstractModel):
    _name = "report.hotel_restaurant.report_res_table"
    _inherit = "report.hotel_restaurant.report_period"
    _description = "report.hotel_restaurant.report_res_table"

    def get_res_data(self, date_start, date_end):
        """Table bookings overlapping the period, cancelled ones excluded."""
        return self.env["hotel.restaurant.reservation"].search(
            [
                ("start_date", "<", date_end),
                ("end_date", ">", date_start),
                ("state", "!=", "cancel"),
            ],
            order="start_date, id",
        )

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start, date_end = self._get_period(data)
        return {
            "doc_ids": docids,
            "doc_model": "hotel.restaurant.reservation",
            "docs": self.env["hotel.restaurant.reservation"],
            "data": {"date_start": date_start, "date_end": date_end},
            "Reservations": self.get_res_data(date_start, date_end),
        }


class ReportKot(models.AbstractModel):
    _name = "report.hotel_restaurant.report_hotel_order_kot"
    _description = "report.hotel_restaurant.report_hotel_order_kot"

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            "doc_ids": docids,
            "doc_model": "hotel.restaurant.order",
            "docs": self.env["hotel.restaurant.order"].browse(docids),
            "data": data,
        }


class FolioRestReport(models.AbstractModel):
    """Orders of table bookings (hotel.reservation.order) per folio."""

    _name = "report.hotel_restaurant.report_rest_order"
    _inherit = "report.hotel_restaurant.report_period"
    _description = "Folio Rest Report"

    _orders_field = "hotel_reservation_orders_ids"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start, date_end = self._get_period(data)
        folios = self._get_folios(date_start, date_end, self._orders_field)
        form = (data or {}).get("form") or {}
        return {
            "doc_ids": docids,
            "doc_model": "hotel.folio",
            "docs": folios,
            "data": {"date_start": date_start, "date_end": date_end},
            "folios": folios,
            "orders_field": self._orders_field,
            "with_details": form.get("check"),
            "order_date": lambda order: (
                order.order_date
                if order._name == "hotel.reservation.order"
                else order.o_date
            ),
            "grand_total": sum(
                sum(folio[self._orders_field].mapped("amount_total"))
                for folio in folios
            ),
        }


class FolioReservReport(models.AbstractModel):
    """Table orders (hotel.restaurant.order) per folio."""

    _name = "report.hotel_restaurant.report_reserv_order"
    _inherit = "report.hotel_restaurant.report_rest_order"
    _description = "report.hotel_restaurant.report_reserv_order"

    _orders_field = "hotel_restaurant_orders_ids"
