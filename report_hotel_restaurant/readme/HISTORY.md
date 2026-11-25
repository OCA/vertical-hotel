## 20.0.1.0.0

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`.
- "Status By Restaurant" becomes *Restaurant Sales Analysis*. It grouped
  table bookings by their number, so every line was one booking with a
  count of 1, under a measure labelled "Reservation Order No". Now there is
  one line per food item ordered, for table orders and booking orders, with
  date, order, customer, waiter, folio, food item and category; measures
  quantity, amount and orders (each order counted once, also when grouped
  by food item or category); pivot by month and food item category, graph
  by month.
- Company of the folio the order is charged to, with a multi-company rule;
  orders not charged to a folio have no company and are seen by all
  companies.
- Filters by order kind, hotel guests and state (cancelled orders hidden by
  default), and group-bys.
