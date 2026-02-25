"use client";

import { useEffect, useState } from "react";

import { getAnalyticsSummary } from "@/lib/jobsAPI";
import type { AnalyticsSummary } from "@/types/job";

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalyticsSummary()
      .then(setData)
      .catch(() => setError("Failed to load analytics."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-gray-500">Loading…</div>;
  if (error || !data)
    return <div className="p-8 text-red-600">{error ?? "No data"}</div>;

  const statusBars = [
    { label: "Draft", value: data.by_status.draft, color: "bg-gray-400" },
    { label: "Active", value: data.by_status.active, color: "bg-green-500" },
    { label: "Paused", value: data.by_status.paused, color: "bg-yellow-400" },
    { label: "Closed", value: data.by_status.closed, color: "bg-red-400" },
  ];

  const typeBars = [
    { label: "Full Time", value: data.by_type.full_time, color: "bg-indigo-500" },
    { label: "Part Time", value: data.by_type.part_time, color: "bg-blue-400" },
    { label: "Contract", value: data.by_type.contract, color: "bg-purple-400" },
    { label: "Internship", value: data.by_type.internship, color: "bg-pink-400" },
    { label: "Remote", value: data.by_type.remote, color: "bg-teal-400" },
  ];

  const maxStatus = Math.max(...statusBars.map((b) => b.value), 1);
  const maxType = Math.max(...typeBars.map((b) => b.value), 1);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Recruiter Analytics</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Total Jobs" value={data.total_jobs} icon="💼" />
        <StatCard label="Active Jobs" value={data.active_jobs} icon="✅" />
        <StatCard label="Total Applications" value={data.total_applications} icon="📋" />
        <StatCard label="Total Views" value={data.total_views} icon="👁" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <ChartCard title="Jobs by Status">
          {statusBars.map((b) => (
            <BarRow key={b.label} {...b} max={maxStatus} />
          ))}
        </ChartCard>

        <ChartCard title="Jobs by Type">
          {typeBars.map((b) => (
            <BarRow key={b.label} {...b} max={maxType} />
          ))}
        </ChartCard>
      </div>

      {/* Top jobs */}
      {data.top_jobs.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-base font-semibold text-gray-900 mb-4">
            Top Performing Jobs
          </h2>
          <div className="space-y-2">
            {data.top_jobs.map((job) => (
              <div
                key={job.id}
                className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
              >
                <div>
                  <p className="text-sm font-medium text-gray-800">{job.title}</p>
                  <p className="text-xs text-gray-500">
                    {job.department ?? "—"} · {job.location ?? "Remote"}
                  </p>
                </div>
                <div className="flex gap-4 text-sm text-gray-500">
                  <span title="Applications">📋 {job.applications_count}</span>
                  <span title="Views">👁 {job.views_count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: string;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h2 className="text-base font-semibold text-gray-900 mb-4">{title}</h2>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function BarRow({
  label,
  value,
  color,
  max,
}: {
  label: string;
  value: number;
  color: string;
  max: number;
}) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="font-medium text-gray-900">{value}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
