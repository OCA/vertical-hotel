## 20.0.1.0.0

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`, no
  `report_file` on the reports, Owl 3 room summary. No longer depends on
  `website_sale` (it was only used by the demo pricelist).
- A reservation with several rooms now creates **one** folio with all its
  rooms (it created one folio per reservation line, billing rooms twice).
- Billable days follow the folio line rule: a 2-night stay checked in and
  out at the same time is 2 days, not 3.
- Draft and confirmed reservations can be cancelled from the form; a
  reservation with a folio cannot be cancelled (cancel the folio instead).
  Each button checks the state on the server.
- Rooms become occupied when the stay starts, not when the reservation is
  confirmed. The room status job only changes the rooms whose status
  changes and no longer fails when a room is on a reservation and a folio.
- Availability is the same everywhere: a room is taken by a confirmed
  reservation or a folio overlapping the stay; a stay ending when the next
  one starts does not block it. Confirming checks folios too, the room
  list of a reservation line only offers free rooms, and the folio room
  list leaves out the rooms of confirmed reservations.
- Reports: the period start was ignored and "From/To" printed empty; the
  Reservation List shows the stays overlapping the period, Max Room Used is
  sorted by use.
- New Reservation Summary: a free day opens a quick reservation for that
  room and day, a booked day opens its reservation or folio; also for hotel
  users. The grid shows at most 93 days.
- The 24 hour reminder email is sent (the scheduled job never found any
  reservation). Duplicating a reservation works again.
- Removed the unused "Make Folios" wizard.
- Upgrade: saved reservation summaries are deleted (the grid is computed).
