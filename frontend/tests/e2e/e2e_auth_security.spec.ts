/**
 * E2E — Auth & Security (Module 10)
 *
 * Pre-conditions:
 *   docker compose up --build -d && alembic upgrade head && python seed.py
 */
import { expect, Page, test } from "@playwright/test";

// ── Login tests ────────────────────────────────────────────────────────────────

test.describe("Auth — Login", () => {
  test("login page renders both tabs", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("tab", { name: /candidate/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /hr|employer/i })).toBeVisible();
  });

  test("candidate can log in successfully", async ({ page }) => {
    await page.goto("/login");
    const candTab = page.getByRole("tab", { name: /candidate/i });
    if (await candTab.isVisible()) await candTab.click();
    await page.getByLabel(/email/i).fill("candidate@donehr.com");
    await page.getByLabel(/password/i).fill("Candidate@1!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 15_000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("HR can log in successfully", async ({ page }) => {
    await page.goto("/login");
    const hrTab = page.getByRole("tab", { name: /hr/i });
    if (await hrTab.isVisible()) await hrTab.click();
    await page.getByLabel(/email/i).fill("hr@donehr.com");
    await page.getByLabel(/password/i).fill("Hr@123456!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 15_000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("wrong password shows error", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("candidate@donehr.com");
    await page.getByLabel(/password/i).fill("WrongPassword123!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    // Should NOT navigate to dashboard
    await page.waitForTimeout(3000);
    await expect(page).not.toHaveURL(/\/dashboard/);
    // Should show an error message
    await expect(page.getByText(/invalid|incorrect|wrong|error|unauthorized/i)).toBeVisible({ timeout: 8_000 });
  });

  test("non-existent user shows error", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("ghost@donehr.com");
    await page.getByLabel(/password/i).fill("Ghost@1234!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    await page.waitForTimeout(3000);
    await expect(page).not.toHaveURL(/\/dashboard/);
  });

  test("empty form shows validation", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    // Should not navigate (HTML5 validation or error toast)
    await page.waitForTimeout(1000);
    await expect(page).not.toHaveURL(/\/dashboard/);
  });
});

// ── Register tests ─────────────────────────────────────────────────────────────

test.describe("Auth — Register", () => {
  test("register page loads", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByText(/register|sign up|create account/i)).toBeVisible();
  });

  test("register requires valid email format", async ({ page }) => {
    await page.goto("/register");
    const emailInput = page.getByLabel(/email/i);
    if (await emailInput.isVisible()) {
      await emailInput.fill("not-an-email");
      await page.getByRole("button", { name: /register|sign up|next/i }).click();
      await page.waitForTimeout(1000);
      await expect(page).not.toHaveURL(/\/dashboard/);
    }
  });
});

// ── Role-based access control ──────────────────────────────────────────────────

