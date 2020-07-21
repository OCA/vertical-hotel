This is an alternative implementation of the reservation summary
already implemented in `hotel_reservation` module.

Why did we implement a new version?

- the summary is built on top of hotel.room.reservation.line. That model is strongly linked to hotel_reservation.line,
- we find it complex to maintain a correct matching state between those two models,
- the code to synchronise states is making the reservation code complex,
- it is hard to extend the current code (for example we would like to display days where a draft reservation is running)
- the summary code could be in a separate module for more modularity

What did we keep?
- the reservation table template
- the javascript widget and the data model to use it.
