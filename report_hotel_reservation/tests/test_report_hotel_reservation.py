# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time, timedelta

from odoo import fields
from odoo.fields import Command
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestReservationAnalysis(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env["res.partner"].create({"name": "Analysis Guest"})
        cls.pricelist = cls.env["product.pricelist"].create({"name": "Analysis PL"})
        cls.single = cls.env["hotel.room.type"].create({"name": "Analysis Single"})
        cls.double = cls.env["hotel.room.type"].create({"name": "Analysis Double"})
        cls.room1 = cls._room("AN-101", cls.single)
        cls.room2 = cls._room("AN-201", cls.double)
        cls.base = datetime.combine(fields.Date.today() + timedelta(days=10), time(12))
        cls.Report = cls.env["report.hotel.reservation.status"]

    @classmethod
    def _room(cls, name, room_type):
        return cls.env["hotel.room"].create(
            {"name": name, "capacity": 4, "room_categ_id": room_type.id}
        )

    def _reservation(self, lines, nights=3, **vals):
        values = {
            "partner_id": self.partner.id,
            "partner_invoice_id": self.partner.id,
            "partner_order_id": self.partner.id,
            "partner_shipping_id": self.partner.id,
            "pricelist_id": self.pricelist.id,
            "checkin": self.base,
            "checkout": self.base + timedelta(days=nights),
            # main guest + one adult + one child: 2 adults, 1 child
            "guest_ids": [
                Command.create({"name": "Analysis Adult", "guest_type": "adult"}),
                Command.create({"name": "Analysis Child", "guest_type": "child"}),
            ],
            "reservation_line": [
                Command.create(
                    {
                        "categ_id": room.room_categ_id.id,
                        "reserve": [Command.set(room.ids)],
                    }
                )
                for room in lines
            ],
        }
        values.update(vals)
        reservation = self.env["hotel.reservation"].create(values)
        self.env.flush_all()
        return reservation

    def _rows(self, reservations):
        return self.Report.search([("reservation_id", "in", reservations.ids)])

    def test_one_row_per_room(self):
        reservation = self._reservation([self.room1, self.room2])
        rows = self._rows(reservation)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows.room_id, self.room1 | self.room2)
        self.assertEqual(rows.room_type_id, self.single | self.double)
        self.assertEqual(set(rows.mapped("room_nights")), {3})
        # reservation counters only once, whatever the number of rooms
        self.assertEqual(sum(rows.mapped("no_of_reservation")), 1)
        self.assertEqual(sum(rows.mapped("guests")), 3)
        self.assertEqual(sum(rows.mapped("adults")), 2)
        self.assertEqual(sum(rows.mapped("children")), 1)
        self.assertEqual(
            set(rows.mapped("reservation_no")), {reservation.reservation_no}
        )

    def test_measures_by_room_type(self):
        first = self._reservation([self.room1], nights=2)
        second = self._reservation(
            [self.room1, self.room2],
            nights=1,
            checkin=self.base + timedelta(days=5),
            checkout=self.base + timedelta(days=6),
        )
        groups = {
            room_type: (nights, count)
            for room_type, nights, count in self.Report._read_group(
                [("reservation_id", "in", (first | second).ids)],
                ["room_type_id"],
                ["room_nights:sum", "no_of_reservation:sum"],
            )
        }
        self.assertEqual(groups[self.single], (3, 2))
        self.assertEqual(groups[self.double][0], 1)

    def test_states_and_same_day_stay(self):
        cancelled = self._reservation([self.room1])
        cancelled.cancel_reservation()
        same_day = self._reservation(
            [self.room2], checkout=self.base + timedelta(hours=3)
        )
        self.env.flush_all()
        self.assertEqual(self._rows(cancelled).state, "cancel")
        # a stay without a night still counts one room night
        self.assertEqual(self._rows(same_day).room_nights, 1)
        not_cancelled = self.Report.search(
            [
                ("reservation_id", "in", (cancelled | same_day).ids),
                ("state", "!=", "cancel"),
            ]
        )
        self.assertEqual(not_cancelled.reservation_id, same_day)

    def test_multi_company(self):
        reservation = self._reservation([self.room1])
        other_company = self.env["res.company"].create({"name": "Other Hotel"})
        user = new_test_user(
            self.env,
            login="analysis_user",
            groups="base.group_user,vertical_hotel.group_hotel_user",
            company_id=other_company.id,
            company_ids=[Command.set(other_company.ids)],
        )
        self.assertFalse(
            self.Report.with_user(user).search(
                [("reservation_id", "=", reservation.id)]
            )
        )
        own_user = new_test_user(
            self.env,
            login="analysis_user_own",
            groups="base.group_user,vertical_hotel.group_hotel_user",
        )
        self.assertTrue(
            self.Report.with_user(own_user).search(
                [("reservation_id", "=", reservation.id)]
            )
        )
