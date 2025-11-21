import React from "react";
import CalendarHeatmap from "react-calendar-heatmap";
import { Tooltip } from "react-tooltip";
import data from "../data/data.json"; // <-- import JSON
import "react-calendar-heatmap/dist/styles.css";

export default function Heatmap() {
    const today = new Date();

    return (
        <div className="bg-white p-6 rounded-xl shadow">
            <h2 className="text-xl font-semibold mb-4">Daily Walking Activity</h2>

            <CalendarHeatmap
                startDate={new Date(today.getFullYear(), 0, 1)}
                endDate={today}
                values={data} // use imported JSON
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
                        ? `${value.date}: ${value.count} walks`
                        : "No data",
                })}
                showWeekdayLabels={true}
            />

            <Tooltip id="walking-heatmap-tooltip" />
        </div>
    );
}
