# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ActivityReport(models.AbstractModel):

    _name = "report.hotel_housekeeping.housekeeping_report"
    _description = "Hotel Housekeeping Report"

    def get_room_activity_detail(self, date_start, date_end, room_id):
        activity_detail = []
        house_keep_act_obj = self.env["hotel.housekeeping.activities"]

        activity_line_ids = house_keep_act_obj.search(
            [
                ("clean_start_time", ">=", date_start),
                ("clean_end_time", "<=", date_end),
                ("housekeeping_id.room_id", "=", room_id),
            ]
        )

        for activity in activity_line_ids:
            ss_date = activity.clean_start_time
            ee_date = activity.clean_end_time
            diff = ee_date - ss_date
            activity_detail.append(
                {
                    "current_date": activity.today_date,
                    "activity": (activity.activity_id.name or ""),
                    "login": (activity.housekeeper_id.name or ""),
                    "clean_start_time": activity.clean_start_time,
                    "clean_end_time": activity.clean_end_time,
                    "duration": diff,
                }
            )
        return activity_detail

    @api.model
    def _get_report_values(self, docids, data=None):
        active_model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        activity_doc = self.env["hotel.housekeeping.activities"].browse(docids)
        date_start = data["form"].get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],
        )
        room_id = data["form"].get("room_id")[0]
        return {
            "doc_ids": docids,
            "doc_model": active_model,
            "data": data["form"],
            "docs": activity_doc,
            "time": time,
            "activity_detail": self.get_room_activity_detail(
                date_start, date_end, room_id
            ),
        }
