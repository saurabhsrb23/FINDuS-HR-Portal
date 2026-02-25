"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { getSessionUser, type UserRole } from "@/lib/auth";
import { candidateAPI } from "@/lib/candidateAPI";
import { applicationAPI } from "@/lib/applicationAPI";
import { getAnalyticsSummary } from "@/lib/jobsAPI";
import type { ProfileStrength } from "@/types/candidate";
import type { AnalyticsSummary } from "@/types/job";
import LiveCounterBadge from "@/components/shared/LiveCounterBadge";
import LiveActivityFeed from "@/components/shared/LiveActivityFeed";
import { useRealtime } from "@/hooks/useRealtimeEvents";

const HR_ROLES = new Set<UserRole>([
  "hr", "hr_admin", "hiring_manager", "recruiter", "superadmin", "admin", "elite_admin",
]);

// ── Profile strength ring ──────────────────────────────────────────────────────
function StrengthRing({ score }: { score: number }) {
  const r = 28;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative w-20 h-20">
      <svg width="80" height="80" className="-rotate-90">
        <circle cx="40" cy="40" r={r} stroke="#e5e7eb" strokeWidth="6" fill="none" />
        <circle
          cx="40" cy="40" r={r}
          stroke={color} strokeWidth="6" fill="none"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-800">
        {score}%
      </span>
    </div>
  );
}

