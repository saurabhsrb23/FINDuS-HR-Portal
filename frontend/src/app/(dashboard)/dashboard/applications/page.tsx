"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listJobs, getJobApplicants, updateApplicationStatus, type HRApplicant } from "@/lib/jobsAPI";
import type { JobListItem } from "@/types/job";

const STATUS_OPTIONS = [
  { value: "applied",   label: "Applied",   color: "bg-blue-100 text-blue-700" },
  { value: "screening", label: "Screening", color: "bg-yellow-100 text-yellow-700" },
  { value: "interview", label: "Interview", color: "bg-purple-100 text-purple-700" },
  { value: "offer",     label: "Offer",     color: "bg-green-100 text-green-700" },
  { value: "hired",     label: "Hired",     color: "bg-emerald-100 text-emerald-700" },
  { value: "rejected",  label: "Rejected",  color: "bg-red-100 text-red-700" },
  { value: "withdrawn", label: "Withdrawn", color: "bg-gray-100 text-gray-500" },
];

function statusColor(s: string) {
  return STATUS_OPTIONS.find((o) => o.value === s)?.color ?? "bg-gray-100 text-gray-600";
}
function statusLabel(s: string) {
  return STATUS_OPTIONS.find((o) => o.value === s)?.label ?? s;
}

interface ApplicantRow extends HRApplicant {
  job_title: string;
  job_id_str: string;
}

