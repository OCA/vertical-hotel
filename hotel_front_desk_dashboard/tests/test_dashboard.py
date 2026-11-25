# Copyright (C) 2026-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import TransactionCase, new_test_user, tagged

TILES = (
    "occupancy",
    "rooms_ready",
    "rooms_not_ready",
    "rooms_stale",
    "rooms_unknown",
    "in_house",
    "unassigned_reservations",
    "unpaid_departures",
    "restaurant_charges",
    "turnovers",
    "arrivals",
    "departures",
)


@tagged("post_install", "-at_install")
class TestFrontDeskDashboard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Dashboard = cls.env["hotel.dashboard"]
        cls.partner = cls.env["res.partner"].create({"name": "Desk Guest"})
        cls.partner2 = cls.env["res.partner"].create({"name": "Desk Arriving"})
        room_type = cls.env["hotel.room.type"].create({"name": "Desk Type"})
        cls.rooms = cls.env["hotel.room"].create(
            [
                {"name": f"DK-{n}", "capacity": 2, "room_categ_id": room_type.id}
                for n in range(1, 6)
            ]
        )
        cls.hotel_user = new_test_user(
            cls.env,
            login="desk_user",
            groups="base.group_user,vertical_hotel.group_hotel_user",
        )

    def setUp(self):
        super().setUp()
        _day_start, day_end = self.Dashboard._get_today_range_utc()
        self.now = fields.Datetime.now().replace(microsecond=0)
        if self.now + timedelta(minutes=30) > fields.Datetime.to_datetime(day_end):
            self.skipTest("too close to midnight for same-day stays")

    def _folio(self, room, start_min, end_min, partner=None, confirm=True):
        checkin = self.now + timedelta(minutes=start_min)
        checkout = self.now + timedelta(minutes=end_min)
        folio = self.env["hotel.folio"].create(
            {
                "partner_id": (partner or self.partner).id,
                "checkin_date": checkin,
                "checkout_date": checkout,
                "room_line_ids": [
                    Command.create(
                        {
                            "product_id": room.product_id.id,
                            "checkin_date": checkin,
                            "checkout_date": checkout,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )
        if confirm:
            folio.action_confirm()
        return folio

    def _job(self, room, done=True):
        job = self.env["hotel.housekeeping"].create(
            {
                "room_id": room.id,
                "clean_type": "checkout",
                "inspector_id": self.env.uid,
            }
        )
        if done:
            job.room_clean()
            job.quality = "good"
            job.room_done()
        return job

    def _past_stay(self, room, hours_ago):
        """A stay that ended ``hours_ago`` (folio lines refuse past dates)."""
        folio = self._folio(room, 60 * 24 * 3, 60 * 24 * 4)
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE folio_room_line SET check_in = %s, check_out = %s "
            "WHERE folio_id = %s",
            (
                self.now - timedelta(hours=hours_ago + 24),
                self.now - timedelta(hours=hours_ago),
                folio.id,
            ),
        )
        self.env.invalidate_all()
        # confirming a folio marks its rooms occupied at once; the room
        # status job of hotel_reservation puts them back by the clock
        self.env["hotel.room"].cron_room_line()
        return folio

    # Figures

    def test_dashboard_data(self):
        departing = self._folio(self.rooms[0], 2, 10)
        arriving = self._folio(self.rooms[0], 15, 60 * 24, partner=self.partner2)
        self._folio(self.rooms[1], 5, 60 * 24)
        self._job(self.rooms[2])  # ready
        self._job(self.rooms[3], done=False)  # needs housekeeping
        data = self.Dashboard.get_dashboard_data()
        self.assertEqual(len(data["arrivals"]), 3)
        self.assertEqual(len(data["departures"]), 1)
        self.assertEqual(data["departures"][0]["folio_id"], departing.id)
        self.assertGreater(data["departures"][0]["balance"], 0)
        turnover = data["turnovers"][0]
        self.assertEqual(turnover["room_id"], self.rooms[0].id)
        self.assertEqual(turnover["in_folio_id"], arriving.id)
        rooms = data["rooms"]
        self.assertEqual(rooms["total"], rooms["occupied"] + rooms["available"])
        readiness = self.Dashboard._get_room_readiness()
        self.assertIn(self.rooms[2], readiness["ready"])
        self.assertIn(self.rooms[3], readiness["not_ready"])
        self.assertIn(self.rooms[4], readiness["unknown"])

    def test_cleaned_not_inspected_is_not_ready(self):
        job = self._job(self.rooms[2], done=False)
        job.room_clean()
        readiness = self.Dashboard._get_room_readiness()
        self.assertIn(self.rooms[2], readiness["not_ready"])
        self.assertEqual(self.rooms[2].housekeeping_state, "to_inspect")

    def test_stale_clean(self):
        job = self._job(self.rooms[2])
        job.inspect_date_time = self.now - timedelta(hours=10)
        self._past_stay(self.rooms[2], hours_ago=2)
        readiness = self.Dashboard._get_room_readiness()
        self.assertIn(self.rooms[2], readiness["stale"])
        # inspected again after the guest left: ready
        self._job(self.rooms[2])
        readiness = self.Dashboard._get_room_readiness()
        self.assertIn(self.rooms[2], readiness["ready"])

    def test_unpaid_departures(self):
        folio = self._folio(self.rooms[0], 2, 10)
        data = self.Dashboard.get_dashboard_data()
        self.assertEqual(data["unpaid_departures"]["count"], 1)
        self.assertAlmostEqual(
            data["unpaid_departures"]["amount"], folio.amount_total, places=2
        )
        invoice = folio.order_id._create_invoices()
        invoice.action_post()
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({"amount": invoice.amount_total / 2})._create_payments()
        data = self.Dashboard.get_dashboard_data()
        # invoiced but half paid: still owed
        self.assertEqual(data["unpaid_departures"]["count"], 1)
        self.assertAlmostEqual(
            data["unpaid_departures"]["amount"], invoice.amount_residual, places=2
        )
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({})._create_payments()
        data = self.Dashboard.get_dashboard_data()
        self.assertEqual(data["unpaid_departures"]["count"], 0)

    def test_unassigned_reservations(self):
        pricelist = self.env["product.pricelist"].create({"name": "Desk PL"})
        checkin = self.now + timedelta(days=3)
        reservation = self.env["hotel.reservation"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_order_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "pricelist_id": pricelist.id,
                "checkin": checkin,
                "checkout": checkin + timedelta(days=1),
                "adults": 1,
                "reservation_line": [
                    Command.create({"reserve": [Command.set(self.rooms[4].ids)]})
                ],
            }
        )
        reservation.confirmed_reservation()
        self.assertIn(reservation, self.Dashboard._get_unassigned_reservations())
        reservation.create_folio()
        self.assertNotIn(reservation, self.Dashboard._get_unassigned_reservations())

    def test_restaurant_charges(self):
        if "hotel.restaurant.order" not in self.env:
            self.skipTest("hotel_restaurant is not installed")
        folio = self._folio(self.rooms[0], 2, 10)
        table = self.env["hotel.restaurant.tables"].create({"name": "DK-T"})
        dish = self.env["hotel.menucard"].create(
            {"name": "Desk Dish", "list_price": 30}
        )

        def order():
            return self.env["hotel.restaurant.order"].create(
                {
                    "customer_id": self.partner.id,
                    "folio_id": folio.id,
                    "is_folio": True,
                    "table_nos_ids": [Command.set(table.ids)],
                    "order_list_ids": [
                        Command.create(
                            {"menucard_id": dish.id, "item_qty": 1, "item_rate": 30}
                        )
                    ],
                }
            )

        pending, charged = order(), order()
        charged.generate_kot()
        charged.done_order_kot()
        data = self.Dashboard.get_dashboard_data()
        # the closed order is already on the folio
        self.assertEqual(data["restaurant_charges"], {"count": 1, "amount": 30.0})
        self.assertEqual(
            self.Dashboard._get_open_restaurant_orders(
                *self.Dashboard._get_today_range_utc()
            ),
            pending,
        )

    # Drill-downs and search, for a hotel user too

    def _check_tiles(self, dashboard):
        for tile in TILES:
            action = dashboard.get_tile_action(tile)
            self.assertEqual(action["type"], "ir.actions.act_window", tile)
            records = dashboard.env[action["res_model"]].search(action["domain"])
            records.read(["display_name"])
            dashboard.env[action["res_model"]].get_views([(False, "list")])
        with self.assertRaises(UserError):
            dashboard.get_tile_action("no_such_tile")

    def test_tiles_and_search(self):
        folio = self._folio(self.rooms[0], 2, 10)
        self._folio(self.rooms[1], 5, 60 * 24, partner=self.partner2)
        self._job(self.rooms[2])
        for dashboard in (self.Dashboard, self.Dashboard.with_user(self.hotel_user)):
            dashboard.get_dashboard_data()
            self._check_tiles(dashboard)
            self.assertEqual(dashboard.search_guests(""), [])
            by_guest = dashboard.search_guests("Desk Guest")
            self.assertEqual([hit["folio_id"] for hit in by_guest], folio.ids)
            by_room = dashboard.search_guests("DK-1")
            self.assertIn(folio.id, [hit["folio_id"] for hit in by_room])
            by_folio = dashboard.search_guests(folio.name)
            self.assertIn(folio.id, [hit["folio_id"] for hit in by_folio])

    def test_empty_hotel(self):
        """No crash when there is nothing to show."""
        self.env["hotel.room"].search([]).write({"active": False})
        data = self.Dashboard.get_dashboard_data()
        self.assertEqual(data["rooms"]["total"], 0)
        self.assertEqual(data["rooms"]["occupancy_pct"], 0.0)
        self._check_tiles(self.Dashboard)
