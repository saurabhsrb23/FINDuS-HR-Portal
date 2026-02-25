/**
 * Auth utilities for the FindUs frontend.
 *
 * Strategy:
 *  - Tokens are stored in httpOnly cookies (via /api/set-cookie Next.js route).
 *    This protects them from XSS.
 *  - A small non-sensitive session object (role, user_id, email) is stored in
 *    sessionStorage so client-side code can make routing decisions without
 *    decoding the JWT (which lives only in httpOnly cookies).
 *  - For API calls to the backend, the access token is read from sessionStorage
 *    (stored after login) for the axios Authorization header.
 */

"use client";

import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

// ─── Types ────────────────────────────────────────────────────────────────────
export type UserRole =
  | "candidate"
  | "hr"
  | "hr_admin"
  | "hiring_manager"
  | "recruiter"
  | "superadmin"
  | "admin"
  | "elite_admin";

export interface SessionUser {
  user_id: string;
  email: string;
  role: UserRole;
}

// ─── Storage keys ─────────────────────────────────────────────────────────────
const SESSION_KEY = "findus_session";
const ACCESS_TOKEN_KEY = "findus_access_token";
const REFRESH_TOKEN_KEY = "findus_refresh_token";

// ─── Token management ─────────────────────────────────────────────────────────
/**
 * Store tokens:
 *  1. Call the Next.js /api/set-cookie route to set httpOnly cookies
 *  2. Also keep in sessionStorage for Authorization header injection
 */
export async function setToken(params: {
  access_token: string;
  refresh_token: string;
  role: UserRole;
  user_id: string;
  email?: string;
}): Promise<void> {
  const { access_token, refresh_token, role, user_id, email = "" } = params;

  // Set httpOnly cookies via Next.js API route
  await fetch("/api/set-cookie", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_token, refresh_token }),
  });

  // Keep in sessionStorage for Authorization header use
  if (typeof window !== "undefined") {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    sessionStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
    sessionStorage.setItem(
      SESSION_KEY,
      JSON.stringify({ user_id, role, email } satisfies SessionUser)
    );
  }
}

/** Read the access token (sessionStorage — not the httpOnly cookie). */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

/** Read the refresh token from sessionStorage. */
export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(REFRESH_TOKEN_KEY);
}

/** Update the access token after a refresh cycle. */
export function updateAccessToken(access_token: string): void {
  if (typeof window !== "undefined") {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, access_token);
  }
}

/**
 * Clear all stored tokens:
 *  1. Delete httpOnly cookies via /api/set-cookie DELETE
 *  2. Clear sessionStorage
 */
export async function clearToken(): Promise<void> {
  await fetch("/api/set-cookie", { method: "DELETE" }).catch(() => {});
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(SESSION_KEY);
  }
}

// ─── Session helpers ──────────────────────────────────────────────────────────
export function getSessionUser(): SessionUser | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export function getUserRole(): UserRole | null {
  return getSessionUser()?.role ?? null;
}

// ─── Role-based redirect ──────────────────────────────────────────────────────
const HR_ROLES: UserRole[] = ["hr", "hr_admin", "hiring_manager", "recruiter"];
const ADMIN_ROLES: UserRole[] = ["admin", "superadmin", "elite_admin"];

export function redirectByRole(
  role: UserRole,
  router: AppRouterInstance
): void {
  if (ADMIN_ROLES.includes(role)) {
    router.push("/admin");
  } else if (HR_ROLES.includes(role)) {
    router.push("/dashboard/jobs");
  } else {
    router.push("/dashboard");
  }
}

/** Return the dashboard path for a role (for use without a router object). */
export function dashboardPathForRole(role: UserRole): string {
  if (ADMIN_ROLES.includes(role)) return "/admin";
  if (HR_ROLES.includes(role)) return "/dashboard/jobs";
  return "/dashboard";
}
