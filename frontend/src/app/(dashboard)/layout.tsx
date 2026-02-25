"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { authAPI } from "@/lib/api";
import { clearToken, getSessionUser, type UserRole } from "@/lib/auth";
import ChatbotWidget from "@/components/ai/ChatbotWidget";
import { useRealtimeEvents, RealtimeContext } from "@/hooks/useRealtimeEvents";

interface NavItem {
  label: string;
  href: string;
  icon: string;
  roles?: UserRole[]; // undefined = all roles
}

const HR_ROLES: UserRole[] = [
  "hr", "hr_admin", "hiring_manager", "recruiter", "superadmin", "admin", "elite_admin",
];

const CANDIDATE_ROLES: UserRole[] = ["candidate"];

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "⊞" },
  // HR nav
  { label: "Job Postings", href: "/dashboard/jobs", icon: "💼", roles: HR_ROLES },
  { label: "Find Candidates", href: "/dashboard/search", icon: "🔎", roles: HR_ROLES },
  { label: "Analytics", href: "/dashboard/analytics", icon: "📊", roles: HR_ROLES },
  // Candidate nav
  { label: "My Profile", href: "/dashboard/profile", icon: "👤", roles: CANDIDATE_ROLES },
  { label: "Browse Jobs", href: "/dashboard/browse-jobs", icon: "🔍", roles: CANDIDATE_ROLES },
  { label: "My Applications", href: "/dashboard/my-applications", icon: "📄", roles: CANDIDATE_ROLES },
  { label: "Job Alerts", href: "/dashboard/job-alerts", icon: "🔔", roles: CANDIDATE_ROLES },
  { label: "Resume Optimizer", href: "/dashboard/resume-optimizer", icon: "✨", roles: CANDIDATE_ROLES },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [userEmail, setUserEmail] = useState<string>("");
  const [userRole, setUserRole] = useState<UserRole | null>(null);

  const realtime = useRealtimeEvents();

  useEffect(() => {
    // Read role from sessionStorage instantly (no network call needed)
    const session = getSessionUser();
    if (session) {
      setUserRole(session.role as UserRole);
      setUserEmail(session.email);
    }
    // Confirm session is still valid via API
    authAPI
      .me()
      .then((res) => setUserEmail(res.data.email))
      .catch(() => {
        clearToken();
        router.replace("/login");
      });
  }, [router]);

  async function handleLogout() {
    try {
      await authAPI.logout();
    } catch {
      // ignore
    } finally {
      clearToken();
      await fetch("/api/set-cookie", { method: "DELETE" });
      router.replace("/login");
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 flex flex-col bg-white border-r border-gray-200">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-gray-200">
          <span className="text-xl font-bold text-indigo-600">FindUs</span>
          <p className="text-xs text-gray-500 mt-0.5">HR Portal</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.filter(
            (item) =>
              !item.roles ||
              (userRole && item.roles.includes(userRole))
          ).map((item) => {
            const active =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User footer */}
        <div className="px-4 py-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 truncate mb-2">{userEmail}</p>
          {/* WebSocket connection status */}
          <div className="flex items-center gap-1.5 mb-2">
            <span
              className={`w-2 h-2 rounded-full flex-shrink-0 ${
                realtime.status === "connected"
                  ? "bg-green-500"
                  : realtime.status === "connecting"
                  ? "bg-yellow-400 animate-pulse"
                  : "bg-gray-400"
              }`}
            />
            <span className="text-xs text-gray-400">
              {realtime.status === "connected"
                ? "Live"
                : realtime.status === "connecting"
                ? "Connecting…"
                : "Offline"}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left text-sm text-red-600 hover:text-red-800 transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <RealtimeContext.Provider value={realtime}>
        <main className="flex-1 overflow-auto">{children}</main>
      </RealtimeContext.Provider>

      {/* AI Chatbot — candidate only */}
      {userRole === "candidate" && <ChatbotWidget />}
    </div>
  );
}
