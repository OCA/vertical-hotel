A single, real-time screen for the receptionist, built on the
vertical-hotel data model (`vertical_hotel`, `hotel_reservation`,
`hotel_housekeeping`). No new master data or workflow is introduced; every
figure is read live from existing records:

- Occupancy right now (occupied / available rooms)
- Rooms ready to sell, split from rooms needing housekeeping and rooms
  whose last housekeeping predates the last check-out (not confirmed since)
- In-house guest count
- What is still left this shift: arrivals not yet in, departures not yet
  out, and departures already overdue
- Same-day turnovers, with the housekeeping deadline per room
- Today's arrivals and departures, with the balance due on departures
- Folios checking out today with something still to pay
- Restaurant orders not yet charged to a folio that leaves today (only
  when `hotel_restaurant` is installed)
- Confirmed reservations that never became a folio
- Quick lookup by guest name, room number or folio number

Every figure is a drill-down: clicking a tile opens the records it was
counted from, and the arrival / departure rows open their folio.
