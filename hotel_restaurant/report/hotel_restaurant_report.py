# Copyright (C) 2023-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HotelRestaurantReport(models.AbstractModel):
    _name = "report.hotel_restaurant.report_res_table"
    _description = "report.hotel_restaurant.report_res_table"

    def _convert_to_ist(self, utc_dt):
        user_tz = self._context.get("tz", "UTC")
        local_tz = pytz.timezone(user_tz)
        utc_tz = pytz.timezone("UTC")

        utc_dt = utc_tz.localize(utc_dt)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt

    def get_res_data(self, date_start, date_end):
        data = []
        tids = self.env["hotel.restaurant.reservation"].search(
            [("start_date", ">=", date_start), ("end_date", "<=", date_end)]
        )
        for record in tids:
            data.append(
                {
                    "reservation": record.reservation_id,
                    "name": record.customer_id.name,
                    "start_date": record.start_date,
                    "end_date": record.end_date,
                }
            )

        # Convert start_date and end_date for each reservation
        for reservation in data:
            if isinstance(reservation["start_date"], datetime):
                start_time = reservation["start_date"]
            else:
                start_time = datetime.strptime(
                    reservation["start_date"], "%Y-%m-%d %H:%M:%S"
                )

            if isinstance(reservation["end_date"], datetime):
                end_time = reservation["end_date"]
            else:
                end_time = datetime.strptime(
                    reservation["end_date"], "%Y-%m-%d %H:%M:%S"
                )

            reservation["start_date"] = self._convert_to_ist(start_time).strftime(
                "%m/%d/%Y %H:%M:%S"
            )
            reservation["end_date"] = self._convert_to_ist(end_time).strftime(
                "%m/%d/%Y %H:%M:%S"
            )

        return data

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.restaurant.tables"].browse(docids)
        date_start_str = data["form"].get("date_start")
        date_end_str = data["form"].get("date_end")

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
        date_start = fields.Datetime.to_string(date_start_ist)
        date_end = fields.Datetime.to_string(date_end_ist)

        date_start_minus_5_30 = date_start_ist - timedelta(hours=5, minutes=30)
        date_end_minus_5_30 = date_end_ist - timedelta(hours=5, minutes=30)

        date_start_server = fields.Datetime.to_string(date_start_minus_5_30)
        date_end_server = fields.Datetime.to_string(date_end_minus_5_30)

        rm_act = self.with_context(**data["form"].get("used_context", {}))
        reservation_res = rm_act.get_res_data(date_start_server, date_end_server)

        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "Reservations": reservation_res,
            "start_time": date_start,
            "end_time": date_end,
        }


class ReportKot(models.AbstractModel):
    _name = "report.hotel_restaurant.report_hotel_order_kot"
    _description = "report.hotel_restaurant.report_hotel_order_kot"

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.restaurant.order"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "docs": folio_profile,
            "data": data,
        }


class FolioRestReport(models.AbstractModel):
    _name = "report.hotel_restaurant.report_rest_order"
    _description = "Folio Rest Report"

    def _convert_to_ist(self, utc_dt):
        user_tz = self._context.get("tz", "UTC")
        local_tz = pytz.timezone(user_tz)
        utc_tz = pytz.timezone("UTC")

        utc_dt = utc_tz.localize(utc_dt)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt

    def get_data(self, date_start, date_end):
        data = []
        tids = self.env["hotel.folio"].search(
            [
                ("checkin_date", ">=", date_start),
                ("checkout_date", "<=", date_end),
            ]
        )

        total = 0.0
        for record in tids:
            if record.hotel_reservation_orders_ids:

                total_amount = sum(
                    order.amount_total for order in record.hotel_reservation_orders_ids
                )
                total_order = len(record.hotel_reservation_orders_ids.ids)
                data.append(
                    {
                        "folio_name": record.name,
                        "customer_name": record.partner_id.name,
                        "checkin_date": fields.Datetime.to_string(record.checkin_date),
                        "checkout_date": fields.Datetime.to_string(
                            record.checkout_date
                        ),
                        "total_amount": total_amount,
                        "total_order": total_order,
                    }
                )

        data.append({"total": total})
        for reservation in data:
            if "checkin_date" in reservation:
                checkin_date_str = reservation["checkin_date"]
                checkin_date = datetime.strptime(checkin_date_str, "%Y-%m-%d %H:%M:%S")
                reservation["checkin_date"] = self._convert_to_ist(
                    checkin_date
                ).strftime("%m/%d/%Y %H:%M:%S")

            if "checkout_date" in reservation:
                checkout_date_str = reservation["checkout_date"]
                checkout_date = datetime.strptime(
                    checkout_date_str, "%Y-%m-%d %H:%M:%S"
                )
                reservation["checkout_date"] = self._convert_to_ist(
                    checkout_date
                ).strftime("%m/%d/%Y %H:%M:%S")
        return data

    def get_rest(self, date_start, date_end):
        data = []
        tids = self.env["hotel.folio"].search(
            [
                ("checkin_date", ">=", date_start),
                ("checkout_date", "<=", date_end),
            ]
        )
        for record in tids:
            if record.hotel_reservation_orders_ids:
                order_data = []
                for order in record.hotel_reservation_orders_ids:
                    order_data.append(
                        {
                            "order_no": order.order_number,
                            "order_date": fields.Datetime.to_string(order.order_date),
                            "state": order.state,
                            "table_nos_ids": len(order.table_nos_ids),
                            "order_len": len(order.order_list_ids),
                            "amount_total": order.amount_total,
                        }
                    )
                data.append(
                    {
                        "folio_name": record.name,
                        "customer_name": record.partner_id.name,
                        "order_data": order_data,
                    }
                )
        for reservation in data:
            for order in reservation["order_data"]:
                start_time_str = order["order_date"]
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                order["order_date"] = self._convert_to_ist(start_time).strftime(
                    "%m/%d/%Y %H:%M:%S"
                )
        return data

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.reservation.order"].browse(docids)
        date_start_str = data["form"].get("date_start")
        date_end_str = data["form"].get("date_end")

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
        date_start = fields.Datetime.to_string(date_start_ist)
        date_end = fields.Datetime.to_string(date_end_ist)

        date_start_minus_5_30 = date_start_ist - timedelta(hours=5, minutes=30)
        date_end_minus_5_30 = date_end_ist - timedelta(hours=5, minutes=30)

        date_start_server = fields.Datetime.to_string(date_start_minus_5_30)
        date_end_server = fields.Datetime.to_string(date_end_minus_5_30)

        rm_act = self.with_context(**data["form"].get("used_context", {}))

        get_data_res = rm_act.get_data(date_start_server, date_end_server)
        get_rest_res = rm_act.get_rest(date_start_server, date_end_server)

        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "GetData": get_data_res,
            "GetRest": get_rest_res,
            "start_time": date_start,
            "end_time": date_end,
        }