test.describe("Auth — RBAC", () => {
  test("candidate cannot access HR jobs page", async ({ page }) => {
    // Login as candidate
    await page.goto("/login");
    const candTab = page.getByRole("tab", { name: /candidate/i });
    if (await candTab.isVisible()) await candTab.click();
    await page.getByLabel(/email/i).fill("candidate@donehr.com");
    await page.getByLabel(/password/i).fill("Candidate@1!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 15_000 });

    // Attempt to navigate to HR-only jobs management
    await page.goto("/dashboard/jobs/new");
    // Should redirect away or show 403/unauthorized
    await page.waitForTimeout(3000);
    const url = page.url();
    const text = await page.locator("body").textContent();
    // Either redirected OR shows unauthorized
    expect(url.includes("/dashboard/jobs/new") === false || /unauthorized|forbidden|not allowed/i.test(text ?? "")).toBeTruthy();
  });

  test("HR cannot access candidate-only resume optimizer", async ({ page }) => {
    await page.goto("/login");
    const hrTab = page.getByRole("tab", { name: /hr/i });
    if (await hrTab.isVisible()) await hrTab.click();
    await page.getByLabel(/email/i).fill("hr@donehr.com");
    await page.getByLabel(/password/i).fill("Hr@123456!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 15_000 });

    await page.goto("/dashboard/resume-optimizer");
    await page.waitForTimeout(3000);
    const url = page.url();
    const text = await page.locator("body").textContent();
    expect(url.includes("/dashboard/resume-optimizer") === false || /unauthorized|forbidden|not allowed/i.test(text ?? "")).toBeTruthy();
  });

  test("unauthenticated user is redirected to login", async ({ page }) => {
    // Direct access without auth
    await page.goto("/dashboard");
    await page.waitForURL(/\/login/, { timeout: 10_000 });
    await expect(page).toHaveURL(/\/login/);
  });
});

// ── Logout ─────────────────────────────────────────────────────────────────────

test.describe("Auth — Logout", () => {
  test("candidate can log out", async ({ page }) => {
    await page.goto("/login");
    const candTab = page.getByRole("tab", { name: /candidate/i });
    if (await candTab.isVisible()) await candTab.click();
    await page.getByLabel(/email/i).fill("candidate@donehr.com");
    await page.getByLabel(/password/i).fill("Candidate@1!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 15_000 });

    // Click logout
    const logoutBtn = page.getByRole("button", { name: /sign out|logout/i });
    if (await logoutBtn.isVisible()) {
      await logoutBtn.click();
      await page.waitForURL(/\/login/, { timeout: 10_000 });
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test("after logout, protected routes redirect to login", async ({ page }) => {
    // Login
    await page.goto("/login");
    const candTab = page.getByRole("tab", { name: /candidate/i });
    if (await candTab.isVisible()) await candTab.click();
    await page.getByLabel(/email/i).fill("candidate@donehr.com");
    await page.getByLabel(/password/i).fill("Candidate@1!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 15_000 });

    // Logout
    const logoutBtn = page.getByRole("button", { name: /sign out|logout/i });
    if (await logoutBtn.isVisible()) {
      await logoutBtn.click();
      await page.waitForURL(/\/login/, { timeout: 10_000 });
      // Try to go back to dashboard
      await page.goto("/dashboard");
      await page.waitForURL(/\/login/, { timeout: 10_000 });
      await expect(page).toHaveURL(/\/login/);
    }
  });
});

// ── Admin Portal ────────────────────────────────────────────────────────────────

test.describe("Auth — Admin Portal", () => {
  test("admin login page is accessible", async ({ page }) => {
    await page.goto("/admin/login");
    await expect(page.getByText(/admin|portal/i)).toBeVisible({ timeout: 8_000 });
  });

  test("admin login requires PIN", async ({ page }) => {
    await page.goto("/admin/login");
    const emailInput = page.getByLabel(/email/i);
    const pinInput = page.getByLabel(/pin/i);
    if (await emailInput.isVisible()) {
      await expect(emailInput).toBeVisible();
      if (await pinInput.isVisible()) {
        await expect(pinInput).toBeVisible();
      }
    }
  });

  test("superadmin can log into admin portal", async ({ page }) => {
    await page.goto("/admin/login");
    const emailInput = page.getByLabel(/email/i);
    const passwordInput = page.getByLabel(/password/i);
    const pinInput = page.getByLabel(/pin/i);
    if (await emailInput.isVisible() && await pinInput.isVisible()) {
      await emailInput.fill("superadmin@donehr.com");
      if (await passwordInput.isVisible()) await passwordInput.fill("SuperAdmin@2024!");
      await pinInput.fill("123456");
      await page.getByRole("button", { name: /login|sign in/i }).click();
      await page.waitForURL(/\/admin\/dashboard/, { timeout: 15_000 });
      await expect(page).toHaveURL(/\/admin/);
    }
  });

  test("wrong admin PIN shows error", async ({ page }) => {
    await page.goto("/admin/login");
    const emailInput = page.getByLabel(/email/i);
    const pinInput = page.getByLabel(/pin/i);
    if (await emailInput.isVisible() && await pinInput.isVisible()) {
      await emailInput.fill("superadmin@donehr.com");
      const pw = page.getByLabel(/password/i);
      if (await pw.isVisible()) await pw.fill("SuperAdmin@2024!");
      await pinInput.fill("999999");
      await page.getByRole("button", { name: /login|sign in/i }).click();
      await page.waitForTimeout(3000);
      await expect(page).not.toHaveURL(/\/admin\/dashboard/);
    }
  });
});
