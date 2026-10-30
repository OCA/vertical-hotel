A guest-facing hotel website for the vertical-hotel modules. Guests browse
room types, check what is free for their dates and send a reservation
request; the front desk confirms it, and a free room of the requested type
is assigned at that moment.

What guests see:

- A homepage with the hotel's name (always the company's name), a booking
  bar and the room types.
- **Rooms & Suites** (`/rooms`): every room type with photos, description,
  capacity, amenities and "from" price. With dates, each type shows how
  many rooms are still free and can be added to the stay.
- A page per room type with gallery, facts, availability and reviews.
- A stay summary, a guest details form with the accompanying guests, and a
  "request received" page.
- Their requests and reservations in the portal (`/my/reservations`).

How a website request becomes a reservation:

1. The request is saved as a **draft** reservation, marked *Booked Online*,
   with one line per requested room carrying only its room type, and the
   accompanying guests on its *Guests* tab (each one a contact under the
   guest who booked). No room is blocked yet.
2. The guest gets an acknowledgement from the reservation's chatter.
3. The receptionist presses **Confirm**: each line without a room gets a
   free room of its type (cheapest first), then the usual confirmation runs
   (overlap check, room blocking, capacity check).
4. From there it is the normal flow: confirmation email, folio, check-in,
   invoice.

Availability follows the back office rule (confirmed reservations and folios
block a room). Only rooms marked *Bookable on Website* are offered.
