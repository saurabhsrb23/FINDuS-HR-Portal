/**
 * POST /api/set-cookie  — set httpOnly auth cookies
 * DELETE /api/set-cookie — clear auth cookies
 *
 * Called by the frontend after a successful login or token refresh so that
 * the actual JWTs are stored in httpOnly, Secure, SameSite=Strict cookies
 * inaccessible to JavaScript (XSS protection).
 */

import { NextRequest, NextResponse } from "next/server";

const IS_PROD = process.env.NODE_ENV === "production";

const ACCESS_TOKEN_MAX_AGE = 15 * 60;           // 15 minutes
const REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60; // 7 days

export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: { access_token?: string; refresh_token?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { access_token, refresh_token } = body;

  if (!access_token || !refresh_token) {
    return NextResponse.json(
      { error: "access_token and refresh_token are required" },
      { status: 400 }
    );
  }

  const response = NextResponse.json({ success: true });

  response.cookies.set("access_token", access_token, {
    httpOnly: true,
    secure: IS_PROD,
    sameSite: "strict",
    maxAge: ACCESS_TOKEN_MAX_AGE,
    path: "/",
  });

  response.cookies.set("refresh_token", refresh_token, {
    httpOnly: true,
    secure: IS_PROD,
    sameSite: "strict",
    maxAge: REFRESH_TOKEN_MAX_AGE,
    path: "/",
  });

  return response;
}

export async function DELETE(_request: NextRequest): Promise<NextResponse> {
  const response = NextResponse.json({ success: true });

  for (const name of ["access_token", "refresh_token", "admin_token"]) {
    response.cookies.set(name, "", {
      httpOnly: true,
      secure: IS_PROD,
      sameSite: "strict",
      maxAge: 0,
      path: "/",
    });
  }

  return response;
}
