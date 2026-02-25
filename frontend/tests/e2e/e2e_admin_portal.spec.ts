/**
 * E2E tests for the Admin Portal (Module 8)
 * Tests: login, redirect, dashboard KPIs, users page, monitoring
 */
import { test, expect } from "@playwright/test";

const BASE = "http://localhost:3000";
const API = "http://localhost:8001";

const SUPERADMIN_EMAIL = "superadmin@donehr.com";
const SUPERADMIN_PASSWORD = "SuperAdmin@2024!";
const SUPERADMIN_PIN = "123456";

const ADMIN_EMAIL = "admin@donehr.com";
const ADMIN_PASSWORD = "Admin@2024!";
const ADMIN_PIN = "654321";

const ELITE_EMAIL = "elite@donehr.com";
const ELITE_PASSWORD = "Elite@2024!";
const ELITE_PIN = "111111";

async function loginAdmin(
  page: import("@playwright/test").Page,
  email: string,
  password: string,
  pin: string
) {
  await page.goto(`${BASE}/admin/login`);
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);

  // Fill 6-digit PIN boxes
  const pinInputs = page.locator('input[maxlength="1"]');
  for (let i = 0; i < 6; i++) {
    await pinInputs.nth(i).fill(pin[i]);
  }

  await page.click('button[type="submit"]');
  await page.waitForURL("**/admin/dashboard", { timeout: 10000 });
}

// ── Test 1: Unauthenticated redirect ─────────────────────────────────────────
test("unauthenticated access to /admin/dashboard redirects to /admin/login", async ({
  page,
}) => {
  await page.goto(`${BASE}/admin/dashboard`);
  await expect(page).toHaveURL(/\/admin\/login/);
});

