"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

interface Flag {
    id: string;
    name: string;
    description: string;
    is_enabled: boolean;
    rollout_percentage: number;
    target_user_ids: string[];
    created_at: string;
    updated_at: string;
}

interface FlagAnalytics {
    flag_name: string;
    total_evaluations: number;
    true_count: number;
    false_count: number;
    true_percentage: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AdminFlagsPage() {
    const [flags, setFlags] = useState<Flag[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [creating, setCreating] = useState(false);
    const [analytics, setAnalytics] = useState<Record<string, FlagAnalytics>>({});

    // New flag form
    const [newName, setNewName] = useState("");
    const [newDesc, setNewDesc] = useState("");
    const [newRollout, setNewRollout] = useState(0);

    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

    const fetchFlags = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/api/v1/flags`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error("Failed to fetch flags");
            const data = await res.json();
            setFlags(data);
        } catch {
            setError("Failed to load feature flags");
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        fetchFlags();
    }, [fetchFlags]);

    const toggleFlag = async (flag: Flag) => {
        try {
            const res = await fetch(`${API_URL}/api/v1/flags/${flag.name}`, {
                method: "PATCH",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ is_enabled: !flag.is_enabled }),
            });
            if (!res.ok) throw new Error("Failed to toggle flag");
            await fetchFlags();
        } catch {
            setError("Failed to toggle flag");
        }
    };

    const updateRollout = async (flag: Flag, percentage: number) => {
        try {
            const res = await fetch(`${API_URL}/api/v1/flags/${flag.name}`, {
                method: "PATCH",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ rollout_percentage: percentage / 100 }),
            });
            if (!res.ok) throw new Error("Failed to update rollout");
            await fetchFlags();
        } catch {
            setError("Failed to update rollout");
        }
    };

    const createFlag = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        try {
            const res = await fetch(`${API_URL}/api/v1/flags`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name: newName.toLowerCase().replace(/\s+/g, "_"),
                    description: newDesc,
                    rollout_percentage: newRollout / 100,
                }),
            });
            if (!res.ok) throw new Error("Failed to create flag");
            setNewName("");
            setNewDesc("");
            setNewRollout(0);
            await fetchFlags();
        } catch {
            setError("Failed to create flag");
        } finally {
            setCreating(false);
        }
    };

    const deleteFlag = async (flagName: string) => {
        if (!confirm(`Delete flag "${flagName}"? This cannot be undone.`)) return;
        try {
            const res = await fetch(`${API_URL}/api/v1/flags/${flagName}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error("Failed to delete flag");
            await fetchFlags();
        } catch {
            setError("Failed to delete flag");
        }
    };

    const fetchAnalytics = async (flagName: string) => {
        try {
            const res = await fetch(`${API_URL}/api/v1/flags/${flagName}/analytics`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) return;
            const data = await res.json();
            setAnalytics((prev) => ({ ...prev, [flagName]: data }));
        } catch {
            // silently fail
        }
    };

