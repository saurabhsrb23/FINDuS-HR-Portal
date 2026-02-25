"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getJob } from "@/lib/jobsAPI";
import { getJobApplicants, updateApplicationStatus, type HRApplicant } from "@/lib/jobsAPI";
import type { Job } from "@/types/job";

const STATUS_OPTIONS = [
  { value: "applied", label: "Applied", color: "bg-blue-100 text-blue-700" },
  { value: "screening", label: "Screening", color: "bg-yellow-100 text-yellow-700" },
  { value: "interview", label: "Interview", color: "bg-purple-100 text-purple-700" },
  { value: "offer", label: "Offer", color: "bg-green-100 text-green-700" },
  { value: "hired", label: "Hired", color: "bg-emerald-100 text-emerald-700" },
  { value: "rejected", label: "Rejected", color: "bg-red-100 text-red-700" },
  { value: "withdrawn", label: "Withdrawn", color: "bg-gray-100 text-gray-500" },
];

function statusColor(status: string) {
  return STATUS_OPTIONS.find((s) => s.value === status)?.color ?? "bg-gray-100 text-gray-500";
}
function statusLabel(status: string) {
  return STATUS_OPTIONS.find((s) => s.value === status)?.label ?? status;
}

export default function ApplicantsPage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [applicants, setApplicants] = useState<HRApplicant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<HRApplicant | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [updating, setUpdating] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getJob(id), getJobApplicants(id)])
      .then(([j, apps]) => {
        setJob(j);
        setApplicants(apps);
        if (apps.length > 0) setSelected(apps[0]!);
      })
      .catch(() => setError("Failed to load applicants."))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleStatusChange(appId: string, newStatus: string) {
    setUpdating(appId);
    try {
      await updateApplicationStatus(appId, newStatus);
      setApplicants((prev) =>
        prev.map((a) => (a.id === appId ? { ...a, status: newStatus } : a))
      );
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

  const filtered = statusFilter
    ? applicants.filter((a) => a.status === statusFilter)
    : applicants;

  if (loading) return <div className="p-8 text-gray-400">Loading…</div>;
  if (error) return <div className="p-8 text-red-600">{error}</div>;

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white px-4 py-2 rounded-lg text-sm shadow-lg">
          {toast}
        </div>
      )}

      {/* Left panel — applicant list */}
      <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/dashboard/jobs"
              className="text-gray-400 hover:text-gray-600 text-sm"
            >
              ← Jobs
            </Link>
          </div>
          <h2 className="font-semibold text-gray-900 truncate">{job?.title}</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {applicants.length} applicant{applicants.length !== 1 ? "s" : ""}
          </p>
        </div>

        {/* Status filter */}
        <div className="px-4 py-2 border-b border-gray-100">
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
          {filtered.length === 0 ? (
            <div className="px-4 py-8 text-sm text-gray-400 text-center">No applicants found.</div>
          ) : (
            filtered.map((app) => (
              <button
                key={app.id}
                onClick={() => setSelected(app)}
                className={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                  selected?.id === app.id ? "bg-indigo-50 border-l-2 border-l-indigo-500" : ""
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-sm text-gray-900 truncate">
                    {app.candidate_name ?? "Unknown"}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${statusColor(app.status)}`}>
                    {statusLabel(app.status)}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{app.candidate_headline ?? app.candidate_email ?? ""}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(app.applied_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                </p>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right panel — applicant detail */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {!selected ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            Select an applicant to view details
          </div>
        ) : (
          <div className="max-w-3xl mx-auto p-6 space-y-5">
            {/* Candidate header */}
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

            {/* Quick actions */}
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
                href={`/dashboard/jobs/${id}/ai-tools`}
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

            {/* Questionnaire answers */}
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
