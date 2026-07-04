import { useEffect, useState } from "react";

import { DATA_BASE_URL } from "../lib/config";

const AGG_URL = `${DATA_BASE_URL}/aggregations.json`;

export default function StepStats() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch(AGG_URL)
            .then((res) => {
                if (!res.ok) throw new Error("Failed to load aggregations data");
                return res.json();
            })
            .then((json) => setData(json))
            .catch((err) => setError(err.message));
    }, []);

    if (error) {
        return (
            <div className="bg-red-100 p-4 rounded-xl text-red-700">
                Error loading aggregations data: {error}
            </div>
        );
    }

    if (!data) {
        return (
            <div className="bg-white p-6 rounded-xl shadow text-gray-500">
                Loading aggregations…
            </div>
        );
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow h-full flex flex-col">
            <h3 className="text-lg font-semibold mb-4 text-blue-400 text-center">
                Step Stats
            </h3>
            <ul className="flex flex-col gap-4 flex-1 justify-center">
                <li className="bg-blue-400 text-white rounded-lg p-3 text-center">
                    <span className="font-semibold">Max Steps</span> —{" "}
                    <span className="font-bold">{data.max_steps.count}</span> · {data.max_steps.date}
                </li>

                <li className="bg-blue-400 text-white rounded-lg p-3 text-center">
                    <span className="font-semibold">Max Avg Weekday</span> —{" "}
                    {data.max_avg_dow.day_of_week} ·{" "}
                    <span className="font-bold">{data.max_avg_dow.count.toFixed(0)}</span>
                </li>

                <li className="bg-blue-400 text-white rounded-lg p-3 text-center">
                    <p className="font-semibold mb-1">Average Steps · last 3 months</p>
                    <ul className="text-sm space-y-0.5">
                        {data.avg_last_3_months.map((monthData) => (
                            <li key={monthData.month}>
                                {monthData.month}:{" "}
                                <span className="font-bold">{monthData.count.toFixed(0)}</span>
                            </li>
                        ))}
                    </ul>
                </li>
            </ul>
        </div>
    );
}