    const rolloutPresets = [
        { label: "5%", value: 5 },
        { label: "25%", value: 25 },
        { label: "50%", value: 50 },
        { label: "100%", value: 100 },
    ];

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-950 text-white p-6">
            <div className="max-w-5xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                            Feature Flags
                        </h1>
                        <p className="text-gray-400 mt-1">Manage feature rollouts and canary deployments</p>
                    </div>
                    <span className="px-3 py-1 bg-emerald-900/40 text-emerald-400 rounded-full text-sm font-medium">
                        {flags.length} flags
                    </span>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300">
                        {error}
                        <button onClick={() => setError("")} className="ml-3 text-red-400 hover:text-red-200">✕</button>
                    </div>
                )}

                {/* Create New Flag */}
                <form onSubmit={createFlag} className="mb-8 p-6 bg-gray-900/60 backdrop-blur border border-gray-800 rounded-xl">
                    <h2 className="text-lg font-semibold mb-4 text-gray-200">Create Flag</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <input
                            type="text"
                            placeholder="flag_name (snake_case)"
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            pattern="^[a-z][a-z0-9_]*$"
                            required
                            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none"
                        />
                        <input
                            type="text"
                            placeholder="Description"
                            value={newDesc}
                            onChange={(e) => setNewDesc(e.target.value)}
                            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none"
                        />
                        <div className="flex gap-2">
                            <input
                                type="number"
                                min={0}
                                max={100}
                                value={newRollout}
                                onChange={(e) => setNewRollout(Number(e.target.value))}
                                placeholder="Rollout %"
                                className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none"
                            />
                            <button
                                type="submit"
                                disabled={creating || !newName}
                                className="px-6 py-2 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium rounded-lg hover:from-amber-400 hover:to-orange-500 disabled:opacity-50 transition-all"
                            >
                                {creating ? "..." : "Create"}
                            </button>
                        </div>
                    </div>
                </form>

                {/* Flags List */}
                <div className="space-y-4">
                    {flags.map((flag) => (
                        <div
                            key={flag.id}
                            className="p-5 bg-gray-900/60 backdrop-blur border border-gray-800 rounded-xl hover:border-gray-700 transition-colors"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3">
                                        <code className="text-lg font-mono text-white">{flag.name}</code>
                                        <button
                                            onClick={() => toggleFlag(flag)}
                                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${flag.is_enabled ? "bg-emerald-600" : "bg-gray-700"
                                                }`}
                                        >
                                            <span
                                                className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${flag.is_enabled ? "translate-x-6" : "translate-x-1"
                                                    }`}
                                            />
                                        </button>
                                        <span className={`text-xs font-medium ${flag.is_enabled ? "text-emerald-400" : "text-gray-500"}`}>
                                            {flag.is_enabled ? "ENABLED" : "DISABLED"}
                                        </span>
                                    </div>
                                    {flag.description && (
                                        <p className="text-gray-400 text-sm mt-1">{flag.description}</p>
                                    )}
                                </div>
                                <button
                                    onClick={() => deleteFlag(flag.name)}
                                    className="text-gray-600 hover:text-red-400 transition-colors ml-4"
                                    title="Delete flag"
                                >
                                    🗑️
                                </button>
                            </div>

                            {/* Rollout Controls */}
                            <div className="mt-4 flex items-center gap-3 flex-wrap">
                                <span className="text-xs text-gray-400 uppercase tracking-wide">Rollout:</span>
                                <div className="flex gap-1">
                                    {rolloutPresets.map(({ label, value }) => (
                                        <button
                                            key={value}
                                            onClick={() => updateRollout(flag, value)}
                                            className={`px-3 py-1 text-xs rounded-md transition-colors ${Math.round(flag.rollout_percentage * 100) === value
                                                    ? "bg-amber-600 text-white"
                                                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                                                }`}
                                        >
                                            {label}
                                        </button>
                                    ))}
                                </div>
                                <div className="flex-1 max-w-xs">
                                    <input
                                        type="range"
                                        min={0}
                                        max={100}
                                        value={Math.round(flag.rollout_percentage * 100)}
                                        onChange={(e) => updateRollout(flag, Number(e.target.value))}
                                        className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
                                    />
                                </div>
                                <span className="text-sm font-mono text-amber-400">
                                    {Math.round(flag.rollout_percentage * 100)}%
                                </span>
                            </div>

                            {/* Analytics */}
                            <div className="mt-3 flex items-center gap-4">
                                <button
                                    onClick={() => fetchAnalytics(flag.name)}
                                    className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                                >
                                    📊 View Analytics
                                </button>
                                {analytics[flag.name] && (
                                    <div className="flex gap-4 text-xs text-gray-400">
                                        <span>Total: <strong className="text-white">{analytics[flag.name].total_evaluations}</strong></span>
                                        <span>True: <strong className="text-emerald-400">{analytics[flag.name].true_count}</strong></span>
                                        <span>False: <strong className="text-red-400">{analytics[flag.name].false_count}</strong></span>
                                        <span>Rate: <strong className="text-amber-400">{analytics[flag.name].true_percentage}%</strong></span>
                                    </div>
                                )}
                            </div>

                            <div className="mt-2 text-xs text-gray-600">
                                Updated {new Date(flag.updated_at).toLocaleString()}
                            </div>
                        </div>
                    ))}

                    {flags.length === 0 && (
                        <div className="text-center py-16 text-gray-500">
                            <p className="text-4xl mb-3">🏴</p>
                            <p>No feature flags defined yet. Create one above to get started.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
