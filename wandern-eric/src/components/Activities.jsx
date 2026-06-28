import { useEffect, useState } from "react";

const ACTIVITIES_URL = "https://storage.googleapis.com/wandern-eric-data/activities.json";
const ICON_BASE = `${import.meta.env.BASE_URL}activities/`;

// Google Health exerciseType -> icon file in public/activities/. Unknown types fall
// back to default.svg (also the runtime fallback if an icon file 404s).
const ICON_BY_TYPE = {
    BIKING: "bike.svg",
    TREADMILL: "treadmill.svg",
    WALKING: "walk.svg",
};

function iconSrc(type) {
    return ICON_BASE + (ICON_BY_TYPE[type] || "default.svg");
}

function formatDuration(seconds) {
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes} min`;
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return m ? `${h}h ${m}m` : `${h}h`;
}

function formatDate(dateStr) {
    // dateStr is "YYYY-MM-DD"; pin to local midnight so it doesn't shift a day.
    const d = new Date(`${dateStr}T00:00:00`);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function Activities() {
    const [activities, setActivities] = useState(null);

    useEffect(() => {
        // activities.json may briefly not exist; treat any failure as "no activities".
        fetch(ACTIVITIES_URL)
            .then((res) => (res.ok ? res.json() : []))
            .then(setActivities)
            .catch(() => setActivities([]));
    }, []);

    if (!activities || activities.length === 0) return null;

    return (
        <div className="bg-white p-6 rounded-xl shadow h-full">
            <h3 className="text-lg font-semibold mb-4 text-blue-400 text-center">
                Latest Activities
            </h3>
            <ul className="flex flex-col gap-3">
                {activities.map((a) => (
                    <li
                        key={`${a.date}-${a.exercise_type}`}
                        className="flex items-center gap-4 bg-gray-50 rounded-lg p-3"
                    >
                        <img
                            src={iconSrc(a.exercise_type)}
                            alt={a.label}
                            className="w-10 h-10 shrink-0"
                            onError={(e) => {
                                if (!e.currentTarget.src.endsWith("default.svg")) {
                                    e.currentTarget.src = `${ICON_BASE}default.svg`;
                                }
                            }}
                        />
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                                <p className="font-semibold text-gray-800 truncate">
                                    {a.label}
                                    {a.sessions > 1 && (
                                        <span className="text-gray-400 font-normal"> ×{a.sessions}</span>
                                    )}
                                </p>
                                <p className="text-sm text-gray-400 shrink-0">{formatDate(a.date)}</p>
                            </div>
                            <p className="text-sm text-gray-500">
                                {a.distance_km > 0 && `${a.distance_km.toFixed(2)} km · `}
                                {formatDuration(a.duration_seconds)}
                            </p>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
}
