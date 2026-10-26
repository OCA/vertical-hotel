## 20.0.1.0.0

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`, no
  `report_file` on the report, depends on `vertical_hotel` only.
- The Activity Report printed empty on Odoo 20 (`t-esc`); it now shows the
  room, the period and the activities, with the duration in hours:minutes.
  It can also be printed from selected jobs (*Print > Activity Detail*).
- New board of housekeeping jobs grouped by status (default view), a
  calendar, and *My Jobs*, *Today* and *Open* filters.
- New housekeeping status on rooms (*Needs Cleaning*, *To Inspect*,
  *Ready*), shown on the room form, list and board, with a *Housekeeping*
  button on the room.
- The inspection time must now be **after** the end of the cleaning (the
  check was reversed). It is optional and filled in when the job is done.
- The workflow is checked on the server: a job is done only after
  cleaning, and a done or cancelled job cannot be changed by the buttons.
- Hotel users can remove activity lines; a loop in activity types is
  refused instead of freezing the server; *Done* works on several jobs.
- Activity lines are deleted with their job.
