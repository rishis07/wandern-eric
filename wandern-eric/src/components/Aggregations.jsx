import React, { useEffect, useState } from "react";

export default function Heatmap() {
    const today = new Date();
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch("https://storage.googleapis.com/wandern-eric-data/aggregations.json")
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
        // Cards for each aggregation type (max steps, avg dow, avg per month)
        <div className="bg-white p-6 text-center rounded-xl shadow grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-400 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Max Steps</h3>
                <p className="text-2xl font-bold">{data.max_steps.date}</p>
                <p className="text-2xl font-bold">{data.max_steps.count}</p>
            </div>
            <div className="bg-blue-400 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Max avg Day of the week</h3>
                <p className="text-2xl font-bold">{data.max_avg_dow.day_of_week}</p>
                <p className="text-2xl font-bold">{data.max_avg_dow.count.toFixed(0)}</p>
            </div>
            <div className="bg-blue-400 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Average Steps per Month</h3>
                <ul>
                    {data.avg_per_month.map((monthData) => (
                        <li key={monthData.month} className="text-2xl font-bold">
                            {monthData.month}: {monthData.count.toFixed(0)}
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}
