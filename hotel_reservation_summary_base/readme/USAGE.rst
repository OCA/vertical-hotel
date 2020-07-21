To create a reservation summary, inherit this module and implement the hotel.room.reservation.summary
abstract class. For the new model, you need to

- overwrite action_generate_summary method,
- add an action calling action_generate_summary,
- add a menuitem calling that action,
- write a form view,
- set _form_view to that view.

See hotel_reservation_summary_range for an example implementation.
