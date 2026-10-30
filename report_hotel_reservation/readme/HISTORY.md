## 20.0.1.0.0

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`.
- "States By Reservation" becomes *Reservation Analysis*. It grouped by
  reservation number, so every line was one reservation with a count of 1.
  Now there is one line per reserved room with the guest, room, room type,
  check-in / check-out and room nights; measures room nights,
  reservations, adults, children and guests; pivot by check-in month and
  room type, graph by month and state.
- Users only see the reservations of their companies (the report had no
  company).
- Cancel / not cancelled filters and group-bys; cancelled reservations are
  hidden by default.
