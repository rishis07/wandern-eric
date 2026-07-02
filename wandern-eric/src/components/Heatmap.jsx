import React, { useEffect, useState } from "react";
import CalendarHeatmap from "react-calendar-heatmap";
import { Tooltip } from "react-tooltip";
import "react-calendar-heatmap/dist/styles.css";

import { DATA_BASE_URL } from "../lib/config";

export default function Heatmap() {
    const today = new Date();
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    const pastDate = new Date(new Date().setDate(new Date().getDate() - 365));


    useEffect(() => {
        const base = DATA_BASE_URL;

        // Finalized days (required) + today's in-progress record (optional).
        const historicalReq = fetch(`${base}/data.json`).then((res) => {
            if (!res.ok) throw new Error("Failed to load heatmap data");
            return res.json();
        });

        // today.json may not exist yet (e.g. overnight); treat any failure as "no today".
        const todayReq = fetch(`${base}/today.json`)
            .then((res) => (res.ok ? res.json() : null))
            .catch(() => null);

        Promise.all([historicalReq, todayReq])
            .then(([historical, today]) => {
                const byDate = new Map(historical.map((d) => [d.date, d]));
                // Finalized data always wins; only add today if it isn't finalized yet.
                if (today && !byDate.has(today.date)) {
                    byDate.set(today.date, today);
                }
                setData(Array.from(byDate.values()));
            })
            .catch((err) => setError(err.message));
    }, []);

    if (error) {
        return (
            <div className="bg-red-100 p-4 rounded-xl text-red-700">
                Error loading heatmap data: {error}
            </div>
        );
    }

    if (!data) {
        return (
            <div className="bg-white p-6 rounded-xl shadow text-gray-500">
                Loading heatmap…
            </div>
        );
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow">
            <CalendarHeatmap
                startDate={pastDate}
                endDate={today}
                values={data}
                classForValue={(value) => {
                    if (!value) return "color-scale-0";
                    let scale;
                    if (value.count <= 1000) scale = "color-scale-1";
                    else if (value.count <= 2500) scale = "color-scale-2";
                    else if (value.count <= 5000) scale = "color-scale-3";
                    else if (value.count <= 7500) scale = "color-scale-4";
                    else if (value.count < 10000) scale = "color-scale-5";
                    else scale = "color-scale-6";
                    // mark today's still-in-progress cell so it stands out
                    return value.intraday ? `${scale} color-scale-intraday` : scale;
                }}
                tooltipDataAttrs={(value) => ({
                    "data-tooltip-id": "walking-heatmap-tooltip",
                    "data-tooltip-content": value.date
                        ? `${value.date}: ${value.count} steps${value.intraday ? " (so far today)" : ""}`
                        : "No data",
                })}
                showWeekdayLabels={true}
            />

            <Tooltip id="walking-heatmap-tooltip" />
        </div>
    );
}
