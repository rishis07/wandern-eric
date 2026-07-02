import { Tooltip } from "react-tooltip";

// Custom SVG step heatmap. GitHub-style contribution grid, but weeks run
// Monday (top row) to Sunday (bottom). Presentational: it takes the already
// merged { date, count, intraday? } records plus the [startDate, endDate] window
// and renders. Colors come from the .color-scale-* classes in index.css.

const CELL = 10; // cell edge, in SVG units
const GAP = 1; // gap between cells
const LEFT = 30; // left margin for weekday labels
const TOP = 14; // top margin for month labels
const STEP = CELL + GAP;
const BOTTOM_MARGIN = 5; // extra breathing room below the grid, in SVG units
const DAY_MS = 86400000;

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const WEEKDAY_LABELS = [
    { row: 0, label: "Mon" },
    { row: 2, label: "Wed" },
    { row: 4, label: "Fri" },
];

const pad = (n) => String(n).padStart(2, "0");
const toKey = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const mondayIdx = (d) => (d.getDay() + 6) % 7; // Mon=0 .. Sun=6

function colorClass(value) {
    if (!value) return "color-scale-0";
    let scale;
    if (value.count <= 1000) scale = "color-scale-1";
    else if (value.count <= 2500) scale = "color-scale-2";
    else if (value.count <= 5000) scale = "color-scale-3";
    else if (value.count <= 7500) scale = "color-scale-4";
    else if (value.count < 10000) scale = "color-scale-5";
    else scale = "color-scale-6";
    return value.intraday ? `${scale} color-scale-intraday` : scale;
}

function tooltipContent(value) {
    if (!value) return "No data";
    return `${value.date}: ${value.count} steps${value.intraday ? " (so far today)" : ""}`;
}

export default function StepHeatmap({
    data,
    startDate,
    endDate,
    tooltipId = "walking-heatmap-tooltip",
}) {
    const byDate = new Map((data || []).map((d) => [d.date, d]));

    const start = new Date(startDate);
    start.setHours(0, 0, 0, 0);
    const end = new Date(endDate);
    end.setHours(0, 0, 0, 0);

    // First column begins on the Monday of the week containing startDate.
    const gridStart = new Date(start);
    gridStart.setDate(start.getDate() - mondayIdx(start));

    const totalCols = Math.floor(Math.round((end - gridStart) / DAY_MS) / 7) + 1;

    const cells = [];
    const monthLabels = [];
    let lastMonth = -1;

    for (let d = new Date(gridStart); d <= end; d.setDate(d.getDate() + 1)) {
        if (d < start) continue; // leading out-of-range days stay blank

        const col = Math.floor(Math.round((d - gridStart) / DAY_MS) / 7);
        const row = mondayIdx(d);

        // Label a month above the column that holds its first in-range day.
        // Skip a month that first appears in the last column (a sliver with no
        // room for a label), matching the old library.
        if (d.getMonth() !== lastMonth) {
            lastMonth = d.getMonth();
            if (col < totalCols - 1) {
                monthLabels.push({ x: LEFT + col * STEP, label: MONTHS[d.getMonth()] });
            }
        }

        const value = byDate.get(toKey(d));
        cells.push({
            x: LEFT + col * STEP,
            y: TOP + row * STEP,
            className: colorClass(value),
            content: tooltipContent(value),
        });
    }

    const width = LEFT + totalCols * STEP;
    const height = TOP + 7 * STEP;

    return (
        <>
            <svg
                viewBox={`0 0 ${width} ${height + BOTTOM_MARGIN}`}
                width="100%"
                style={{ display: "block" }}
            >
                {monthLabels.map((m, i) => (
                    <text
                        key={`m${i}`}
                        x={m.x}
                        y={TOP - 4}
                        fontSize={10}
                        fill="#aaa"
                        textAnchor="start"
                    >
                        {m.label}
                    </text>
                ))}
                {WEEKDAY_LABELS.map((w) => (
                    <text
                        key={w.label}
                        x={0}
                        y={TOP + w.row * STEP + 7}
                        fontSize={10}
                        fill="#aaa"
                    >
                        {w.label}
                    </text>
                ))}
                {cells.map((c, i) => (
                    <rect
                        key={i}
                        x={c.x}
                        y={c.y}
                        width={CELL}
                        height={CELL}
                        className={`heatmap-cell ${c.className}`}
                        data-tooltip-id={tooltipId}
                        data-tooltip-content={c.content}
                    />
                ))}
            </svg>
            <Tooltip id={tooltipId} />
        </>
    );
}
