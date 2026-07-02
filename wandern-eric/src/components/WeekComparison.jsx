import { useEffect, useState } from "react";

import {
    ComposedChart,
    Bar,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

import { WEEKDAYS, weekDates } from "../lib/week";
import { DATA_BASE_URL } from "../lib/config";

const BASE = DATA_BASE_URL;

// Averaging is the backend's job (avg_steps_by_weekday). This week / last week
// are raw daily counts we just window out of data.json + today.json — the same
// "finalized wins, add today if not yet finalized" merge the heatmap does.
export default function WeekComparison() {
    const [chartData, setChartData] = useState(null);
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        // Required inputs: the daily data and the backend's weekday averages.
        const dataReq = fetch(`${BASE}/data.json`).then((res) => {
            if (!res.ok) throw new Error();
            return res.json();
        });
        const aggReq = fetch(`${BASE}/aggregations.json`).then((res) => {
            if (!res.ok) throw new Error();
            return res.json();
        });
        // Optional: today's in-progress bar. Its absence shouldn't blank the chart.
        const todayReq = fetch(`${BASE}/today.json`)
            .then((res) => (res.ok ? res.json() : null))
            .catch(() => null);

        Promise.all([dataReq, aggReq, todayReq])
            .then(([data, agg, today]) => {
                const avg = agg?.avg_steps_by_weekday;
                if (!data?.length || !avg?.length) throw new Error();

                const counts = new Map(data.map((d) => [d.date, d.count]));
                if (today && !counts.has(today.date)) {
                    counts.set(today.date, today.count);
                }

                // Anchor the week on the data itself (never the browser clock),
                // so week boundaries are correct in any timezone.
                const anchor = today?.date ?? data[data.length - 1].date;
                const thisWeek = weekDates(anchor, 0);
                const lastWeek = weekDates(anchor, -1);
                const avgByDay = new Map(avg.map((e) => [e.day, e.steps]));

                setChartData(
                    WEEKDAYS.map((day, i) => ({
                        day: day.slice(0, 3),
                        current: counts.get(thisWeek[i]) ?? null,
                        last: counts.get(lastWeek[i]) ?? null,
                        average: avgByDay.has(day) ? Math.round(avgByDay.get(day)) : null,
                    }))
                );
            })
            .catch(() => setFailed(true));
    }, []);

    if (failed) {
        return (
            <div className="bg-white p-6 rounded-xl shadow text-gray-500 text-center">
                Data couldn't be loaded
            </div>
        );
    }

    if (!chartData) {
        return (
            <div className="bg-white p-6 rounded-xl shadow text-gray-500">
                Loading chart…
            </div>
        );
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow">
            <h3 className="text-lg font-semibold mb-4 text-blue-400 text-center">
                This Week vs Last Week vs Historical Average
            </h3>

            <div style={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                    <ComposedChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="day" />
                        <YAxis />
                        <Tooltip labelStyle={{ color: "#60a5fa", fontWeight: 600 }} />
                        <Legend />
                        <Bar dataKey="last" name="Last week" fill="#bfdbfe" />
                        <Bar dataKey="current" name="This week" fill="#3b82f6" />
                        <Line
                            type="monotone"
                            dataKey="average"
                            name="Historical average"
                            stroke="#f59e0b"
                            strokeWidth={3}
                            dot={false}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
