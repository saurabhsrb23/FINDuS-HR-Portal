"use client";

import { useEffect, useState } from "react";
import { adminAPI } from "@/lib/adminAPI";
import type { PlatformOverview } from "@/types/admin";
import { LiveMetricsGrid } from "@/components/admin/LiveMetricsGrid";
import { RealTimeEventFeed } from "@/components/admin/RealTimeEventFeed";

interface KPICardProps {
  label: string;
  value: number | string;
  sub?: string;
  color?: string;
}

function KPICard({ label, value, sub, color = "indigo" }: KPICardProps) {
  const colorMap: Record<string, string> = {
    indigo: "text-indigo-400",
    emerald: "text-emerald-400",
    amber: "text-amber-400",
    rose: "text-rose-400",
    sky: "text-sky-400",
  };
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-gray-400 text-sm">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${colorMap[color] ?? "text-indigo-400"}`}>
        {value}
      </p>
      {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminDashboardPage() {
  const [overview, setOverview] = useState<PlatformOverview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    adminAPI
      .getPlatformOverview()
      .then(setOverview)
      .catch(() => setError("Failed to load platform overview"));
  }, []);

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Platform Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Real-time overview of the DoneHR platform</p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* KPI Grid */}
      {overview ? (
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <KPICard label="Total Users" value={overview.total_users} color="indigo" />
          <KPICard
            label="Candidates"
            value={overview.total_candidates}
            sub={`${overview.total_hr_users} HR users`}
            color="sky"
          />
          <KPICard
            label="Jobs Posted"
            value={overview.total_jobs}
            sub={`${overview.active_jobs} active`}
            color="emerald"
          />
          <KPICard label="Applications" value={overview.total_applications} color="amber" />
          <KPICard label="Companies" value={overview.total_companies} color="indigo" />
          <KPICard
            label="Live Connections"
            value={overview.active_ws_connections}
            sub="WebSocket"
            color="emerald"
          />
          <KPICard
            label="Events Today"
            value={overview.platform_events_today}
            color="rose"
          />
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-5 animate-pulse">
              <div className="h-4 bg-gray-800 rounded w-2/3 mb-2" />
              <div className="h-8 bg-gray-800 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Live Metrics with Recharts sparklines */}
      <LiveMetricsGrid />

      {/* Real-time event feed */}
      <RealTimeEventFeed />
    </div>
  );
}