// ── Test 2: Admin login page renders correctly ────────────────────────────────
test("admin login page renders with PIN inputs and submit button", async ({
  page,
}) => {
  await page.goto(`${BASE}/admin/login`);
  await expect(page.locator("h1")).toContainText("Admin Portal");
  await expect(page.locator('input[type="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
  // 6 PIN digit boxes
  const pinInputs = page.locator('input[maxlength="1"]');
  await expect(pinInputs).toHaveCount(6);
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});

// ── Test 3: Wrong credentials show error ─────────────────────────────────────
test("wrong credentials show error message on admin login", async ({ page }) => {
  await page.goto(`${BASE}/admin/login`);
  await page.fill('input[type="email"]', SUPERADMIN_EMAIL);
  await page.fill('input[type="password"]', "WrongPassword!");
  const pinInputs = page.locator('input[maxlength="1"]');
  for (let i = 0; i < 6; i++) {
    await pinInputs.nth(i).fill("9");
  }
  await page.click('button[type="submit"]');
  // Error should appear (don't navigate away)
  await expect(page.locator("text=Invalid credentials").or(page.locator("text=Login failed"))).toBeVisible({
    timeout: 5000,
  });
});

// ── Test 4: Superadmin successful login and dashboard ─────────────────────────
test("superadmin can login and sees dashboard KPIs", async ({ page }) => {
  await loginAdmin(page, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_PIN);

  // Should be on dashboard
  await expect(page).toHaveURL(/\/admin\/dashboard/);
  await expect(page.locator("h1")).toContainText("Platform Dashboard");

  // KPI cards should render
  await expect(page.locator("text=Total Users")).toBeVisible({ timeout: 8000 });
  await expect(page.locator("text=Jobs Posted")).toBeVisible();
  await expect(page.locator("text=Companies")).toBeVisible();
});

// ── Test 5: Sidebar navigation ────────────────────────────────────────────────
test("admin sidebar navigation links work", async ({ page }) => {
  await loginAdmin(page, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_PIN);

  // Navigate to Users
  await page.click("text=Users");
  await expect(page).toHaveURL(/\/admin\/users/);
  await expect(page.locator("h1")).toContainText("User Management");

  // Navigate to Companies
  await page.click("text=Companies");
  await expect(page).toHaveURL(/\/admin\/companies/);
  await expect(page.locator("h1")).toContainText("Company Management");

  // Navigate to Monitoring
  await page.click("text=Monitoring");
  await expect(page).toHaveURL(/\/admin\/monitoring/);
  await expect(page.locator("h1")).toContainText("System Monitoring");
});

// ── Test 6: Users page shows candidates and HR tabs ───────────────────────────
test("users page shows candidates and HR tabs with data", async ({ page }) => {
  await loginAdmin(page, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_PIN);
  await page.goto(`${BASE}/admin/users`);

  await expect(page.locator("text=Candidates")).toBeVisible();
  await expect(page.locator("text=HR Users")).toBeVisible();

  // Search input exists
  await expect(page.locator('input[placeholder*="Search"]')).toBeVisible();

  // Switch to HR tab
  await page.click("text=HR Users");
  await expect(page.locator("h1")).toContainText("User Management");
});

// ── Test 7: Monitoring auto-refresh metrics ───────────────────────────────────
test("monitoring page shows system metrics", async ({ page }) => {
  await loginAdmin(page, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_PIN);
  await page.goto(`${BASE}/admin/monitoring`);

  await expect(page.locator("text=Query Latency")).toBeVisible({ timeout: 10000 });
  await expect(page.locator("text=Cache Hit Rate")).toBeVisible();
  await expect(page.locator("text=WebSocket")).toBeVisible();
  await expect(page.locator("text=Groq API Calls Today")).toBeVisible();
});

// ── Test 8: Elite admin cannot see Admin Users page ──────────────────────────
test("elite admin is redirected away from /admin/admins", async ({ page }) => {
  await loginAdmin(page, ELITE_EMAIL, ELITE_PASSWORD, ELITE_PIN);

  // Navigate directly to admins page (elite_admin cannot access)
  await page.goto(`${BASE}/admin/admins`);

  // Should be redirected to dashboard
  await expect(page).toHaveURL(/\/admin\/dashboard/);
});

// ── Test 9: Superadmin sees Admin Users nav item ──────────────────────────────
test("superadmin sees Admin Users in sidebar", async ({ page }) => {
  await loginAdmin(page, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_PIN);
  await expect(page.locator("text=Admin Users")).toBeVisible();
});

// ── Test 10: Logout clears session and redirects ──────────────────────────────
test("sign out redirects to /admin/login", async ({ page }) => {
  await loginAdmin(page, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_PIN);
  await page.click("text=Sign Out");
  await expect(page).toHaveURL(/\/admin\/login/, { timeout: 5000 });
  // Trying to access dashboard redirects back
  await page.goto(`${BASE}/admin/dashboard`);
  await expect(page).toHaveURL(/\/admin\/login/);
});

// ── Test 11: Events log page shows event table ────────────────────────────────
test("events log page renders event table", async ({ page }) => {
  await loginAdmin(page, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_PIN);
  await page.goto(`${BASE}/admin/events`);

  await expect(page.locator("h1")).toContainText("Platform Event Log");
  // Filter selects
  await expect(page.locator("select").first()).toBeVisible();
  // Export CSV button visible for non-elite
  await expect(page.locator("text=Export CSV")).toBeVisible();
});

// ── Test 12: Elite admin cannot see Export CSV ────────────────────────────────
test("elite admin cannot see Export CSV on events page", async ({ page }) => {
  await loginAdmin(page, ELITE_EMAIL, ELITE_PASSWORD, ELITE_PIN);
  await page.goto(`${BASE}/admin/events`);

  await expect(page.locator("h1")).toContainText("Platform Event Log");
  await expect(page.locator("text=Export CSV")).not.toBeVisible();
});

// ── Test 13: Backend admin login API (direct API test) ───────────────────────
test("admin login API returns valid JWT", async ({ request }) => {
  const response = await request.post(`${API}/admin/login`, {
    data: {
      email: SUPERADMIN_EMAIL,
      password: SUPERADMIN_PASSWORD,
      pin: SUPERADMIN_PIN,
    },
  });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty("access_token");
  expect(body.role).toBe("superadmin");
  expect(body.full_name).toBe("Super Admin");
});

// ── Test 14: Platform overview API returns expected shape ─────────────────────
test("platform overview API returns correct shape", async ({ request }) => {
  // First get token
  const loginResp = await request.post(`${API}/admin/login`, {
    data: {
      email: SUPERADMIN_EMAIL,
      password: SUPERADMIN_PASSWORD,
      pin: SUPERADMIN_PIN,
    },
  });
  const { access_token } = await loginResp.json();

  const overviewResp = await request.get(`${API}/admin/platform/overview`, {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  expect(overviewResp.status()).toBe(200);
  const overview = await overviewResp.json();
  expect(overview).toHaveProperty("total_users");
  expect(overview).toHaveProperty("total_candidates");
  expect(overview).toHaveProperty("active_jobs");
  expect(overview).toHaveProperty("active_ws_connections");
});

// ── Test 15: Monitoring API requires admin auth ───────────────────────────────
test("monitoring API returns 401 without token", async ({ request }) => {
  const resp = await request.get(`${API}/admin/monitoring`);
  expect(resp.status()).toBe(401);
});