export default function AllApplicationsPage() {
  const [rows, setRows] = useState<ApplicantRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<ApplicantRow | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const jobsRes = await listJobs({ page: 1, page_size: 100 });
        const jobs: JobListItem[] = jobsRes.items;
        const allRows: ApplicantRow[] = [];
        await Promise.all(
          jobs.map(async (job) => {
            try {
              const applicants = await getJobApplicants(job.id);
              applicants.forEach((a) =>
                allRows.push({ ...a, job_title: job.title, job_id_str: job.id })
              );
            } catch {
              // job may have 0 applicants — skip silently
            }
          })
        );
        // Sort newest first
        allRows.sort((a, b) => new Date(b.applied_at).getTime() - new Date(a.applied_at).getTime());
        setRows(allRows);
        if (allRows.length > 0) setSelected(allRows[0]!);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleStatusChange(appId: string, newStatus: string) {
    setUpdating(appId);
    try {
      await updateApplicationStatus(appId, newStatus);
      setRows((prev) => prev.map((r) => (r.id === appId ? { ...r, status: newStatus } : r)));
      if (selected?.id === appId) setSelected((s) => s ? { ...s, status: newStatus } : s);
      showToast("Status updated");
    } catch {
      showToast("Failed to update status");
    } finally {
      setUpdating(null);
    }
  }

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  const filtered = rows.filter((r) => {
    if (statusFilter && r.status !== statusFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        r.candidate_name?.toLowerCase().includes(q) ||
        r.candidate_email?.toLowerCase().includes(q) ||
        r.job_title?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white px-4 py-2 rounded-lg text-sm shadow-lg">
          {toast}
        </div>
      )}

      {/* Left panel */}
      <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col">
        <div className="px-4 py-3 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">All Applications</h2>
          <p className="text-xs text-gray-500 mt-0.5">{rows.length} total</p>
        </div>

        {/* Filters */}
        <div className="px-4 py-2 space-y-2 border-b border-gray-100">
          <input
            type="text"
            placeholder="Search name, email, job…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-6 text-sm text-gray-400 text-center">Loading…</div>
          ) : filtered.length === 0 ? (
            <div className="p-6 text-sm text-gray-400 text-center">No applications found.</div>
          ) : (
            filtered.map((row) => (
              <button
                key={row.id}
                onClick={() => setSelected(row)}
                className={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                  selected?.id === row.id ? "bg-indigo-50 border-l-2 border-l-indigo-500" : ""
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-sm text-gray-900 truncate">
                    {row.candidate_name ?? "Unknown"}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${statusColor(row.status)}`}>
                    {statusLabel(row.status)}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{row.job_title}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(row.applied_at).toLocaleDateString("en-IN", {
                    day: "numeric", month: "short", year: "numeric",
                  })}
                </p>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right panel — detail */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {!selected ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            Select an application to view details
          </div>
        ) : (
          <div className="max-w-3xl mx-auto p-6 space-y-5">
            {/* Header */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    {selected.candidate_name ?? "Unknown Candidate"}
                  </h3>
                  {selected.candidate_headline && (
                    <p className="text-sm text-gray-600 mt-0.5">{selected.candidate_headline}</p>
                  )}
                  <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-500">
                    {selected.candidate_email && (
                      <a href={`mailto:${selected.candidate_email}`} className="hover:text-indigo-600">
                        {selected.candidate_email}
                      </a>
                    )}
                    {selected.candidate_location && <span>{selected.candidate_location}</span>}
                    {selected.candidate_years_exp != null && (
                      <span>{selected.candidate_years_exp} yr{selected.candidate_years_exp !== 1 ? "s" : ""} exp</span>
                    )}
                  </div>
                  <div className="mt-2">
                    <span className="text-xs text-gray-400">Applied for: </span>
                    <Link
                      href={`/dashboard/jobs/${selected.job_id_str}/applicants`}
                      className="text-xs text-indigo-600 hover:underline font-medium"
                    >
                      {selected.job_title}
                    </Link>
                  </div>
                </div>

                {/* Status selector */}
                <div className="flex flex-col items-end gap-2">
                  <select
                    value={selected.status}
                    disabled={updating === selected.id || selected.status === "withdrawn"}
                    onChange={(e) => handleStatusChange(selected.id, e.target.value)}
                    className={`text-sm border rounded-lg px-3 py-1.5 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-300 ${statusColor(selected.status)}`}
                  >
                    {STATUS_OPTIONS.filter((s) => s.value !== "withdrawn").map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                  {updating === selected.id && (
                    <span className="text-xs text-gray-400">Saving…</span>
                  )}
                </div>
              </div>

              {/* Skills */}
              {selected.candidate_skills.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-4">
                  {selected.candidate_skills.map((skill) => (
                    <span key={skill} className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 flex-wrap">
              {selected.resume_url && (
                <a
                  href={selected.resume_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 font-medium"
                >
                  Download Resume
                </a>
              )}
              <Link
                href={`/dashboard/jobs/${selected.job_id_str}/ai-tools`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg hover:bg-indigo-100 font-medium"
              >
                AI Match Score
              </Link>
              {selected.candidate_email && (
                <a
                  href={`mailto:${selected.candidate_email}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 font-medium"
                >
                  Email Candidate
                </a>
              )}
              <Link
                href={`/dashboard/jobs/${selected.job_id_str}/applicants`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 font-medium"
              >
                View Job Applicants
              </Link>
            </div>

            {/* Cover letter */}
            {selected.cover_letter && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Cover Letter</h4>
                <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {selected.cover_letter}
                </p>
              </div>
            )}

            {/* Answers */}
            {selected.answers.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Questionnaire Answers</h4>
                <div className="space-y-3">
                  {selected.answers.map((ans, i) => (
                    <div key={ans.id} className="text-sm">
                      <p className="text-gray-500 text-xs mb-0.5">Q{i + 1}</p>
                      <p className="text-gray-800">{ans.answer_text ?? "—"}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timeline */}
            {selected.timeline && selected.timeline.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Application Timeline</h4>
                <div className="space-y-3">
                  {selected.timeline.map((event, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className={`w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0 ${statusColor(event.status).split(" ")[0]}`} />
                        {i < selected.timeline!.length - 1 && (
                          <div className="w-0.5 bg-gray-200 flex-1 mt-1" />
                        )}
                      </div>
                      <div className="pb-3">
                        <p className="text-sm font-medium text-gray-800 capitalize">{event.status}</p>
                        {event.note && <p className="text-xs text-gray-500">{event.note}</p>}
                        <p className="text-xs text-gray-400 mt-0.5">
                          {new Date(event.timestamp).toLocaleString("en-IN", {
                            day: "numeric", month: "short", year: "numeric",
                            hour: "2-digit", minute: "2-digit",
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
