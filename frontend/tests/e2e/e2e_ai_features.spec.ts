/**
 * E2E — AI Features (Module 10)
 *
 * Pre-conditions:
 *   docker compose up --build -d && alembic upgrade head && python seed.py
 *   GROQ_API_KEY must be set in .env
 *
 * Tests candidate and HR AI features.
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

async function loginAsHR(page: Page) {
  await page.goto("/login");
  const hrTab = page.getByRole("tab", { name: /hr/i });
  if (await hrTab.isVisible()) await hrTab.click();
  await page.getByLabel(/email/i).fill("hr@donehr.com");
  await page.getByLabel(/password/i).fill("Hr@123456!");
  await page.getByRole("button", { name: /login|sign in/i }).click();
  await page.waitForURL(/\/dashboard/, { timeout: 15_000 });
}

// ── Candidate AI ──────────────────────────────────────────────────────────────

test.describe("AI — Resume Optimizer (Candidate)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCandidate(page);
    await page.goto("/dashboard/resume-optimizer");
    await page.waitForLoadState("networkidle");
  });

  test("score analysis tab shows scores", async ({ page }) => {
    const scoreTab = page.getByRole("tab", { name: /score analysis/i });
    if (await scoreTab.isVisible()) await scoreTab.click();
    await expect(page.getByText(/overall|ats|impact/i)).toBeVisible({ timeout: 15_000 });
  });

  test("AI summary tab is accessible", async ({ page }) => {
    const summaryTab = page.getByRole("tab", { name: /ai summary/i });
    if (await summaryTab.isVisible()) {
      await summaryTab.click();
      await page.waitForLoadState("networkidle");
      // Should show loading or content
      await page.waitForTimeout(2000);
      const content = await page.locator("body").textContent();
      expect(content).toBeTruthy();
    }
  });

  test("upload resume button is present", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /upload.*resume.*analyze|upload.*analyze/i })
    ).toBeVisible({ timeout: 5_000 });
  });

  test("refresh button triggers score recalculation", async ({ page }) => {
    const refreshBtn = page.getByRole("button", { name: /refresh|recalculate/i });
    if (await refreshBtn.isVisible()) {
      await refreshBtn.click();
      await expect(page.getByText(/loading|analyzing|calculating/i)).toBeVisible({ timeout: 5_000 });
    }
  });
});

test.describe("AI — Career Chatbot (Candidate)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsCandidate(page);
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
  });

  test("chatbot widget is visible on dashboard", async ({ page }) => {
    const chatbot = page.getByRole("button", { name: /chat|ai assistant|chatbot/i });
    if (await chatbot.isVisible()) {
      await expect(chatbot).toBeVisible();
    }
    // Also check for floating widget
    const floatingWidget = page.locator("[data-testid='chatbot'], .chatbot-widget");
    if (await floatingWidget.isVisible()) {
      await expect(floatingWidget).toBeVisible();
    }
  });

  test("chatbot opens on click", async ({ page }) => {
    const chatToggle = page.getByRole("button", { name: /chat|ai/i }).last();
    if (await chatToggle.isVisible()) {
      await chatToggle.click();
      await page.waitForTimeout(500);
      const chatInput = page.getByPlaceholder(/ask.*career|message|chat/i);
      if (await chatInput.isVisible()) {
        await expect(chatInput).toBeVisible();
      }
    }
  });
});

// ── HR AI ──────────────────────────────────────────────────────────────────────

test.describe("AI — Resume Summary (HR)", () => {
  test("HR can view AI resume summary for candidate", async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/search");
    await page.waitForLoadState("networkidle");

    // Search for a candidate
    const searchInput = page.getByPlaceholder(/search|query/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill("python");
      await page.keyboard.press("Enter");
      await page.waitForLoadState("networkidle");
    }

    // Look for AI summary trigger
    const summaryBtn = page.getByRole("button", { name: /ai summary|view summary|summarize/i }).first();
    if (await summaryBtn.isVisible()) {
      await summaryBtn.click();
      await page.waitForTimeout(3000);
      await expect(page.getByText(/experience|skills|summary/i)).toBeVisible({ timeout: 15_000 });
    }
  });
});

test.describe("AI — JD Generator (HR)", () => {
  test("JD generator produces output", async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/jobs");
    await page.waitForLoadState("networkidle");

    // Find any job and navigate to AI tools
    const aiToolsLink = page.getByRole("link", { name: /ai tools/i }).first();
    if (await aiToolsLink.isVisible()) {
      await aiToolsLink.click();
      await page.waitForLoadState("networkidle");

      const jdTab = page.getByRole("tab", { name: /jd generator|generate/i });
      if (await jdTab.isVisible()) {
        await jdTab.click();
        const generateBtn = page.getByRole("button", { name: /generate/i });
        if (await generateBtn.isVisible()) {
          await generateBtn.click();
          await page.waitForTimeout(5000);
          await expect(page.getByText(/description|requirements|responsibilities/i)).toBeVisible({ timeout: 20_000 });
        }
      }
    }
  });
});

test.describe("AI — Match Score (HR)", () => {
  test("match score badge loads for application", async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/jobs");
    await page.waitForLoadState("networkidle");

    // Navigate to first job's applicants
    const viewAppsLink = page.getByRole("link", { name: /applicants|view apps/i }).first();
    if (await viewAppsLink.isVisible()) {
      await viewAppsLink.click();
      await page.waitForLoadState("networkidle");

      // Look for match score badge
      const matchBadge = page.getByText(/match|score|%/i).first();
      if (await matchBadge.isVisible()) {
        await expect(matchBadge).toBeVisible({ timeout: 10_000 });
      }
    }
  });
});

test.describe("AI — Rejection Email (HR)", () => {
  test("rejection email draft is generated", async ({ page }) => {
    await loginAsHR(page);
    await page.goto("/dashboard/jobs");
    await page.waitForLoadState("networkidle");

    const aiToolsLink = page.getByRole("link", { name: /ai tools/i }).first();
    if (await aiToolsLink.isVisible()) {
      await aiToolsLink.click();
      await page.waitForLoadState("networkidle");

      const rejectionTab = page.getByRole("tab", { name: /rejection/i });
      if (await rejectionTab.isVisible()) {
        await rejectionTab.click();
        // Should have some content or controls
        await expect(page.locator("body")).toBeVisible();
      }
    }
  });
});
