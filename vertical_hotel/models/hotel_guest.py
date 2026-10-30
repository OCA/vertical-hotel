# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import ClassVar

import psycopg2

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class HotelGuest(models.Model):
    """A person occupying a room, filed as a child contact of whoever
    made the booking.

    Delegation to res.partner (the same pattern hotel.room and hotel.folio
    already use) means every guest *is* a contact: the name, phone, email
    and address fields come for free, the record shows up under the booking
    partner in Contacts, and nothing here has to re-implement address
    handling."""

    _name = "hotel.guest"
    _description = "Hotel Guest"
    _inherits: ClassVar[dict] = {"res.partner": "partner_id"}
    _rec_name = "partner_id"

    partner_id = fields.Many2one(
        "res.partner",
        "Guest Contact",
        required=True,
        ondelete="cascade",
        index=True,
    )
    folio_id = fields.Many2one(
        "hotel.folio",
        ondelete="cascade",
        index=True,
    )
    guest_type = fields.Selection(
        [("adult", "Adult"), ("child", "Child")],
        required=True,
        default="adult",
        help="Counted towards the room capacity check on confirmation.",
    )

    @api.model
    def _resolve_host_partner(self, vals):
        """The contact this guest should be filed under.

        Extended by hotel_reservation so a guest added on a reservation
        hangs under the reservation's partner."""
        if vals.get("folio_id"):
            return self.env["hotel.folio"].browse(vals["folio_id"]).partner_id
        return self.env["res.partner"]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("partner_id"):
                # Linking a contact that already exists (a reservation guest
                # carried onto its folio): it is filed correctly already.
                continue
            if not vals.get("parent_id"):
                host = self._resolve_host_partner(vals)
                if host:
                    vals["parent_id"] = host.id
            # Standard shape for a child contact, so the guest appears in
            # the booker's contact hierarchy rather than as a loose partner.
            vals.setdefault("type", "contact")
        return super().create(vals_list)

    def unlink(self):
        """Take the delegated contact down with the guest line.

        Odoo's _inherits does not cascade on unlink, so without this a
        removed guest would leave an orphan contact behind. A contact that
        is already referenced elsewhere (an invoice, say) cannot be
        deleted - archive it instead of failing the whole removal.

        A reservation and the folio made from it share the same contacts,
        so a contact is only removed once no guest line uses it any more."""
        partners = self.partner_id
        res = super().unlink()
        still_used = self.search([("partner_id", "in", partners.ids)]).partner_id
        for partner in partners - still_used:
            try:
                with self.env.cr.savepoint():
                    partner.unlink()
            except (UserError, ValidationError, psycopg2.Error):
                partner.active = False
        return res
