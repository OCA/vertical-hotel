Generates a report for room housekeeping.

The report contains a row per room and a column for
- room name,
- each day of the current week,
- a comment from the reservation line.

Each day cell contains:
- A if a checkin is scheduled on that day
- D if a checkout is scheduled on that day
- D/A if both a checkin and a checkout are scheduled on that day
- O if the room is busy (occupied) onn that day
- nothing if the room is free
