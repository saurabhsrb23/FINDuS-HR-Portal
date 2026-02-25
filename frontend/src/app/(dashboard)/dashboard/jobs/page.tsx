"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { cloneJob, deleteJob, listJobs, pauseJob, publishJob } from "@/lib/jobsAPI";
import type { JobListItem, JobStatus, JobType } from "@/types/job";
import { JOB_STATUS_COLORS, JOB_STATUS_LABELS, JOB_TYPE_LABELS } from "@/types/job";

const STATUS_FILTERS: Array<{ label: string; value: JobStatus | "" }> = [
  { label: "All", value: "" },
  { label: "Draft", value: "draft" },
  { label: "Active", value: "active" },
  { label: "Paused", value: "paused" },
  { label: "Closed", value: "closed" },
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<JobStatus | "">("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const PAGE_SIZE = 20;

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listJobs({
        status: statusFilter || undefined,
        search: search || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setJobs(res.items);
      setTotal(res.total);
    } catch {
      setError("Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, search, page]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  async function handlePublish(id: string) {
    await publishJob(id);
    fetchJobs();
  }

  async function handlePause(id: string) {
    await pauseJob(id);
    fetchJobs();
  }

  async function handleClone(id: string) {
    await cloneJob(id);
    fetchJobs();
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this job? This cannot be undone.")) return;
    await deleteJob(id);
    fetchJobs();
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Postings</h1>
          <p className="text-sm text-gray-500 mt-1">{total} total jobs</p>
        </div>
        <Link
          href="/dashboard/jobs/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          + New Job
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => {
                setStatusFilter(f.value);
                setPage(1);
              }}
              className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                statusFilter === f.value
                  ? "bg-indigo-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Search jobs…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="flex-1 min-w-48 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
      </div>

      {/* Content */}
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg mb-4">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-gray-400">Loading…</div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-500 mb-4">No jobs found.</p>
          <Link
            href="/dashboard/jobs/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
          >
            Create your first job
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <JobRow
              key={job.id}
              job={job}
              onPublish={handlePublish}
              onPause={handlePause}
              onClone={handleClone}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <p className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── JobRow sub-component ─────────────────────────────────────────────────────

function JobRow({
  job,
  onPublish,
  onPause,
  onClone,
  onDelete,
}: {
  job: JobListItem;
  onPublish: (id: string) => void;
  onPause: (id: string) => void;
  onClone: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="flex items-center gap-4 bg-white border border-gray-200 rounded-xl px-5 py-4 hover:shadow-sm transition-shadow">
      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <Link
            href={`/dashboard/jobs/${job.id}/edit`}
            className="font-semibold text-gray-900 hover:text-indigo-600 truncate"
          >
            {job.title}
          </Link>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${JOB_STATUS_COLORS[job.status]}`}
          >
            {JOB_STATUS_LABELS[job.status]}
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-0.5 truncate">
          {[
            job.department,
            job.location,
            JOB_TYPE_LABELS[job.job_type as JobType],
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      </div>

      {/* Metrics */}
      <div className="hidden sm:flex items-center gap-5 text-sm text-gray-500 flex-shrink-0">
        <span title="Views">👁 {job.views_count}</span>
        <span title="Applications">📋 {job.applications_count}</span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 flex-shrink-0">
        {job.status === "draft" && (
          <button
            onClick={() => onPublish(job.id)}
            className="px-2.5 py-1 text-xs bg-green-50 text-green-700 rounded-lg hover:bg-green-100 font-medium"
          >
            Publish
          </button>
        )}
        {job.status === "active" && (
          <button
            onClick={() => onPause(job.id)}
            className="px-2.5 py-1 text-xs bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 font-medium"
          >
            Pause
          </button>
        )}
        <Link
          href={`/dashboard/jobs/${job.id}/pipeline`}
          className="px-2.5 py-1 text-xs bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 font-medium"
        >
          Pipeline
        </Link>
        <Link
          href={`/dashboard/jobs/${job.id}/questionnaire`}
          className="px-2.5 py-1 text-xs bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 font-medium"
        >
          Questions
        </Link>
        <button
          onClick={() => onClone(job.id)}
          className="px-2.5 py-1 text-xs bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 font-medium"
        >
          Clone
        </button>
        {(job.status === "draft" || job.status === "closed") && (
          <button
            onClick={() => onDelete(job.id)}
            className="px-2.5 py-1 text-xs bg-red-50 text-red-700 rounded-lg hover:bg-red-100 font-medium"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
