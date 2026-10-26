## Bring the data of an Odoo 19 database

The hotel data of an Odoo 19 database (module `hotel` or `vertical_hotel`)
can be copied into a new Odoo 20 database. The Odoo 19 database is only read,
never changed.

**At installation**: name the Odoo 19 database in the Odoo configuration file
of the Odoo 20 server, then install *Hotel Management*:

``` ini
[options]
vertical_hotel_import_db = customer-19
; only when different from this server's own connection:
vertical_hotel_import_host = localhost
vertical_hotel_import_port = 5432
vertical_hotel_import_user = odoo
vertical_hotel_import_password = secret
; folder with the Odoo 19 files, for room and service images:
vertical_hotel_import_filestore = /var/lib/odoo/filestore/customer-19
```

**Afterwards**: *Hotel Management > Configuration > Import from Odoo 19*
(Settings / Administration rights), fill in the database and click *Import*.

Copied: floors, room / amenity / service types, amenities, services, rooms
(images, taxes, amenities, status), the customers and salespersons of the
folios, the folios with their room lines, service lines, other order lines,
room occupancy and state, and the company's extra-hours setting. Taxes,
units, pricelists, warehouses, countries and users are matched with the ones
of this database (by amount and type, name, code, login).

Not copied: invoices and payments (each order gets a note with the Odoo 19
invoice numbers), taxes of other companies. Every record is copied into the
current company.

The import can be run again: it only adds what is not there yet.
