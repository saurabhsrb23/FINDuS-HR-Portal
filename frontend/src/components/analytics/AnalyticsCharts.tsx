"use client";

/**
 * AnalyticsCharts — pure presentational components for recruiter analytics.
 * Uses CSS-only horizontal bar charts (no external chart library needed).
 */

import type { AnalyticsSummary, JobCountByStatus, JobCountByType } from "@/types/job";

interface AnalyticsChartsProps {
  data: AnalyticsSummary;
}

export function AnalyticsCharts({ data }: AnalyticsChartsProps) {
  return (
    <div className="space-y-6">
      <SummaryCards data={data} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StatusChart byStatus={data.by_status} />
        <TypeChart byType={data.by_type} />
      </div>
      {data.top_jobs.length > 0 && <TopJobsTable jobs={data.top_jobs} />}
    </div>
  );
}

// ── Summary cards ────────────────────────────────────────────────────────────

function SummaryCards({ data }: { data: AnalyticsSummary }) {
  const cards = [
    { label: "Total Jobs", value: data.total_jobs, icon: "💼", color: "bg-blue-50 text-blue-700" },
    { label: "Active Jobs", value: data.active_jobs, icon: "✅", color: "bg-green-50 text-green-700" },
    { label: "Applications", value: data.total_applications, icon: "📋", color: "bg-purple-50 text-purple-700" },
    { label: "Total Views", value: data.total_views, icon: "👁", color: "bg-orange-50 text-orange-700" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div key={c.label} className={`rounded-xl p-4 ${c.color}`}>
          <div className="text-2xl mb-1">{c.icon}</div>
          <div className="text-2xl font-bold">{c.value.toLocaleString()}</div>
          <div className="text-sm font-medium opacity-80 mt-0.5">{c.label}</div>
        </div>
      ))}
    </div>
  );
}

// ── Status chart ─────────────────────────────────────────────────────────────

function StatusChart({ byStatus }: { byStatus: JobCountByStatus }) {
  const bars = [
    { label: "Draft", value: byStatus.draft, color: "#94a3b8" },
    { label: "Active", value: byStatus.active, color: "#22c55e" },
    { label: "Paused", value: byStatus.paused, color: "#eab308" },
    { label: "Closed", value: byStatus.closed, color: "#ef4444" },
  ];
  const max = Math.max(...bars.map((b) => b.value), 1);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Jobs by Status</h3>
      <div className="space-y-3">
        {bars.map((b) => (
          <HorizontalBar key={b.label} {...b} max={max} />
        ))}
      </div>
    </div>
  );
}

// ── Type chart ────────────────────────────────────────────────────────────────

function TypeChart({ byType }: { byType: JobCountByType }) {
  const bars = [
    { label: "Full Time", value: byType.full_time, color: "#6366f1" },
    { label: "Part Time", value: byType.part_time, color: "#60a5fa" },
    { label: "Contract", value: byType.contract, color: "#a78bfa" },
    { label: "Internship", value: byType.internship, color: "#f472b6" },
    { label: "Remote", value: byType.remote, color: "#2dd4bf" },
  ];
  const max = Math.max(...bars.map((b) => b.value), 1);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Jobs by Type</h3>
      <div className="space-y-3">
        {bars.map((b) => (
          <HorizontalBar key={b.label} {...b} max={max} />
        ))}
      </div>
    </div>
  );
}

// ── Shared bar component ──────────────────────────────────────────────────────

function HorizontalBar({
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
      <div className="flex items-center justify-between text-sm mb-1.5">
        <span className="text-gray-600">{label}</span>
        <span className="font-semibold text-gray-900 tabular-nums">{value}</span>
      </div>
      <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// ── Top jobs table ────────────────────────────────────────────────────────────

function TopJobsTable({
  jobs,
}: {
  jobs: AnalyticsSummary["top_jobs"];
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">
        Top Performing Jobs
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
              <th className="pb-2 font-medium">Title</th>
              <th className="pb-2 font-medium text-center">Applications</th>
              <th className="pb-2 font-medium text-center">Views</th>
              <th className="pb-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr
                key={job.id}
                className="border-b border-gray-50 last:border-0 hover:bg-gray-50"
              >
                <td className="py-2.5 pr-4">
                  <p className="font-medium text-gray-800 truncate max-w-48">
                    {job.title}
                  </p>
                  {job.department && (
                    <p className="text-xs text-gray-400 mt-0.5">{job.department}</p>
                  )}
                </td>
                <td className="py-2.5 text-center font-semibold text-gray-800">
                  {job.applications_count}
                </td>
                <td className="py-2.5 text-center text-gray-600">
                  {job.views_count}
                </td>
                <td className="py-2.5">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      job.status === "active"
                        ? "bg-green-100 text-green-700"
                        : job.status === "paused"
                        ? "bg-yellow-100 text-yellow-700"
                        : job.status === "draft"
                        ? "bg-gray-100 text-gray-600"
                        : "bg-red-100 text-red-600"
                    }`}
                  >
                    {job.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
