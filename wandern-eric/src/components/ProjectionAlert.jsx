import { useEffect, useState } from "react";

import { DATA_BASE_URL } from "../lib/config";

const AGG_URL = `${DATA_BASE_URL}/aggregations.json`;

// End-of-month guilt banner: steps/day still needed to match last month's
// average. Only shows from the 20th of the month.
export default function ProjectionAlert() {
    const today = new Date();
    const [data, setData] = useState(null);

    useEffect(() => {
        fetch(AGG_URL)
            .then((res) => (res.ok ? res.json() : null))
            .then(setData)
            .catch(() => setData(null));
    }, []);

    if (!data) return null;

    const current = parseInt(data.prev_month_avg_to_eom_projection.current_month);
    const prev_month = parseInt(data.prev_month_avg_to_eom_projection.last_month);
    const indicatorMsg =
        current < prev_month
            ? `Extra ${Math.abs(current)} steps per day compared to last months!`
            : `Missing ${current} steps to reach last month avg`;

    let BgAlertColor;
    if (current < prev_month) {
        BgAlertColor = "bg-green-400";
    } else if (current > prev_month * 1.75) {
        BgAlertColor = "bg-red-400";
    } else {
        BgAlertColor = "bg-blue-400";
    }

    const showAlert = today.getDate() >= 20 && current > -10000;
    if (!showAlert) return null;

    return (
        <div className={`${BgAlertColor} p-4 rounded-xl shadow text-center`}>
            <p className="text-l font-bold">{indicatorMsg}</p>
            <p className="text-l font-bold">Last Month Avg: {prev_month}</p>
        </div>
    );
}