// ── Toast notification (candidate) ────────────────────────────────────────────
interface Toast {
  id: number;
  message: string;
  icon: string;
}

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  if (!toasts.length) return null;
  return (
    <div className="fixed bottom-6 right-6 flex flex-col gap-2 z-50">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="flex items-center gap-2 bg-white border border-gray-200 shadow-lg rounded-lg px-4 py-3 text-sm text-gray-800 animate-slide-in"
        >
          <span>{t.icon}</span>
          <span>{t.message}</span>
          <button onClick={() => onDismiss(t.id)} className="ml-2 text-gray-400 hover:text-gray-600 text-xs">
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [role, setRole] = useState<UserRole | null>(null);
  const [name, setName] = useState("");
  const [strength, setStrength] = useState<ProfileStrength | null>(null);
  const [appCount, setAppCount] = useState<number | null>(null);
  const [jobCount, setJobCount] = useState<number | null>(null);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastIdRef = useRef(0);

  const { subscribe, unsubscribe, events } = useRealtime();

  useEffect(() => {
    const session = getSessionUser();
    if (session) {
      setRole(session.role as UserRole);
      setName(session.email.split("@")[0] ?? session.email);
    }
  }, []);

  // Load candidate-specific data
  useEffect(() => {
    if (!role || HR_ROLES.has(role)) return;
    Promise.all([
      candidateAPI.getStrength().then(r => setStrength(r.data)).catch(() => {}),
      applicationAPI.getMyApplications().then(r => setAppCount(r.data.length)).catch(() => {}),
      applicationAPI.searchJobs({ limit: 1 }).then(r => setJobCount(r.data.total)).catch(() => {}),
    ]);
  }, [role]);

  // Load HR analytics summary
  useEffect(() => {
    if (!role || !HR_ROLES.has(role)) return;
    getAnalyticsSummary().then(setSummary).catch(() => {});
  }, [role]);

  // Candidate: show toast when profile is viewed or status changes
  const addToast = useCallback((message: string, icon: string) => {
    const id = ++toastIdRef.current;
    setToasts(prev => [...prev, { id, message, icon }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 5000);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!role || HR_ROLES.has(role)) return;

    const onProfileViewed = () => addToast("An HR viewed your profile!", "👀");
    const onShortlisted = () => addToast("You've been shortlisted for a job!", "🎉");
    const onInterview = () => addToast("Interview scheduled — check your applications.", "📅");
    const onNewJob = () => setJobCount(prev => (prev !== null ? prev + 1 : prev));

    subscribe("profile_viewed", onProfileViewed);
    subscribe("shortlisted", onShortlisted);
    subscribe("interview_scheduled", onInterview);
    subscribe("new_job_posted", onNewJob);

    return () => {
      unsubscribe("profile_viewed", onProfileViewed);
      unsubscribe("shortlisted", onShortlisted);
      unsubscribe("interview_scheduled", onInterview);
      unsubscribe("new_job_posted", onNewJob);
    };
  }, [role, subscribe, unsubscribe, addToast]);

  const isHR = role && HR_ROLES.has(role);

  return (
    <div className="p-8 max-w-5xl">
      <h1 className="text-2xl font-bold text-gray-900">
        Welcome back, {name || "there"}!
      </h1>
      <p className="mt-1 text-sm text-gray-500 capitalize">
        Role: <span className="font-medium text-indigo-600">{role?.replace(/_/g, " ") ?? "—"}</span>
      </p>

      {isHR ? (
        <>
          <p className="mt-4 text-gray-600">Manage your hiring pipeline from here.</p>

          {/* Live KPI cards */}
          <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Link
              href="/dashboard/jobs"
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md hover:border-indigo-300 transition-all group"
            >
              <LiveCounterBadge
                value={summary?.total_jobs ?? null}
                label="Total Jobs"
                icon="💼"
                onUpdate={(v) => setSummary(prev => prev ? { ...prev, total_jobs: v } : prev)}
              />
              <p className="text-xs text-indigo-500 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">View jobs →</p>
            </Link>
            <Link
              href="/dashboard/jobs?status=active"
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md hover:border-green-300 transition-all group"
            >
              <LiveCounterBadge
                value={summary?.active_jobs ?? null}
                label="Active Jobs"
                icon="🟢"
                colorClass="text-green-600"
                eventTypes={["new_job_posted"]}
                onUpdate={(v) => setSummary(prev => prev ? { ...prev, active_jobs: v } : prev)}
              />
              <p className="text-xs text-green-500 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">View active →</p>
            </Link>
            <Link
              href="/dashboard/applications"
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md hover:border-indigo-300 transition-all group"
            >
              <LiveCounterBadge
                value={summary?.total_applications ?? null}
                label="Applications"
                icon="📄"
                colorClass="text-indigo-600"
                eventTypes={["new_application"]}
                onUpdate={(v) => setSummary(prev => prev ? { ...prev, total_applications: v } : prev)}
              />
              <p className="text-xs text-indigo-500 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">View all →</p>
            </Link>
            <Link
              href="/dashboard/analytics"
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md hover:border-purple-300 transition-all group"
            >
              <LiveCounterBadge
                value={summary?.total_views ?? null}
                label="Job Views"
                icon="👁️"
                colorClass="text-purple-600"
              />
              <p className="text-xs text-purple-500 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">View analytics →</p>
            </Link>
          </div>

          {/* Two-column: quick links + live feed */}
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 content-start">
              <Link
                href="/dashboard/jobs"
                className="flex flex-col gap-1 p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
              >
                <span className="text-2xl">💼</span>
                <span className="font-semibold text-gray-900">Job Postings</span>
                <span className="text-sm text-gray-500">Create and manage jobs</span>
              </Link>
              <Link
                href="/dashboard/search"
                className="flex flex-col gap-1 p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
              >
                <span className="text-2xl">🔎</span>
                <span className="font-semibold text-gray-900">Find Candidates</span>
                <span className="text-sm text-gray-500">Search the talent pool</span>
              </Link>
              <Link
                href="/dashboard/analytics"
                className="flex flex-col gap-1 p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow sm:col-span-2"
              >
                <span className="text-2xl">📊</span>
                <span className="font-semibold text-gray-900">Analytics</span>
                <span className="text-sm text-gray-500">Recruiter metrics &amp; insights</span>
              </Link>
            </div>

            {/* Live activity feed */}
            <LiveActivityFeed events={events} maxHeight="260px" title="Live Activity" />
          </div>
        </>
      ) : (
        <>
          <p className="mt-4 text-gray-600">Your career dashboard — find jobs and track your progress.</p>

          {/* Stats row */}
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Profile strength */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex items-center gap-4">
              {strength ? (
                <>
                  <StrengthRing score={strength.score} />
                  <div>
                    <p className="text-xs text-gray-500">Profile Strength</p>
                    <p className="text-sm font-semibold text-gray-900 mt-0.5">
                      {strength.score >= 80 ? "Excellent" : strength.score >= 50 ? "Good" : "Needs work"}
                    </p>
                    <Link href="/dashboard/profile" className="text-xs text-indigo-600 hover:underline mt-1 block">
                      Improve profile →
                    </Link>
                  </div>
                </>
              ) : (
                <div>
                  <p className="text-xs text-gray-500">Profile Strength</p>
                  <Link href="/dashboard/profile" className="text-sm font-medium text-indigo-600 hover:underline mt-1 block">
                    Complete your profile →
                  </Link>
                </div>
              )}
            </div>

            {/* Active applications — live counter */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <LiveCounterBadge
                value={appCount}
                label="My Applications"
                icon="📄"
                colorClass="text-indigo-600"
              />
              <Link href="/dashboard/my-applications" className="text-xs text-indigo-600 hover:underline mt-2 block">
                View all →
              </Link>
            </div>

            {/* Open jobs — live counter */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <LiveCounterBadge
                value={jobCount}
                label="Open Positions"
                icon="💼"
                eventTypes={["new_job_posted"]}
                onUpdate={setJobCount}
              />
              <Link href="/dashboard/browse-jobs" className="text-xs text-indigo-600 hover:underline mt-2 block">
                Browse jobs →
              </Link>
            </div>
          </div>

          {/* Quick actions */}
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link
              href="/dashboard/browse-jobs"
              className="flex flex-col gap-2 p-5 bg-indigo-600 text-white rounded-xl shadow-sm hover:bg-indigo-700 transition-colors"
            >
              <span className="text-2xl">🔍</span>
              <span className="font-semibold">Browse Jobs</span>
              <span className="text-sm text-indigo-200">Find your next opportunity</span>
            </Link>
            <Link
              href="/dashboard/profile"
              className="flex flex-col gap-2 p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
            >
              <span className="text-2xl">👤</span>
              <span className="font-semibold text-gray-900">Complete Profile</span>
              <span className="text-sm text-gray-500">Add resume, skills, experience</span>
            </Link>
            <Link
              href="/dashboard/my-applications"
              className="flex flex-col gap-2 p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
            >
              <span className="text-2xl">📄</span>
              <span className="font-semibold text-gray-900">Track Applications</span>
              <span className="text-sm text-gray-500">Monitor your application status</span>
            </Link>
            <Link
              href="/dashboard/job-alerts"
              className="flex flex-col gap-2 p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
            >
              <span className="text-2xl">🔔</span>
              <span className="font-semibold text-gray-900">Job Alerts</span>
              <span className="text-sm text-gray-500">Get daily job digest emails</span>
            </Link>
          </div>

          {/* Tips from profile strength */}
          {strength && strength.tips.length > 0 && (
            <div className="mt-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-amber-800 mb-2">Boost your profile:</p>
              <ul className="space-y-1">
                {strength.tips.map((tip, i) => (
                  <li key={i} className="text-sm text-amber-700 flex items-start gap-2">
                    <span className="mt-0.5">•</span> {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Toast notifications (candidate only) */}
      <ToastContainer toasts={toasts} onDismiss={(id) => setToasts(prev => prev.filter(t => t.id !== id))} />
    </div>
  );
}
