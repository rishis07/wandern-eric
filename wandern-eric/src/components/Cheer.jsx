import { useEffect, useState } from "react";

import { fetchCheerAggregations, submitCheer } from "../lib/cheerApi";
import { BUY_ME_A_COFFEE_URL } from "../lib/config";

const CHEERED_KEY = "wandern-eric-cheered";

export default function Cheer() {
    const [aggregations, setAggregations] = useState(null);
    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState(null);
    const [cheered, setCheered] = useState(
        () => localStorage.getItem(CHEERED_KEY) === "true",
    );

    useEffect(() => {
        fetchCheerAggregations()
            .then(setAggregations)
            .catch((err) => setError(err.message));
    }, []);

    async function cheer() {
        setSubmitting(true);
        setSubmitError(null);
        try {
            await submitCheer();
            const fresh = await fetchCheerAggregations();
            setAggregations(fresh);
            localStorage.setItem(CHEERED_KEY, "true");
            setCheered(true);
        } catch (err) {
            setSubmitError(err.message);
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div id="support" className="bg-white p-6 rounded-xl shadow scroll-mt-6">
            <h3 className="text-lg font-semibold mb-4 text-blue-400 text-center">
                Support Eric on
            </h3>

            <div className="flex flex-col items-center gap-2">
                <a
                    href={BUY_ME_A_COFFEE_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-yellow-400 text-gray-900 font-semibold px-4 py-2 rounded-lg"
                >
                    ☕ Buy me a coffee
                </a>
                <p className="text-sm text-gray-500 text-center">
                    I'll walk 1,000 extra steps for you ☕ — plus it helps cover the
                    Raspberry Pi and domain that keep this dashboard running.
                </p>
            </div>

            <div className="mt-6 border-t border-gray-100 pt-4 flex flex-col items-center gap-2">
                <p className="text-xs uppercase tracking-wide text-gray-400">
                    Or, cheer for free
                </p>

                <div className="flex items-center justify-center gap-3 flex-wrap">
                    {cheered ? (
                        <p className="text-gray-700 font-medium">
                            Thanks for the support! 🎉
                        </p>
                    ) : (
                        <button
                            onClick={cheer}
                            disabled={submitting}
                            className="cursor-pointer bg-blue-400 text-white font-semibold px-4 py-2 rounded-lg disabled:opacity-50"
                        >
                            👏 Support
                        </button>
                    )}

                    {error && (
                        <p className="text-sm text-red-700">
                            Error loading support data: {error}
                        </p>
                    )}

                    {!error && !aggregations && (
                        <p className="text-sm text-gray-500">Loading…</p>
                    )}

                    {aggregations && (
                        <p className="text-gray-700">
                            <span className="font-bold text-blue-400">
                                {aggregations.count}
                            </span>{" "}
                            people supported this month
                        </p>
                    )}
                </div>

                <p className="text-sm text-gray-500 text-center">
                    I'll walk 100 extra steps for you 👏
                </p>

                {submitError && (
                    <p className="text-sm text-red-700">
                        Couldn't submit your support: {submitError}
                    </p>
                )}
            </div>
        </div>
    );
}
