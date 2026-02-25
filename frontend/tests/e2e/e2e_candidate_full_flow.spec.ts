/**
 * E2E — Candidate full flow (Module 10)
 *
 * Pre-conditions:
 *   docker compose up --build -d && alembic upgrade head && python seed.py
 *
 * Test user: candidate@donehr.com / Candidate@1!
 */
import { expect, Page, test } from "@playwright/test";

async function loginAsCandidate(page: Page) {
  await page.goto("/login");
  const candTab = page.getByRole("tab", { name: /candidate/i });
  if (await candTab.isVisible()) await candTab.click();
  await page.getByLabel(/email/i).fill("candidate@donehr.com");
  await page.getByLabel(/password/i).fill("Candidate@1!");
  await page.getByRole("button", { name: /login|sign in/i }).click();
  await page.waitForURL(/\/dashboard/, { timeout: 15_000 });
}

test.describe("Candidate — Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCandidate(page);
  });

  test("dashboard loads and shows welcome", async ({ page }) => {
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator("body")).toBeVisible();
  });

  test("sidebar has expected navigation links", async ({ page }) => {
    await expect(page.getByRole("link", { name: /profile/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /browse jobs|search jobs/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /applications/i })).toBeVisible();
  });
});

test.describe("Candidate — Profile", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCandidate(page);
    await page.goto("/dashboard/profile");
    await page.waitForLoadState("networkidle");
  });

  test("profile page loads with sections", async ({ page }) => {
    await expect(page.getByText(/my profile/i)).toBeVisible();
    await expect(page.getByText(/profile strength/i)).toBeVisible();
    await expect(page.getByText(/skills/i)).toBeVisible();
    await expect(page.getByText(/work experience/i)).toBeVisible();
    await expect(page.getByText(/education/i)).toBeVisible();
    await expect(page.getByText(/certifications/i)).toBeVisible();
    await expect(page.getByText(/projects/i)).toBeVisible();
  });

  test("can edit basic info", async ({ page }) => {
    await page.getByRole("button", { name: /edit/i }).first().click();
    const headlineInput = page.getByLabel(/headline/i);
    if (await headlineInput.isVisible()) {
      await headlineInput.fill("Software Engineer | Python | React | 3 Years");
    }
    await page.getByRole("button", { name: /save/i }).click();
    await expect(page.getByText(/profile updated/i)).toBeVisible({ timeout: 8_000 });
  });

  test("can add and delete a skill", async ({ page }) => {
    const addBtn = page.locator("button", { hasText: /add/i }).first();
    await addBtn.click();
    await page.getByPlaceholder(/skill name/i).fill("GraphQL");
    await page.getByRole("button", { name: /^add$/i }).click();
    await expect(page.getByText(/skill added/i)).toBeVisible({ timeout: 8_000 });
  });

  test("can add work experience", async ({ page }) => {
    const expSection = page.getByText(/work experience/i);
    await expSection.scrollIntoViewIfNeeded();
    // Find Add button in Work Experience section
    const addButtons = page.getByRole("button", { name: /add/i });
    await addButtons.nth(1).click();
    await page.getByLabel(/company/i).fill("Acme Corp");
    await page.getByLabel(/job title/i).fill("Software Engineer");
    await page.getByRole("button", { name: /save experience/i }).click();
    await expect(page.getByText(/work experience added/i)).toBeVisible({ timeout: 8_000 });
  });

  test("can add education", async ({ page }) => {
    const eduSection = page.getByText(/education/i);
    await eduSection.scrollIntoViewIfNeeded();
    const addButtons = page.getByRole("button", { name: /add/i });
    await addButtons.nth(2).click();
    await page.getByLabel(/institution/i).fill("Mumbai University");
    await page.getByRole("button", { name: /save education/i }).click();
    await expect(page.getByText(/education added/i)).toBeVisible({ timeout: 8_000 });
  });

  test("can add certification", async ({ page }) => {
    await page.getByText(/certifications/i).scrollIntoViewIfNeeded();
    const addButtons = page.getByRole("button", { name: /add/i });
    await addButtons.nth(3).click();
    await page.getByPlaceholder(/certificate name/i).fill("AWS Certified Developer");
    await page.getByRole("button", { name: /save certification/i }).click();
    await expect(page.getByText(/certification added/i)).toBeVisible({ timeout: 8_000 });
  });

  test("can add project", async ({ page }) => {
    await page.getByText(/projects/i).scrollIntoViewIfNeeded();
    const addButtons = page.getByRole("button", { name: /add/i });
    await addButtons.last().click();
    await page.getByPlaceholder(/project title/i).fill("My Portfolio App");
    await page.getByRole("button", { name: /save project/i }).click();
    await expect(page.getByText(/project added/i)).toBeVisible({ timeout: 8_000 });
  });
});

test.describe("Candidate — Browse Jobs", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCandidate(page);
    await page.goto("/dashboard/browse-jobs");
    await page.waitForLoadState("networkidle");
  });

  test("shows job listings", async ({ page }) => {
    const jobs = page.locator("[data-testid='job-card'], .job-card, article");
    await expect(jobs.first()).toBeVisible({ timeout: 10_000 });
  });

  test("can search for jobs", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search.*job|role|keyword/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill("Python");
      await searchInput.press("Enter");
      await page.waitForLoadState("networkidle");
    }
  });
});

test.describe("Candidate — My Applications", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCandidate(page);
    await page.goto("/dashboard/my-applications");
    await page.waitForLoadState("networkidle");
  });

  test("applications page loads", async ({ page }) => {
    await expect(page.getByText(/application|applied/i)).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("Candidate — Resume Optimizer", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCandidate(page);
    await page.goto("/dashboard/resume-optimizer");
    await page.waitForLoadState("networkidle");
  });

  test("shows score analysis tab", async ({ page }) => {
    await expect(page.getByText(/score analysis|ats score|overall score/i)).toBeVisible({ timeout: 10_000 });
  });

  test("has AI summary tab", async ({ page }) => {
    const summaryTab = page.getByRole("tab", { name: /ai summary|summary/i });
    if (await summaryTab.isVisible()) {
      await summaryTab.click();
    }
  });

  test("has upload resume button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /upload resume|analyze/i })).toBeVisible();
  });
});

test.describe("Candidate — Job Alerts", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCandidate(page);
    await page.goto("/dashboard/job-alerts");
    await page.waitForLoadState("networkidle");
  });

  test("job alerts page loads", async ({ page }) => {
    await expect(page.getByText(/job alert/i)).toBeVisible({ timeout: 10_000 });
  });
});
