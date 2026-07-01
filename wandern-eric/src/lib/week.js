// Monday-start week helpers. Timezone-safe by construction: everything operates
// on "YYYY-MM-DD" calendar-date strings (which the backend already emits in
// Berlin-local time), never on the browser clock. Reused by the week-over-week
// chart and, later, the heatmap's Monday-start fix.

export const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

// Parse "YYYY-MM-DD" as a local calendar date (no UTC shift).
function parseYMD(str) {
  const [y, m, d] = str.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function toYMD(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

// 0 = Monday … 6 = Sunday (JS getDay() is 0 = Sunday).
export function weekdayIndex(dateStr) {
  return (parseYMD(dateStr).getDay() + 6) % 7;
}

export function weekdayName(dateStr) {
  return WEEKDAYS[weekdayIndex(dateStr)];
}

// The 7 date strings (Mon→Sun) of the week containing `anchorStr`, offset by
// `weekOffset` weeks (0 = this week, -1 = last week).
export function weekDates(anchorStr, weekOffset = 0) {
  const monday = parseYMD(anchorStr);
  monday.setDate(monday.getDate() - weekdayIndex(anchorStr) + weekOffset * 7);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return toYMD(d);
  });
}
