import { useEffect, useState } from "react";

import { DATA_BASE_URL } from "../lib/config";
import StepHeatmap from "./StepHeatmap";

export default function Heatmap() {
    const today = new Date();
    const pastDate = new Date(new Date().setDate(new Date().getDate() - 365));
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

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
            .then(([historical, todayRecord]) => {
                const byDate = new Map(historical.map((d) => [d.date, d]));
                // Finalized data always wins; only add today if it isn't finalized yet.
                if (todayRecord && !byDate.has(todayRecord.date)) {
                    byDate.set(todayRecord.date, todayRecord);
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
            <StepHeatmap data={data} startDate={pastDate} endDate={today} />
        </div>
    );
}