class FolioReservReport(models.AbstractModel):
    _name = "report.hotel_restaurant.report_reserv_order"
    _description = "report.hotel_restaurant.report_reserv_order"

    def _convert_to_ist(self, utc_dt):
        user_tz = self._context.get("tz", "UTC")
        local_tz = pytz.timezone(user_tz)
        utc_tz = pytz.timezone("UTC")

        utc_dt = utc_tz.localize(utc_dt)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt

    def get_data(self, date_start, date_end):
        data = []
        tids = self.env["hotel.folio"].search(
            [
                ("checkin_date", ">=", date_start),
                ("checkout_date", "<=", date_end),
            ]
        )
        total = 0.0
        for record in tids:
            if record.hotel_restaurant_orders_ids:
                total_amount = sum(
                    order.amount_total for order in record.hotel_restaurant_orders_ids
                )
                total_order = len(record.hotel_restaurant_orders_ids.ids)
                data.append(
                    {
                        "folio_name": record.name,
                        "customer_name": record.partner_id.name,
                        "checkin_date": fields.Datetime.to_string(record.checkin_date),
                        "checkout_date": fields.Datetime.to_string(
                            record.checkout_date
                        ),
                        "total_amount": total_amount,
                        "total_order": total_order,
                    }
                )
        for reservation in data:
            if "checkin_date" in reservation:
                checkin_date_str = reservation["checkin_date"]
                checkin_date = datetime.strptime(checkin_date_str, "%Y-%m-%d %H:%M:%S")
                reservation["checkin_date"] = self._convert_to_ist(
                    checkin_date
                ).strftime("%m/%d/%Y %H:%M:%S")

            if "checkout_date" in reservation:
                checkout_date_str = reservation["checkout_date"]
                checkout_date = datetime.strptime(
                    checkout_date_str, "%Y-%m-%d %H:%M:%S"
                )
                reservation["checkout_date"] = self._convert_to_ist(
                    checkout_date
                ).strftime("%m/%d/%Y %H:%M:%S")
        data.append({"total": total})
        return data

    def get_reserv(self, date_start, date_end):
        data = []
        tids = self.env["hotel.folio"].search(
            [
                ("checkin_date", ">=", date_start),
                ("checkout_date", "<=", date_end),
            ]
        )
        for record in tids:
            if record.hotel_restaurant_orders_ids:
                order_data = []
                for order in record.hotel_restaurant_orders_ids:
                    order_date = order.o_date
                    # order_date = (fields.Datetime.to_string(record.order_date),)
                    order_data.append(
                        {
                            "order_no": order.order_no,
                            "order_date": order_date,
                            "state": order.state,
                            "room_id": order.room_id.name,
                            "table_nos_ids": len(order.table_nos_ids),
                            "amount_total": order.amount_total,
                        }
                    )
                data.append(
                    {
                        "folio_name": record.name,
                        "customer_name": record.partner_id.name,
                        "order_data": order_data,
                    }
                )
        for reservation in data:
            for order in reservation["order_data"]:
                start_time_str = order["order_date"]
                if isinstance(start_time_str, datetime):
                    start_time_str = fields.Datetime.to_string(start_time_str)
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                order["order_date"] = self._convert_to_ist(start_time).strftime(
                    "%m/%d/%Y %H:%M:%S"
                )

        return data

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.restaurant.order"].browse(docids)
        date_start_str = data["form"].get("date_start")
        date_end_str = data["form"].get("date_end")

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
        date_start = fields.Datetime.to_string(date_start_ist)
        date_end = fields.Datetime.to_string(date_end_ist)

        date_start_minus_5_30 = date_start_ist - timedelta(hours=5, minutes=30)
        date_end_minus_5_30 = date_end_ist - timedelta(hours=5, minutes=30)

        date_start_server = fields.Datetime.to_string(date_start_minus_5_30)
        date_end_server = fields.Datetime.to_string(date_end_minus_5_30)

        rm_act = self.with_context(**data["form"].get("used_context", {}))

        get_data_res = rm_act.get_data(date_start_server, date_end_server)
        get_reserv_res = rm_act.get_reserv(date_start_server, date_end_server)

        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "GetData": get_data_res,
            "GetReserv": get_reserv_res,
            "start_time": date_start,
            "end_time": date_end,
        }
