"use client";

import { useEffect, useRef, useState } from "react";
import { adminAPI } from "@/lib/adminAPI";
import type { MonitoringMetrics } from "@/types/admin";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  status?: "good" | "warn" | "bad" | "neutral";
}

function MetricCard({ label, value, unit, status = "neutral" }: MetricCardProps) {
  const statusColor = {
    good: "text-emerald-400",
    warn: "text-amber-400",
    bad: "text-red-400",
    neutral: "text-white",
  }[status];
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-gray-400 text-sm">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${statusColor}`}>
        {value}
        {unit && <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>}
      </p>
    </div>
  );
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default function AdminMonitoringPage() {
  const [metrics, setMetrics] = useState<MonitoringMetrics | null>(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function load() {
    setError("");
    try {
      const data = await adminAPI.getMonitoring();
      setMetrics(data);
      setLastUpdated(new Date());
    } catch {
      setError("Failed to load monitoring metrics");
    }
  }

  useEffect(() => {
    load();
    intervalRef.current = setInterval(load, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const dbStatus =
    !metrics ? "neutral"
    : metrics.db_latency_ms < 10 ? "good"
    : metrics.db_latency_ms < 50 ? "warn"
    : "bad";

  const redisStatus =
    !metrics ? "neutral"
    : metrics.redis_hit_rate > 80 ? "good"
    : metrics.redis_hit_rate > 50 ? "warn"
    : "bad";

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">System Monitoring</h1>
          <p className="text-gray-400 text-sm mt-1">
            Auto-refreshes every 5 seconds
            {lastUpdated && (
              <> · Last updated {lastUpdated.toLocaleTimeString()}</>
            )}
          </p>
        </div>
        <button
          onClick={load}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium transition-colors"
        >
          Refresh Now
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* WebSocket */}
      <section>
        <h2 className="text-gray-300 font-medium text-sm uppercase tracking-wide mb-3">
          WebSocket
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard
            label="Active Connections"
            value={metrics?.active_ws_connections ?? "—"}
            status={
              !metrics ? "neutral"
              : metrics.active_ws_connections > 0 ? "good"
              : "neutral"
            }
          />
        </div>
      </section>

      {/* Database */}
      <section>
        <h2 className="text-gray-300 font-medium text-sm uppercase tracking-wide mb-3">
          Database (PostgreSQL)
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard
            label="Query Latency"
            value={metrics?.db_latency_ms.toFixed(2) ?? "—"}
            unit="ms"
            status={dbStatus}
          />
        </div>
      </section>

      {/* Redis */}
      <section>
        <h2 className="text-gray-300 font-medium text-sm uppercase tracking-wide mb-3">
          Redis Cache
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard
            label="Connected Clients"
            value={metrics?.redis_connected_clients ?? "—"}
            status="neutral"
          />
          <MetricCard
            label="Memory Used"
            value={metrics?.redis_used_memory_mb.toFixed(2) ?? "—"}
            unit="MB"
            status="neutral"
          />
          <MetricCard
            label="Cache Hit Rate"
            value={
              metrics ? `${metrics.redis_hit_rate.toFixed(1)}%` : "—"
            }
            status={redisStatus}
          />
        </div>
      </section>

      {/* AI & Errors */}
      <section>
        <h2 className="text-gray-300 font-medium text-sm uppercase tracking-wide mb-3">
          AI & Errors
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard
            label="Groq API Calls Today"
            value={metrics?.groq_calls_today ?? "—"}
            status="neutral"
          />
          <MetricCard
            label="Error Events Today"
            value={metrics?.error_events_today ?? "—"}
            status={
              !metrics ? "neutral"
              : metrics.error_events_today === 0 ? "good"
              : metrics.error_events_today < 5 ? "warn"
              : "bad"
            }
          />
          <MetricCard
            label="Process Uptime"
            value={metrics ? formatUptime(metrics.uptime_seconds) : "—"}
            status="good"
          />
        </div>
      </section>

      {/* Status indicators legend */}
      <div className="flex gap-6 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> Good
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" /> Warning
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-400 inline-block" /> Critical
        </span>
      </div>
    </div>
  );
}
