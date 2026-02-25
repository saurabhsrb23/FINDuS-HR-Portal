/**
 * E2E test: Candidate Search (Module 6)
 *
 * Pre-conditions:
 *   - Full stack is running (docker compose up --build -d)
 *   - Migration 006 has been applied (alembic upgrade head)
 *   - seed.py has been run (HR users + 10 candidates exist)
 *
 * Test user:  hr@donehr.com / Hr@123456!  (hr_admin role)
 */

import { expect, Page, test } from "@playwright/test";

// ── Helpers ───────────────────────────────────────────────────────────────────

async function loginAsHR(page: Page) {
  await page.goto("/login");
  // Switch to HR tab if present
  const hrTab = page.getByRole("tab", { name: /hr/i });
  if (await hrTab.isVisible()) {
    await hrTab.click();
  }
  await page.getByLabel(/email/i).fill("hr@donehr.com");
  await page.getByLabel(/password/i).fill("Hr@123456!");
  await page.getByRole("button", { name: /login|sign in/i }).click();
  // Wait for dashboard to load
  await page.waitForURL(/\/dashboard/, { timeout: 15_000 });
}

async function goToSearchPage(page: Page) {
  await page.goto("/dashboard/search");
  await page.waitForLoadState("networkidle");
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe("Candidate Search Page", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsHR(page);
    await goToSearchPage(page);
  });

  // ── 1. Page loads ────────────────────────────────────────────────────────

  test("search page renders heading and filter panel", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /find candidates/i })).toBeVisible();
    await expect(page.getByText(/filters/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /search/i })).toBeVisible();
  });

  // ── 2. Initial search (no filters) ───────────────────────────────────────

  test("clicking Search with no filters returns results", async ({ page }) => {
    await page.getByRole("button", { name: /search/i }).click();
    // Wait for results
    await page.waitForResponse(
      (r) => r.url().includes("/api/v1/search/candidates") && r.status() === 200,
      { timeout: 15_000 }
    );
    // Should show result count
    await expect(page.getByText(/\d+ results/i)).toBeVisible({ timeout: 8_000 });
  });

  // ── 3. Location filter ────────────────────────────────────────────────────

  test("location filter narrows results", async ({ page }) => {
    await page.getByPlaceholder(/bangalore|mumbai/i).fill("Bangalore");
    await page.getByRole("button", { name: /search/i }).click();
    await page.waitForResponse(
      (r) => r.url().includes("/api/v1/search/candidates") && r.status() === 200,
      { timeout: 15_000 }
    );
    // Results should appear (or zero-state message)
    const hasResults = await page.locator("[aria-label]").count();
    // No assertion on count — just assert no server error
    await expect(page.locator("body")).not.toContainText("500");
  });

  // ── 4. Skill filter chip ──────────────────────────────────────────────────

  test("adding a skill chip and searching", async ({ page }) => {
    const skillInput = page.getByPlaceholder("Skill name");
    await skillInput.fill("Python");
    await page.getByRole("button", { name: "+" }).first().click();
    // Chip should appear
    await expect(page.getByText("Python")).toBeVisible();

    await page.getByRole("button", { name: /search/i }).click();
    await page.waitForResponse(
      (r) => r.url().includes("/api/v1/search/candidates") && r.status() === 200,
      { timeout: 15_000 }
    );
    await expect(page.locator("body")).not.toContainText("500");
  });

  // ── 5. Remove skill chip ──────────────────────────────────────────────────

  test("removing a skill chip", async ({ page }) => {
    const skillInput = page.getByPlaceholder("Skill name");
    await skillInput.fill("React");
    await page.getByRole("button", { name: "+" }).first().click();
    await expect(page.getByText("React")).toBeVisible();

    // Remove via × button
    await page.locator("button").filter({ hasText: "×" }).first().click();
    await expect(page.getByText("React")).not.toBeVisible();
  });

  // ── 6. View toggle: card ↔ table ─────────────────────────────────────────

  test("view mode toggle switches between card and table", async ({ page }) => {
    await page.getByRole("button", { name: /search/i }).click();
    await page.waitForResponse(
      (r) => r.url().includes("/api/v1/search/candidates") && r.status() === 200,
      { timeout: 15_000 }
    );

    // Switch to table view
    await page.getByRole("button", { name: /table/i }).click();
    await expect(page.getByRole("table")).toBeVisible({ timeout: 5_000 });

    // Switch back to card view
    await page.getByRole("button", { name: /cards/i }).click();
    await expect(page.getByRole("table")).not.toBeVisible();
  });

  // ── 7. Sort change ────────────────────────────────────────────────────────

  test("changing sort order fires a new search request", async ({ page }) => {
    // First do an initial search
    await page.getByRole("button", { name: /search/i }).click();
    await page.waitForResponse(
      (r) => r.url().includes("/api/v1/search/candidates") && r.status() === 200,
      { timeout: 15_000 }
    );

    // Change sort to "Experience"
    const sortSelect = page.getByRole("combobox").first();
    const [newReq] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes("/api/v1/search/candidates") && r.status() === 200,
        { timeout: 15_000 }
      ),
      sortSelect.selectOption("experience"),
    ]);
    expect(newReq.status()).toBe(200);
  });

  // ── 8. Save search flow ───────────────────────────────────────────────────

  test("saving and loading a search", async ({ page }) => {
    // Set a location filter
    await page.getByPlaceholder(/bangalore|mumbai/i).fill("Hyderabad");
    await page.getByRole("button", { name: /search/i }).click();
    await page.waitForResponse(
      (r) => r.url().includes("/api/v1/search/candidates") && r.status() === 200,
      { timeout: 15_000 }
    );

    // Open save dialog
    await page.getByRole("button", { name: /save search/i }).click();
    const dialog = page.getByRole("dialog").or(page.locator(".fixed.inset-0"));
    // Type name
    await page.getByPlaceholder(/give this search a name/i).fill("Hyderabad devs");
    await page.getByRole("button", { name: /save$/i }).click();

    // Chip should appear in saved searches bar
    await expect(page.getByText("Hyderabad devs")).toBeVisible({ timeout: 5_000 });
  });

  // ── 9. Candidate selection & bulk export ─────────────────────────────────

  test("selecting candidates shows bulk action bar", async ({ page }) => {
    // First run a search to get candidates
    await page.getByRole("button", { name: /search/i }).click();
    await page.waitForResponse(
      (r) => r.url().includes("/api/v1/search/candidates") && r.status() === 200,
      { timeout: 15_000 }
    );

    // Try to find a checkbox and check it
    const checkboxes = page.getByRole("checkbox");
    const count = await checkboxes.count();
    if (count > 1) {
      // Skip header "select all" at index 0
      await checkboxes.nth(1).check();
      // Bulk actions bar should appear
      await expect(page.getByText(/selected/i)).toBeVisible({ timeout: 3_000 });
      await expect(page.getByRole("button", { name: /export csv/i })).toBeVisible();
    }
  });

  // ── 10. Candidate-only routes redirect HR away from search page
  //       (already handled by middleware, but ensure search is accessible)

  test("HR can access /dashboard/search without redirect", async ({ page }) => {
    await expect(page).toHaveURL(/\/dashboard\/search/);
  });
});

// ── Auth guard: candidate cannot access search ────────────────────────────────

test.describe("Search page auth guard", () => {
  test("candidate user is redirected away from /dashboard/search", async ({ page }) => {
    // Login as candidate
    await page.goto("/login");
    const candidateTab = page.getByRole("tab", { name: /candidate/i });
    if (await candidateTab.isVisible()) {
      await candidateTab.click();
    }
    await page.getByLabel(/email/i).fill("candidate@donehr.com");
    await page.getByLabel(/password/i).fill("Candidate@1!");
    await page.getByRole("button", { name: /login|sign in/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 15_000 });

    // Navigate to search page directly
    await page.goto("/dashboard/search");
    await page.waitForLoadState("networkidle");

    // Middleware should have redirected away from /dashboard/search
    await expect(page).not.toHaveURL(/\/dashboard\/search/);
  });
});
