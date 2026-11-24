# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tools import SQL
from odoo.tools.sql import column_exists, table_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Reservation summaries are saved screens, not data: their period
    columns change from datetime to date and the grid is now computed, so
    drop the old rows and columns instead of converting them."""
    if not table_exists(cr, "room_reservation_summary"):
        return
    cr.execute("DELETE FROM room_reservation_summary")
    _logger.info("Deleted %s saved reservation summaries", cr.rowcount)
    for column in ("date_from", "date_to", "summary_header", "room_summary"):
        if column_exists(cr, "room_reservation_summary", column):
            cr.execute(
                SQL(
                    "ALTER TABLE room_reservation_summary DROP COLUMN %s",
                    SQL.identifier(column),
                )
            )
