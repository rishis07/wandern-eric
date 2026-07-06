import { CHEER_ENDPOINT, CHEERS_AGGREGATIONS_URL } from "./config";

function currentMonthKey() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function emptyAggregations() {
    return { month: currentMonthKey(), count: 0 };
}

// TEMPORARY DEV MOCK (specs/0006) — the Cloud Function + cheers_aggregations.json
// don't exist yet. This in-memory stand-in lets the UI be built/tested end to
// end. Remove this block (and the import.meta.env.DEV branches below) once
// CHEER_ENDPOINT points at a real deployed function.
let mockAggregations = { month: currentMonthKey(), count: 12 };

export async function fetchCheerAggregations() {
    if (import.meta.env.DEV) {
        await delay(200);
        return mockAggregations;
    }

    const res = await fetch(CHEERS_AGGREGATIONS_URL);
    if (res.status === 404) return emptyAggregations();
    if (!res.ok) throw new Error("Failed to load support data");
    return res.json();
}

// The server geolocates the request IP to attribute a country internally;
// the client never selects or sends one (see specs/0006 amendment).
export async function submitCheer() {
    if (import.meta.env.DEV) {
        await delay(300);
        mockAggregations = { ...mockAggregations, count: mockAggregations.count + 1 };
        return { ok: true };
    }

    const res = await fetch(CHEER_ENDPOINT, { method: "POST" });
    if (!res.ok) throw new Error("Failed to submit support");
    return res.json();
}
