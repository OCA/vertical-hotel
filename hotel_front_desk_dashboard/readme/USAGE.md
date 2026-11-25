Open *Hotel > Dashboard* (hotel users).

- Click a tile, or one of the small figures inside it, to open the
  records it counts; the arrival, departure and turnover rows open their
  folio or room.
- Type a guest name, a folio number or a room number in the search box to
  find the folio.
- The screen refreshes itself every minute; *Auto* switches that off and
  *Refresh* reloads it at once.

A room is *ready to sell* when its latest housekeeping job is done
(inspected) after the last guest left; a room cleaned but not inspected
yet, or still dirty, *needs housekeeping*.

Arrivals and departures are not checked in or out by hand: the hotel modules
have no check-in / check-out action yet. *Arrived* and *departed* are read
from the room status, which `hotel_reservation` recomputes every minute from
the stays planned around the current time. So a guest who never shows up is
marked as arrived once the check-in time has passed, and a departure is
marked as done once the check-out time has passed, even if the guest is
still in the room. *Overdue* departures only show in the short time between
the check-out time and the next update of the room status.
