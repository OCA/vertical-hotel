# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ActivityReport(models.AbstractModel):
    _name = "report.hotel_housekeeping.housekeeping_report"
    _description = "Hotel Housekeeping Report"

    def get_room_activity_detail(self, date_start, date_end, room_id):
        """Activity lines of a room cleaned between the two datetimes."""
        return self.env["hotel.housekeeping.activities"].search(
            [
                ("clean_start_time", ">=", date_start),
                ("clean_end_time", "<=", date_end),
                ("housekeeping_id.room_id", "=", room_id),
            ],
            order="clean_start_time, id",
        )

    @api.model
    def _get_sections(self, docids, data):
        """One section per room: the room, the period and its activity lines.

        From the wizard (``data["form"]``): one room over a period.
        From the Print menu of housekeeping jobs: the lines of those jobs,
        one section per room, without a period."""
        form = (data or {}).get("form")
        if form:
            room = self.env["hotel.room"].browse(form["room_id"])
            date_start = fields.Datetime.to_datetime(form["date_start"])
            date_end = fields.Datetime.to_datetime(form["date_end"])
            lines = self.get_room_activity_detail(date_start, date_end, room.id)
            return [
                {
                    "room": room,
                    "date_start": date_start,
                    "date_end": date_end,
                    "lines": lines,
                }
            ]
        jobs = self.env["hotel.housekeeping"].browse(docids)
        return [
            {
                "room": room,
                "date_start": False,
                "date_end": False,
                "lines": jobs.filtered(
                    lambda j, r=room: j.room_id == r
                ).activity_line_ids.sorted(
                    lambda line: (line.clean_start_time, line.id)
                ),
            }
            for room in jobs.room_id
        ]

    @api.model
    def _get_report_values(self, docids, data=None):
        sections = self._get_sections(docids, data)
        return {
            "doc_ids": docids,
            "doc_model": "hotel.housekeeping",
            "docs": self.env["hotel.housekeeping"].browse(
                docids if not (data or {}).get("form") else []
            ),
            "data": data,
            "sections": sections,
            "duration_hours": lambda line: (
                (line.clean_end_time - line.clean_start_time).total_seconds() / 3600
            ),
        }
