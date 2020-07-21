# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.fields import Datetime


class HotelReservationLine(models.Model):
    _inherit = "hotel_reservation.line"

    def format_date(self, dt):
        """dt: string"""
        local_timestamp = Datetime.context_timestamp(
            self, Datetime.from_string(dt)
        )
        return local_timestamp.strftime("%H:%M")

    def format_departure_arrival_status(self):
        lines = self.sorted(lambda r: r.checkin)
        checkout = lines[0].checkout
        checkin = lines[1].checkin

        return _("%s D/A %s") % (
            self.format_date(checkout),
            self.format_date(checkin),
        )

    @api.multi
    def get_room_summary_cell_text(self, day):
        if len(self) > 2:
            raise ValidationError(
                _(
                    "Data inconsistency, contact your system administrator. "
                    "Can't have more than two reservation for a day."
                )
            )
        elif len(self) == 2:
            return self.format_departure_arrival_status()
        elif len(self) == 0:
            return _("")
        elif Datetime.from_string(self.checkin).date() == day:
            return _("A %s") % self.format_date(self.checkin)
        elif Datetime.from_string(self.checkout).date() == day:
            return _("%s D") % self.format_date(self.checkout)
        else:
            return self.line_id.partner_id.name
