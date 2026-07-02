import { useState } from "react";

// Changelog entries, newest first. Add a new object on top for each release.
// Drafted from git history — edit freely.
const CHANGES = [
    {
        date: "2026-07-02",
        items: [
            "The step heatmap now starts each week on Monday.",
            "Replaced the third-party calendar-heatmap library with our own implementation.",
        ],
    },
    {
        date: "2026-07-01",
        items: [
            "Added a week-over-week chart — this week vs last week as bars, with your typical week as a line.",
        ],
    },
    {
        date: "2026-06-28",
        items: [
            "Added a Latest Activities panel — your most recent bike, treadmill, and walk workouts, pulled from the Google Health API.",
            "Reworked the dashboard layout: aggregation stats on the left, latest activities on the right.",
        ],
    },
    {
        date: "2026-06-21",
        items: [
            "🤖 Claude joined the team!",
            "Added intra-day step tracking — today's progress now updates hourly and shows as an outlined cell on the heatmap.",
            "Migrated the step data source from the Fitbit Web API to the Google Health API.",
            "Added this changelog.",
        ],
    },
    {
        date: "2026-02-14",
        items: ["Added a line chart of historical average steps per month."],
    },
    {
        date: "2026-02-03",
        items: ["Fixed the month ordering in the monthly-average aggregation."],
    },
    {
        date: "2026-01-07",
        items: ["Fixed the heatmap missing the start-of-year date range."],
    },
    {
        date: "2025-12-05",
        items: ["Moved the site to a custom domain (wandern-eric.de)."],
    },
    {
        date: "2025-11-29",
        items: [
            'Added the "steps per day needed to match last month\'s average" projection (backend + frontend).',
            "Refactored the Fitbit extraction logic.",
        ],
    },
    {
        date: "2025-11-28",
        items: ["Built the automatic Fitbit token-refresh pipeline."],
    },
    {
        date: "2025-11-25",
        items: [
            "Added aggregations: max steps, best average weekday, and monthly averages.",
        ],
    },
    {
        date: "2025-11-23",
        items: ["Moved step data to a cloud storage bucket (GCS)."],
    },
    {
        date: "2025-11-22",
        items: ["Automated the daily step-data update."],
    },
    {
        date: "2025-11-19",
        items: ["Wandern Eric goes live — Fitbit step heatmap on the web."],
    },
];

export default function Changelog() {
    const [open, setOpen] = useState(false);

    return (
        <div className="bg-white p-6 rounded-xl shadow">
            <button
                onClick={() => setOpen((o) => !o)}
                className="cursor-pointer text-blue-400 font-semibold flex items-center gap-2 mx-auto"
                aria-expanded={open}
            >
                <span>{open ? "▾" : "▸"}</span>
                {open ? "Changelog" : "Click for changelog"}
            </button>

            {open && (
                <ol className="mt-4 space-y-4 text-left">
                    {CHANGES.map((entry) => (
                        <li key={entry.date}>
                            <p className="text-sm font-bold text-blue-400">{entry.date}</p>
                            <ul className="mt-1 list-disc list-inside text-gray-700">
                                {entry.items.map((item, i) => (
                                    <li key={i}>{item}</li>
                                ))}
                            </ul>
                        </li>
                    ))}
                </ol>
            )}
        </div>
    );
}
