import React, { useEffect, useState } from "react";
import CalendarHeatmap from "react-calendar-heatmap";
import { Tooltip } from "react-tooltip";
import "react-calendar-heatmap/dist/styles.css";

export default function Heatmap() {
    const today = new Date();
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch("https://storage.googleapis.com/wandern-eric-data/data.json")
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Failed to load heatmap data");
                }
                return res.json();
            })
            .then((json) => setData(json))
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
            <h2 className="text-xl font-semibold mb-4">Daily Walking Activity</h2>

            <CalendarHeatmap
                startDate={new Date(today.getFullYear(), 0, 1)}
                endDate={today}
                values={data}
                classForValue={(value) => {
                    if (!value) return "color-scale-0";
                    if (value.count <= 1000) return "color-scale-1";
                    if (value.count <= 2500) return "color-scale-2";
                    if (value.count <= 5000) return "color-scale-3";
                    if (value.count <= 7500) return "color-scale-4";
                    if (value.count < 10000) return "color-scale-5";
                    if (value.count >= 10000) return "color-scale-6";
                }}
                tooltipDataAttrs={(value) => ({
                    "data-tooltip-id": "walking-heatmap-tooltip",
                    "data-tooltip-content": value.date
                        ? `${value.date}: ${value.count} steps`
                        : "No data",
                })}
                showWeekdayLabels={true}
            />

            <Tooltip id="walking-heatmap-tooltip" />
        </div>
    );
}
