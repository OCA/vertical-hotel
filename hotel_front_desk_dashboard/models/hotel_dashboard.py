# Copyright (C) 2026-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.exceptions import UserError

# Folio states (mirrors sale.order state, since hotel.folio _inherits it)
# that represent a real, active stay/booking.
ACTIVE_FOLIO_STATES = ("sale", "done")

# hotel.room.housekeeping_state (hotel_housekeeping) values: "ready" means
# inspected and done; the others still need housekeeping.
READY_HOUSEKEEPING_STATES = ("ready",)
NOT_READY_HOUSEKEEPING_STATES = ("needs_cleaning", "to_inspect")

# hotel.restaurant.order states whose charges are not on the folio yet:
# closing an order ("done") adds it to the folio, a cancelled one owes nothing.
OPEN_RESTAURANT_ORDER_STATES = ("draft", "order")


class HotelDashboard(models.AbstractModel):
    _name = "hotel.dashboard"
    _description = "Hotel Front Desk Dashboard - Data Provider"

    @api.model
    def _get_today_range_utc(self):
        """Return (day_start, day_end) as UTC datetime strings for "today"
        in the current user's timezone, so shift-based filtering matches
        what the receptionist sees on the wall clock."""
        tz = ZoneInfo(self.env.user.tz or self.env.company.partner_id.tz or "UTC")
        now_utc = fields.Datetime.now().replace(tzinfo=UTC)
        today_local = now_utc.astimezone(tz).date()
        day_start_local = datetime.combine(today_local, time.min, tzinfo=tz)
        day_end_local = datetime.combine(today_local, time.max, tzinfo=tz)
        return (
            fields.Datetime.to_string(
                day_start_local.astimezone(UTC).replace(tzinfo=None)
            ),
            fields.Datetime.to_string(
                day_end_local.astimezone(UTC).replace(tzinfo=None)
            ),
        )

    @api.model
    def _get_last_checkout_by_room(self):
        """Latest past check-out datetime per room, across active folios.

        Used to decide whether a housekeeping record is still meaningful:
        a "clean" logged before the last guest left says nothing about the
        room's current state."""
        self.env.cr.execute(
            """
            select frl.room_id, max(frl.check_out)
            from folio_room_line frl
            join hotel_folio hf on hf.id = frl.folio_id
            join sale_order so on so.id = hf.order_id
            where so.state in %s
              and frl.check_out <= now() at time zone 'UTC'
            group by frl.room_id
            """,
            (ACTIVE_FOLIO_STATES,),
        )
        return dict(self.env.cr.fetchall())

    @api.model
    def _get_room_readiness(self):
        """Bucket the *available* rooms by how sellable they actually are,
        based on the room's housekeeping status (``hotel_housekeeping``: the
        latest non-cancelled housekeeping job of the room):

        * ``ready``      - the job is done (inspected), *after* the last
          guest left, so the room really has been turned over.
        * ``not_ready``  - the room needs cleaning or awaits inspection.
        * ``stale``      - the job is done, but that predates
          the last check-out. Nobody has confirmed the room since a guest
          was in it, so it is not safe to sell as-is. Kept separate from
          ``not_ready`` because the room may well be fine - it just has not
          been checked - and that is a different job for the receptionist.
        * ``unknown``    - no housekeeping record at all.

        Returns a dict of ``hotel.room`` recordsets, so the tile figures
        and the drill-down actions work off the exact same rooms."""
        Room = self.env["hotel.room"]
        available = Room.search([("status", "=", "available")])
        last_checkout_by_room = self._get_last_checkout_by_room()

        ready = not_ready = stale = unknown = Room
        for room in available:
            state = room.housekeeping_state
            if state in READY_HOUSEKEEPING_STATES:
                # the job that made the room ready, as hotel_housekeeping
                # picks it: latest non-cancelled one
                job = room.housekeeping_ids.filtered(
                    lambda job: job.state != "cancel"
                ).sorted(lambda job: (job.current_date, job.id), reverse=True)[:1]
                last_checkout = last_checkout_by_room.get(room.id)
                if self._is_clean_stale(
                    job.current_date, job.inspect_date_time, last_checkout
                ):
                    stale |= room
                else:
                    ready |= room
            elif state in NOT_READY_HOUSEKEEPING_STATES:
                not_ready |= room
            else:
                unknown |= room
        return {
            "ready": ready,
            "not_ready": not_ready,
            "stale": stale,
            "unknown": unknown,
        }

    @api.model
    def _is_clean_stale(self, hk_date, inspect_dt, last_checkout):
        """Was this housekeeping record logged before the last guest left?

        ``current_date`` is a Date, so it is compared on day granularity;
        when the housekeeping record carries an inspection timestamp we
        use that instead for an exact comparison."""
        if not last_checkout:
            return False
        if inspect_dt:
            return inspect_dt < last_checkout
        if not hk_date:
            return False
        return hk_date < last_checkout.date()

    @api.model
    def _get_occupied_rooms(self):
        return self.env["hotel.room"].search([("status", "=", "occupied")])

    @api.model
    def _get_room_status_summary(self, readiness=None):
        total = self.env["hotel.room"].search_count([])
        occupied = len(self._get_occupied_rooms())
        if readiness is None:
            readiness = self._get_room_readiness()
        return {
            "total": total,
            "occupied": occupied,
            "available": total - occupied,
            "occupancy_pct": round((occupied / total) * 100, 1) if total else 0.0,
            "ready": len(readiness["ready"]),
            "not_ready": len(readiness["not_ready"]),
            "stale": len(readiness["stale"]),
            "unknown": len(readiness["unknown"]),
        }

    @api.model
    def _get_folio_balance(self, folio):
        """Amount still owed on a folio: the total, less whatever has
        already been paid on its posted invoices."""
        invoices = folio.order_id.invoice_ids.filtered(
            lambda inv: inv.state == "posted" and inv.move_type == "out_invoice"
        )
        paid = sum(inv.amount_total - inv.amount_residual for inv in invoices)
        return folio.amount_total - paid

    @api.model
    def _serialize_room_line(self, line, kind):
        room = line.room_id
        folio = line.folio_id
        raw_dt = line.check_in if kind == "arrival" else line.check_out
        local_dt = fields.Datetime.context_timestamp(self, raw_dt)
        # "Done" is inferred from the room's live status, since neither
        # folio.room.line nor hotel.folio stores an explicit checked-in /
        # checked-out flag: occupied means arrived, available means
        # departed (or not yet arrived, for a future arrival row).
        expected_status = "occupied" if kind == "arrival" else "available"
        done = room.status == expected_status
        overdue = False
        if kind == "departure" and not done:
            overdue = raw_dt < fields.Datetime.now()
        values = {
            "folio": folio.name,
            "folio_id": folio.id,
            "guest": folio.order_id.partner_id.name or "",
            "room": room.name,
            "room_id": room.id,
            "time": local_dt.strftime("%H:%M"),
            "done": done,
            "overdue": overdue,
        }
        if kind == "departure":
            values["balance"] = round(self._get_folio_balance(folio), 2)
        return values

    @api.model
    def _get_arrival_lines(self, day_start, day_end):
        return self.env["folio.room.line"].search(
            [
                ("check_in", ">=", day_start),
                ("check_in", "<=", day_end),
                ("folio_id.order_id.state", "in", ACTIVE_FOLIO_STATES),
            ],
            order="check_in",
        )

    @api.model
    def _get_departure_lines(self, day_start, day_end):
        return self.env["folio.room.line"].search(
            [
                ("check_out", ">=", day_start),
                ("check_out", "<=", day_end),
                ("folio_id.order_id.state", "in", ACTIVE_FOLIO_STATES),
            ],
            order="check_out",
        )

    @api.model
    def _get_turnovers(self, day_start, day_end, readiness=None):
        """Rooms a guest leaves and another guest enters on the same day.

        These are the rooms that can actually fail the shift: housekeeping
        has a hard deadline, and the dashboard should say so before the
        arriving guest is standing at the desk."""
        arrivals = self._get_arrival_lines(day_start, day_end)
        departures = self._get_departure_lines(day_start, day_end)
        arrivals_by_room = {}
        for line in arrivals:
            arrivals_by_room.setdefault(line.room_id.id, []).append(line)

        def next_arrival(dep):
            """The next guest of the room: another stay starting once this
            one ends (a stay checking in and out today is not its own
            turnover). Earliest wins: it sets the deadline."""
            return next(
                (
                    line
                    for line in arrivals_by_room.get(dep.room_id.id, [])
                    if line.folio_id != dep.folio_id and line.check_in >= dep.check_out
                ),
                None,
            )

        if readiness is None:
            readiness = self._get_room_readiness()
        ready_ids = set(readiness["ready"].ids)
        not_ready_ids = set(readiness["not_ready"].ids)
        stale_ids = set(readiness["stale"].ids)

        turnovers = []
        seen_rooms = set()
        for dep in departures:
            room = dep.room_id
            arrival = next_arrival(dep)
            if not arrival or room.id in seen_rooms:
                continue
            seen_rooms.add(room.id)
            if room.id in ready_ids:
                readiness_state = "ready"
            elif room.id in not_ready_ids:
                readiness_state = "not_ready"
            elif room.id in stale_ids:
                readiness_state = "stale"
            elif room.status == "occupied":
                # Departing guest has not physically left yet.
                readiness_state = "occupied"
            else:
                readiness_state = "unknown"
            turnovers.append(
                {
                    "room": room.name,
                    "room_id": room.id,
                    "out_guest": dep.folio_id.order_id.partner_id.name or "",
                    "out_time": fields.Datetime.context_timestamp(
                        self, dep.check_out
                    ).strftime("%H:%M"),
                    "in_guest": arrival.folio_id.order_id.partner_id.name or "",
                    "in_time": fields.Datetime.context_timestamp(
                        self, arrival.check_in
                    ).strftime("%H:%M"),
                    "in_folio_id": arrival.folio_id.id,
                    "readiness": readiness_state,
                }
            )
        # Tightest deadline first.
        turnovers.sort(key=lambda t: t["in_time"])
        return turnovers

    @api.model
    def _get_turnover_rooms(self, day_start, day_end):
        room_ids = [t["room_id"] for t in self._get_turnovers(day_start, day_end)]
        return self.env["hotel.room"].browse(room_ids)

    @api.model
    def _get_in_house_folios(self):
        now = fields.Datetime.now()
        return self.env["hotel.folio"].search(
            [
                ("checkin_date", "<=", now),
                ("checkout_date", ">=", now),
                ("state", "in", ACTIVE_FOLIO_STATES),
            ]
        )

    @api.model
    def _get_unpaid_departure_folios(self, day_start, day_end):
        """Folios leaving today with something still to pay (invoiced or
        not: an invoice that is not paid is still owed)."""
        departing = self.env["hotel.folio"].search(
            [
                ("checkout_date", ">=", day_start),
                ("checkout_date", "<=", day_end),
                ("state", "in", ACTIVE_FOLIO_STATES),
            ]
        )
        currency = self.env.company.currency_id
        return departing.filtered(
            lambda folio: (
                currency.compare_amounts(self._get_folio_balance(folio), 0) > 0
            )
        )

    @api.model
    def _get_unassigned_reservations(self):
        """Confirmed reservations that never became a folio - i.e. nobody
        has given the guest a room yet."""
        Reservation = self.env["hotel.reservation"]
        confirmed = Reservation.search([("state", "=", "confirm")])
        return confirmed.filtered(lambda res: not res.folio_id)

    @api.model
    def _get_open_restaurant_orders(self, day_start, day_end):
        """Restaurant charges sitting on a folio that checks out today.

        hotel_restaurant is not a dependency of this module, so this stays
        empty rather than failing when the module is not installed."""
        if "hotel.restaurant.order" not in self.env:
            return self.env["hotel.folio"].browse()
        departing = self.env["hotel.folio"].search(
            [
                ("checkout_date", ">=", day_start),
                ("checkout_date", "<=", day_end),
                ("state", "in", ACTIVE_FOLIO_STATES),
            ]
        )
        if not departing:
            return self.env["hotel.restaurant.order"].browse()
        return self.env["hotel.restaurant.order"].search(
            [
                ("folio_id", "in", departing.ids),
                ("state", "in", OPEN_RESTAURANT_ORDER_STATES),
            ]
        )

    @api.model
    def get_dashboard_data(self):
        """Single RPC entry point used by the OWL dashboard widget.
        Returns a plain, JSON-serialisable dict - no recordsets."""
        day_start, day_end = self._get_today_range_utc()
        # Computed once and threaded through: the tiles and the turnover
        # list must agree, and the housekeeping queries are not cheap.
        readiness = self._get_room_readiness()
        in_house = self._get_in_house_folios()
        unpaid = self._get_unpaid_departure_folios(day_start, day_end)
        arrivals = [
            self._serialize_room_line(line, "arrival")
            for line in self._get_arrival_lines(day_start, day_end)
        ]
        departures = [
            self._serialize_room_line(line, "departure")
            for line in self._get_departure_lines(day_start, day_end)
        ]
        turnovers = self._get_turnovers(day_start, day_end, readiness=readiness)
        restaurant_orders = self._get_open_restaurant_orders(day_start, day_end)
        return {
            "generated_at": fields.Datetime.context_timestamp(
                self, fields.Datetime.now()
            ).strftime("%H:%M"),
            "currency_id": self.env.company.currency_id.id,
            "rooms": self._get_room_status_summary(readiness=readiness),
            "in_house_guests": len(in_house.mapped("partner_id")),
            "in_house_stays": len(in_house),
            "arrivals": arrivals,
            "departures": departures,
            # What is actually left to do this shift, as opposed to what
            # the whole day contained.
            "arrivals_pending": sum(1 for line in arrivals if not line["done"]),
            "departures_pending": sum(1 for line in departures if not line["done"]),
            "departures_overdue": sum(1 for line in departures if line["overdue"]),
            "turnovers": turnovers,
            "turnovers_at_risk": sum(1 for t in turnovers if t["readiness"] != "ready"),
            "unassigned_reservations": len(self._get_unassigned_reservations()),
            "restaurant_charges": {
                "count": len(restaurant_orders),
                "amount": round(sum(restaurant_orders.mapped("amount_total")), 2),
            },
            "unpaid_departures": {
                "count": len(unpaid),
                "amount": round(
                    sum(self._get_folio_balance(folio) for folio in unpaid), 2
                ),
            },
        }

    @api.model
    def search_guests(self, query):
        """Quick front-desk lookup: match a guest name, folio number or
        room number and return the folios behind it."""
        query = (query or "").strip()
        if not query:
            return []
        folios = self.env["hotel.folio"].search(
            [
                ("state", "in", ACTIVE_FOLIO_STATES),
                "|",
                "|",
                ("order_id.partner_id.name", "ilike", query),
                ("name", "ilike", query),
                ("room_line_ids.product_id.name", "ilike", query),
            ],
            order="checkin_date desc",
            limit=10,
        )
        now = fields.Datetime.now()
        results = []
        for folio in folios:
            rooms = folio.room_line_ids.mapped("product_id.name")
            in_house = folio.checkin_date <= now <= folio.checkout_date
            results.append(
                {
                    "folio_id": folio.id,
                    "folio": folio.name,
                    "guest": folio.order_id.partner_id.name or "",
                    "rooms": ", ".join(r for r in rooms if r),
                    "checkin": fields.Datetime.context_timestamp(
                        self, folio.checkin_date
                    ).strftime("%d %b %H:%M"),
                    "checkout": fields.Datetime.context_timestamp(
                        self, folio.checkout_date
                    ).strftime("%d %b %H:%M"),
                    "in_house": in_house,
                }
            )
        return results

    @api.model
    def _get_tile_records(self, tile):
        """Map a dashboard tile key to (title, recordset), so clicking a
        figure opens exactly the records that figure was counted from."""
        if tile == "occupancy":
            return self.env._("Occupied Rooms"), self._get_occupied_rooms()
        if tile in ("rooms_ready", "rooms_not_ready", "rooms_stale", "rooms_unknown"):
            readiness = self._get_room_readiness()
            titles = {
                "rooms_ready": self.env._("Rooms Ready to Sell"),
                "rooms_not_ready": self.env._("Rooms Needing Housekeeping"),
                "rooms_stale": self.env._("Rooms Not Confirmed Since Last Check-out"),
                "rooms_unknown": self.env._("Rooms Without Housekeeping Records"),
            }
            keys = {
                "rooms_ready": "ready",
                "rooms_not_ready": "not_ready",
                "rooms_stale": "stale",
                "rooms_unknown": "unknown",
            }
            return titles[tile], readiness[keys[tile]]
        if tile == "in_house":
            return self.env._("In-house Stays"), self._get_in_house_folios()
        if tile == "unassigned_reservations":
            return (
                self.env._("Confirmed Reservations Without a Folio"),
                self._get_unassigned_reservations(),
            )

        day_start, day_end = self._get_today_range_utc()
        if tile == "unpaid_departures":
            return (
                self.env._("Unpaid Check-outs Today"),
                self._get_unpaid_departure_folios(day_start, day_end),
            )
        if tile == "restaurant_charges":
            return (
                self.env._("Restaurant Charges on Today's Check-outs"),
                self._get_open_restaurant_orders(day_start, day_end),
            )
        if tile == "turnovers":
            return (
                self.env._("Same-day Turnover Rooms"),
                self._get_turnover_rooms(day_start, day_end),
            )
        if tile == "arrivals":
            return (
                self.env._("Arrivals Today"),
                self._get_arrival_lines(day_start, day_end),
            )
        if tile == "departures":
            return (
                self.env._("Departures Today"),
                self._get_departure_lines(day_start, day_end),
            )
        raise UserError(self.env._("Unknown dashboard tile: %s", tile))

    @api.model
    def get_tile_action(self, tile):
        """Return the act_window that drills a tile down to its records."""
        name, records = self._get_tile_records(tile)
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": records._name,
            "views": [(False, "list"), (False, "form")],
            "domain": [("id", "in", records.ids)],
            "target": "current",
            "context": {"create": False},
        }
