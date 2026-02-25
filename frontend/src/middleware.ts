/**
 * Next.js edge middleware — route-level auth guard.
 *
 * Rules:
 *  /dashboard/candidate/* → requires access_token cookie with role=candidate
 *  /dashboard/recruiter/* → requires access_token cookie with role in HR_ROLES
 *  /admin/*               → requires admin_token cookie with aud="admin_portal"
 *
 * Uses the `jose` package (edge-runtime safe) to verify JWTs without making
 * a network request. Both frontend and backend share the same SECRET_KEY.
 */

import { NextRequest, NextResponse } from "next/server";
import { jwtVerify, JWTPayload } from "jose";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function enc(secret: string): Uint8Array {
  return new TextEncoder().encode(secret);
}

type JWTPayloadWithRole = JWTPayload & { role?: string };

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

function loginRedirect(request: NextRequest, params?: string): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = "/login";
  if (params) url.searchParams.set("redirect", params);
  return NextResponse.redirect(url);
}

// ─── Role sets ────────────────────────────────────────────────────────────────
const HR_ROLES = new Set([
  "hr",
  "hr_admin",
  "hiring_manager",
  "recruiter",
]);

const ADMIN_ROLES = new Set(["admin", "superadmin", "elite_admin"]);

// ─── Middleware ────────────────────────────────────────────────────────────────
export async function middleware(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl;

  const SECRET_KEY = process.env.SECRET_KEY ?? "";
  const ADMIN_JWT_SECRET = process.env.ADMIN_JWT_SECRET ?? "";

  // ── /admin/* ────────────────────────────────────────────────────────────────
  if (pathname.startsWith("/admin")) {
    const adminToken = request.cookies.get("admin_token")?.value;
    if (!adminToken) return loginRedirect(request, pathname);

    const payload = await verifyToken(adminToken, ADMIN_JWT_SECRET, {
      audience: "admin_portal",
    });
    if (!payload || !ADMIN_ROLES.has(payload.role ?? "")) {
      return loginRedirect(request, pathname);
    }
    return NextResponse.next();
  }

  // ── /dashboard/candidate/* ──────────────────────────────────────────────────
  if (pathname.startsWith("/dashboard/candidate")) {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) return loginRedirect(request, pathname);

    const payload = await verifyToken(accessToken, SECRET_KEY);
    if (!payload) return loginRedirect(request, pathname);

    if (payload.role !== "candidate") {
      const url = request.nextUrl.clone();
      url.pathname = "/unauthorized";
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  // ── /dashboard/recruiter/* ──────────────────────────────────────────────────
  if (pathname.startsWith("/dashboard/recruiter")) {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) return loginRedirect(request, pathname);

    const payload = await verifyToken(accessToken, SECRET_KEY);
    if (!payload) return loginRedirect(request, pathname);

    if (!HR_ROLES.has(payload.role ?? "")) {
      const url = request.nextUrl.clone();
      url.pathname = "/unauthorized";
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/admin/:path*",
  ],
};
