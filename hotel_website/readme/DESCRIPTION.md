A guest-facing hotel website for the vertical-hotel modules. Guests browse
room types, check what is free for their dates and send a reservation
request; the front desk confirms it, and a free room of the requested type
is assigned at that moment.

It is a request form, not a booking engine: a request holds no room until
the front desk confirms it, and the pages and the acknowledgement say so.
Requests nobody confirms are cancelled after a few days (see
*Configuration*).

What guests see:

- On the websites with the hotel layout: a homepage with the hotel's name
  (always the company's name), a booking bar and the room types; the
  company's name as header brand, page title and copyright. Other websites
  of the database keep their own look; the booking pages work on all of
  them, in the website theme's fonts.
- **Rooms & Suites** (`/rooms`): every room type with photos, description,
  capacity, amenities and "from" price. With dates, each type shows how
  many rooms are still free and can be added to the stay.
- A page per room type with gallery, facts, availability and reviews.
  Guests who stayed in a room type (confirmed reservation or folio) can
  review it once; reviews show after the hotel publishes them.
- A stay summary, a guest details form with the accompanying guests, and a
  "request received" page.
- Their requests and reservations in the portal (`/my/reservations`).

How a website request becomes a reservation:

1. The request is saved as a **draft** reservation, marked *Booked Online*,
   with one line per requested room carrying only its room type, and the
   accompanying guests on its *Guests* tab (each one a contact under the
   guest who booked). No room is blocked yet.
2. The guest gets an acknowledgement from the reservation's chatter. The
   form is protected by the website's captcha (reCAPTCHA or Cloudflare
   Turnstile, when set up), and one visitor can only send a few requests
   (5 a day per address, 3 open requests per e-mail).
3. The receptionist presses **Confirm**: each line without a room gets a
   free room of its type (cheapest first), then the usual confirmation runs
   (overlap check, room blocking, capacity check).
4. From there it is the normal flow: confirmation email, folio, check-in,
   invoice.

Availability follows the back office rule (confirmed reservations and folios
block a room). Only rooms marked *Bookable on Website* are offered.
