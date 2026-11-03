## 20.0.1.0.0

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`, groups
  under a "Hotel" privilege (Services), no `report_file` on the report.
- After installation, Administrator is a Hotel Manager. Hotel users are also
  "Sales: All Documents" users: a folio is a sales order.
- Confirming a folio runs the standard sales confirmation. Rooms and hotel
  services are service products, so no delivery order is created (the
  migration converts existing room/service products without stock moves).
- "Set to Draft" uses the standard quotation reset; cancelling a folio no
  longer cancels posted invoices (only draft ones, as in Sales).
- New room board (kanban grouped by status), now the default Rooms view.
- Faster room availability search; a stay ending when the next one starts no
  longer blocks the room. Double bookings inside a folio are also checked
  when a line is added directly.
- Taxes on folio and service lines are limited to the folio's company and
  mapped by its fiscal position.
- "Parent / Child" search on room types, amenity types and service types.
- Folio report: correct check-in/out per folio, no error on a folio without
  room lines.
- New: copy the hotel data of an Odoo 19 database into an Odoo 20 database,
  automatically at installation or from *Configuration > Import from Odoo
  19* (see Usage).
- Upgrading from 19.0: the database must be migrated to 20.0 first (Odoo
  upgrade or OpenUpgrade). If it still has the module under its old name
  `hotel`, run `vertical_hotel/scripts/rename_hotel_to_vertical_hotel.py`
  before upgrading (see 19.0.1.1.0).

## 19.0.1.1.0

- The module was renamed from `hotel` to `vertical_hotel`. Models
  (`hotel.folio`, `hotel.room`, ...) are unchanged; only the module name and
  its XML-ID namespace (`hotel.xxx` becomes `vertical_hotel.xxx`) changed.

  **Upgrading a database where `hotel` is installed** (always on a backup,
  with Odoo stopped, before starting Odoo on the new code):

  ``` bash
  python3 vertical_hotel/scripts/rename_hotel_to_vertical_hotel.py -d <db> --dry-run
  python3 vertical_hotel/scripts/rename_hotel_to_vertical_hotel.py -d <db>
  odoo-bin -d <db> -u vertical_hotel --stop-after-init
  ```

  Use the Python of the Odoo environment (it needs `psycopg2`) and add
  `--db_host`, `--db_port`, `-r <user>` and `-w` as needed. When migrating
  from 18.0 with OpenUpgrade, the rename is done by OpenUpgrade instead.

  Custom modules must replace `"hotel"` by `"vertical_hotel"` in their
  `depends` and every `hotel.<xmlid>` reference (`ref=`, `parent=`,
  `groups=`, `inherit_id`, `env.ref()`, `ir.model.access.csv`) by
  `vertical_hotel.<xmlid>`. Python installs from PyPI use
  `odoo-addon-vertical_hotel` instead of `odoo-addon-hotel`.
