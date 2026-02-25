/**
 * Next.js edge middleware — route-level auth + role guard.
 *
 * /dashboard/jobs/*           → HR roles only  (hr, hr_admin, hiring_manager, recruiter)
 * /dashboard/analytics        → HR roles only
 * /dashboard/profile          → candidate only
 * /dashboard/browse-jobs      → candidate only
 * /dashboard/my-applications  → candidate only
 * /dashboard/job-alerts       → candidate only
 * /dashboard/*                → any authenticated user
 * /admin/*                    → admin roles only (admin, superadmin, elite_admin)
 */

import { jwtVerify, JWTPayload } from "jose";
import { NextRequest, NextResponse } from "next/server";

type JWTPayloadWithRole = JWTPayload & { role?: string };

function enc(secret: string): Uint8Array {
  return new TextEncoder().encode(secret);
}

async function verifyToken(
  token: string,
  secret: string,
  options?: { audience?: string }
): Promise<JWTPayloadWithRole | null> {
  try {
    const { payload } = await jwtVerify(token, enc(secret), {
      algorithms: ["HS256"],
      ...(options?.audience ? { audience: options.audience } : {}),
    });
    return payload as JWTPayloadWithRole;
  } catch {
    return null;
  }
}

function redirectTo(request: NextRequest, pathname: string): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = pathname;
  url.search = "";
  return NextResponse.redirect(url);
}

const HR_ROLES = new Set([
  "hr",
  "hr_admin",
  "hiring_manager",
  "recruiter",
  "superadmin",
  "elite_admin",
]);

const ADMIN_ROLES = new Set(["admin", "superadmin", "elite_admin"]);

// Routes only HR / admin roles can access
const HR_ONLY_PREFIXES = [
  "/dashboard/jobs",
  "/dashboard/analytics",
];

// Routes only candidates can access
const CANDIDATE_ONLY_PREFIXES = [
  "/dashboard/profile",
  "/dashboard/browse-jobs",
  "/dashboard/my-applications",
  "/dashboard/job-alerts",
  "/dashboard/resume-optimizer",
];

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl;
  const SECRET_KEY = process.env.SECRET_KEY ?? "";
  const ADMIN_JWT_SECRET = process.env.ADMIN_JWT_SECRET ?? "";

  // ── /admin/* ─────────────────────────────────────────────────────────────
  if (pathname.startsWith("/admin")) {
    const token = request.cookies.get("admin_token")?.value;
    if (!token) return redirectTo(request, "/login");
    const payload = await verifyToken(token, ADMIN_JWT_SECRET, {
      audience: "admin_portal",
    });
    if (!payload || !ADMIN_ROLES.has(payload.role ?? ""))
      return redirectTo(request, "/login");
    return NextResponse.next();
  }

  // ── /dashboard/* ─────────────────────────────────────────────────────────
  if (pathname.startsWith("/dashboard")) {
    const token = request.cookies.get("access_token")?.value;
    if (!token) return redirectTo(request, "/login");

    const payload = await verifyToken(token, SECRET_KEY);
    if (!payload) return redirectTo(request, "/login");

    const role = payload.role ?? "";

    // HR-only sub-paths → redirect candidates to their dashboard
    const isHrOnly = HR_ONLY_PREFIXES.some((p) => pathname.startsWith(p));
    if (isHrOnly && !HR_ROLES.has(role)) {
      return redirectTo(request, "/dashboard");
    }

    // Candidate-only sub-paths → redirect HR to their jobs page
    const isCandidateOnly = CANDIDATE_ONLY_PREFIXES.some((p) => pathname.startsWith(p));
    if (isCandidateOnly && HR_ROLES.has(role)) {
      return redirectTo(request, "/dashboard/jobs");
    }

    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/admin/:path*"],
};
