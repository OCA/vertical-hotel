## Bring the data of an Odoo 19 database

The hotel data of an Odoo 19 database (module `hotel` or `vertical_hotel`)
can be copied into a new Odoo 20 database. The Odoo 19 database is only read,
never changed.

Open *Hotel Management > Configuration > Import from Odoo 19* (Settings /
Administration rights), enter the name of the Odoo 19 database and click
*Import*. Host, port, user and password are only needed when the Odoo 19
database is not on the same PostgreSQL server as this one: empty, they are
the ones this server uses for its own database. The filestore folder (for
room and service images) defaults to the Odoo 19 database's folder in this
server's data folder, when it is there.

Copied: floors, room / amenity / service types, amenities, services, rooms
(images, taxes, amenities, status), the customers and salespersons of the
folios, the folios with their room lines, service lines, other order lines,
room occupancy and state, and the company's extra-hours setting. Taxes,
units, pricelists, warehouses, countries and users are matched with the ones
of this database (by amount and type, name, code, login).

Not copied: invoices and payments, which stay in the Odoo 19 database; each
order gets a note with its Odoo 19 invoice numbers. Orders fully invoiced in
Odoo 19 are closed for invoicing (*Manually Closed For Invoicing*), so they
show as invoiced and are not invoiced again. Orders not invoiced at all stay
*to invoice*. Orders partly invoiced in Odoo 19 stay *to invoice* too, with a
note and a line in the import result: invoice only the rest. Taxes of other
companies are not copied either. Every record is copied into the current
company.

The import can be run again: it only adds what is not there yet.
