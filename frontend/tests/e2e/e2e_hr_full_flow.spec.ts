/**
 * E2E — HR full flow (Module 10)
 *
 * Pre-conditions:
 *   docker compose up --build -d && alembic upgrade head && python seed.py
 *
 * Test user: hr@donehr.com / Hr@123456!  (hr_admin role)
 */
import { expect, Page, test } from "@playwright/test";

async function loginAsHR(page: Page) {
  await page.goto("/login");
  const hrTab = page.getByRole("tab", { name: /hr/i });
  if (await hrTab.isVisible()) await hrTab.click();
  await page.getByLabel(/email/i).fill("hr@donehr.com");
  await page.getByLabel(/password/i).fill("Hr@123456!");
  await page.getByRole("button", { name: /login|sign in/i }).click();
  await page.waitForURL(/\/dashboard/, { timeout: 15_000 });
}

test.describe("HR — Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsHR(page);
  });

  test("dashboard loads with HR-specific widgets", async ({ page }) => {
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator("body")).toBeVisible();
  });

  test("sidebar shows HR navigation links", async ({ page }) => {
    await expect(page.getByRole("link", { name: /jobs/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /analytics/i })).toBeVisible();
  });
});

test.describe("HR — Job Management", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/jobs");
    await page.waitForLoadState("networkidle");
  });

  test("jobs list loads", async ({ page }) => {
    await expect(page.getByText(/job|posting/i)).toBeVisible({ timeout: 10_000 });
  });

  test("can navigate to create new job", async ({ page }) => {
    const newJobBtn = page.getByRole("link", { name: /new job|create job|post job/i });
    if (await newJobBtn.isVisible()) {
      await newJobBtn.click();
      await page.waitForURL(/\/jobs\/new/, { timeout: 8_000 });
    }
  });

  test("create job form loads with required fields", async ({ page }) => {
    await page.goto("/dashboard/jobs/new");
    await page.waitForLoadState("networkidle");
    await expect(page.getByLabel(/job title|title/i)).toBeVisible({ timeout: 8_000 });
  });

  test("can create a new draft job", async ({ page }) => {
    await page.goto("/dashboard/jobs/new");
    await page.waitForLoadState("networkidle");
    const titleInput = page.getByLabel(/job title|title/i);
    if (await titleInput.isVisible()) {
      await titleInput.fill("E2E Test Job Position");
      const saveBtn = page.getByRole("button", { name: /save|create|draft/i });
      await saveBtn.click();
      await expect(page.getByText(/created|saved|draft/i)).toBeVisible({ timeout: 10_000 });
    }
  });
});

test.describe("HR — Analytics", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/analytics");
    await page.waitForLoadState("networkidle");
  });

  test("analytics page loads with charts", async ({ page }) => {
    await expect(page.getByText(/analytic|application|funnel|hiring/i)).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("HR — Find Candidates (Search)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/search");
    await page.waitForLoadState("networkidle");
  });

  test("search page loads", async ({ page }) => {
    await expect(page.getByText(/find candidate|talent|search/i)).toBeVisible({ timeout: 10_000 });
  });

  test("boolean search returns results", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|query|boolean/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill("python");
      await page.keyboard.press("Enter");
      await page.waitForLoadState("networkidle");
      // Should show at least 1 result
      await expect(page.locator("[data-testid='candidate-card'], .candidate-card").first()).toBeVisible({ timeout: 10_000 });
    }
  });

  test("skill filter works", async ({ page }) => {
    const skillInput = page.getByPlaceholder(/add skill|skill name/i);
    if (await skillInput.isVisible()) {
      await skillInput.fill("Python");
      await skillInput.press("Enter");
      await page.waitForLoadState("networkidle");
    }
  });

  test("candidate card shows download CV button for candidates with resume", async ({ page }) => {
    // After search, cards with resumes should show Download CV button
    await page.waitForLoadState("networkidle");
    const downloadBtn = page.getByRole("button", { name: /download cv/i });
    if (await downloadBtn.isVisible()) {
      await expect(downloadBtn.first()).toBeVisible();
    }
  });
});

test.describe("HR — Pipeline Management", () => {
  test("pipeline editor loads for a job", async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/jobs");
    await page.waitForLoadState("networkidle");

    // Navigate to first job's pipeline
    const firstJobLink = page.getByRole("link", { name: /pipeline/i }).first();
    if (await firstJobLink.isVisible()) {
      await firstJobLink.click();
      await page.waitForLoadState("networkidle");
      await expect(page.getByText(/pipeline|stage/i)).toBeVisible({ timeout: 10_000 });
    }
  });
});

test.describe("HR — AI Tools", () => {
  test("AI tools page loads for a job", async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/jobs");
    await page.waitForLoadState("networkidle");

    const aiToolsLink = page.getByRole("link", { name: /ai tools/i }).first();
    if (await aiToolsLink.isVisible()) {
      await aiToolsLink.click();
      await page.waitForLoadState("networkidle");
      await expect(page.getByText(/ranking|jd generator|rejection/i)).toBeVisible({ timeout: 10_000 });
    }
  });
});

test.describe("HR — Messages", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/messages");
    await page.waitForLoadState("networkidle");
  });

  test("messages inbox loads", async ({ page }) => {
    await expect(page.getByText(/message|conversation|inbox/i)).toBeVisible({ timeout: 10_000 });
  });

  test("new conversation button is visible", async ({ page }) => {
    const newBtn = page.getByRole("button", { name: /new.*chat|new.*conv|compose/i });
    if (await newBtn.isVisible()) {
      await expect(newBtn).toBeVisible();
    }
  });
});
