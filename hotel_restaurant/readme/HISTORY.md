## 20.0.1.0.0

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`, no
  `report_file` on the reports. Depends on `vertical_hotel` only: the
  `point_of_sale` dependency was only used by the demo data.
- Reports printed empty on Odoo 20 (`t-esc`): the kitchen order ticket,
  both customer bills, the table reservation list and the folio restaurant
  reports now show their data, with amounts in the company currency. The
  report period start was ignored. The ticket and the bills are in the
  *Print* menu of the orders.
- An order is charged to the guest folio **once**: closing it again is
  refused, and a closed order cannot be cancelled (remove the charge on the
  folio first).
- A cancelled table booking no longer blocks its tables; a booking ending
  when the next one starts does not block it either.
- *Update KOT* sends only the lines added since the last ticket, on one new
  ticket (it created a ticket per line each time).
- Each button checks the state of the booking or order on the server.
- "Parent / Child" search on food item types; a loop in food item types is
  refused instead of freezing the server.
- The room of a booking or order can only be a hotel room.
