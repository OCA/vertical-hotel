# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HotelRestaurantReport(models.AbstractModel):
    _name = "report.hotel_restaurant.report_res_table"
    _description = "report.hotel_restaurant.report_res_table"

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
                    "start_date": fields.Datetime.to_string(record.start_date),
                    "end_date": fields.Datetime.to_string(record.end_date),
                }
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
        date_start = data.get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=1, day=1, days=1))[:10],
        )
        rm_act = self.with_context(data["form"].get("used_context", {}))
        reservation_res = rm_act.get_res_data(date_start, date_end)
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "Reservations": reservation_res,
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
        return data

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.reservation.order"].browse(docids)
        date_start = data["form"].get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=1, day=1, days=1))[:10],
        )
        rm_act = self.with_context(data["form"].get("used_context", {}))
        get_data_res = rm_act.get_data(date_start, date_end)
        get_rest_res = rm_act.get_rest(date_start, date_end)
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "GetData": get_data_res,
            "GetRest": get_rest_res,
        }


class FolioReservReport(models.AbstractModel):
    _name = "report.hotel_restaurant.report_reserv_order"
    _description = "report.hotel_restaurant.report_reserv_order"

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
        return data

    @api.model
    def _get_report_values(self, docids, data):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.restaurant.order"].browse(docids)
        date_start = data.get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=1, day=1, days=1))[:10],
        )
        rm_act = self.with_context(data["form"].get("used_context", {}))
        get_data_res = rm_act.get_data(date_start, date_end)
        get_reserv_res = rm_act.get_reserv(date_start, date_end)
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "GetData": get_data_res,
            "GetReserv": get_reserv_res,
        }
