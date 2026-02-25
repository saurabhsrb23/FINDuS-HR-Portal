"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getSessionUser, type UserRole } from "@/lib/auth";
import { candidateAPI } from "@/lib/candidateAPI";
import { applicationAPI } from "@/lib/applicationAPI";
import type { ProfileStrength } from "@/types/candidate";

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

export default function DashboardPage() {
  const [role, setRole] = useState<UserRole | null>(null);
  const [name, setName] = useState("");
  const [strength, setStrength] = useState<ProfileStrength | null>(null);
  const [appCount, setAppCount] = useState<number | null>(null);
  const [jobCount, setJobCount] = useState<number | null>(null);

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

  const isHR = role && HR_ROLES.has(role);

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900">
        Welcome back, {name || "there"}!
      </h1>
      <p className="mt-1 text-sm text-gray-500 capitalize">
        Role: <span className="font-medium text-indigo-600">{role?.replace(/_/g, " ") ?? "—"}</span>
      </p>

      {isHR ? (
        <>
          <p className="mt-4 text-gray-600">Manage your hiring pipeline from here.</p>
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link
              href="/dashboard/jobs"
              className="flex flex-col gap-1 p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
            >
              <span className="text-2xl">💼</span>
              <span className="font-semibold text-gray-900">Job Postings</span>
              <span className="text-sm text-gray-500">Create and manage jobs</span>
            </Link>
            <Link
              href="/dashboard/analytics"
              className="flex flex-col gap-1 p-5 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
            >
              <span className="text-2xl">📊</span>
              <span className="font-semibold text-gray-900">Analytics</span>
              <span className="text-sm text-gray-500">Recruiter metrics</span>
            </Link>
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

            {/* Active applications */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <p className="text-xs text-gray-500">My Applications</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{appCount ?? "—"}</p>
              <Link href="/dashboard/my-applications" className="text-xs text-indigo-600 hover:underline mt-1 block">
                View all →
              </Link>
            </div>

            {/* Open jobs */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <p className="text-xs text-gray-500">Open Positions</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{jobCount ?? "—"}</p>
              <Link href="/dashboard/browse-jobs" className="text-xs text-indigo-600 hover:underline mt-1 block">
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
    </div>
  );
}
