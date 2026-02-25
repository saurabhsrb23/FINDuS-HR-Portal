/**
 * E2E tests: Chat System (Module 9)
 *
 * Pre-conditions:
 *   - Full stack is running: docker compose up --build -d
 *   - Alembic migration 009 has been applied
 *   - seed.py executed (candidate@donehr.com / hr@donehr.com exist)
 *
 * Scenarios:
 *   1. Messages nav item appears in sidebar with correct icon
 *   2. HR can open Messages page and see empty inbox
 *   3. HR can open New Conversation modal and search for a user
 *   4. Candidate navigates to Messages, sees sidebar item
 *   5. Admin can access Chat Monitor page and see stats
 */

import { expect, Page, test } from "@playwright/test";

const BASE = process.env.BASE_URL ?? "http://localhost:3000";

const CANDIDATE_EMAIL = "candidate@donehr.com";
const CANDIDATE_PW = "Candidate@1!";
const HR_EMAIL = "hr@donehr.com";
const HR_PW = "Hr@123456!";
const ADMIN_EMAIL = "admin@donehr.com";
const ADMIN_PW = "Admin@2024!";
const ADMIN_PIN = "654321";

// ── Helpers ───────────────────────────────────────────────────────────────────

async function loginAsCandidate(page: Page) {
  await page.goto(`${BASE}/login`);
  await page.fill('input[type="email"]', CANDIDATE_EMAIL);
  await page.fill('input[type="password"]', CANDIDATE_PW);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/dashboard/, { timeout: 15000 });
}

async function loginAsHR(page: Page) {
  await page.goto(`${BASE}/login`);
  // Switch to HR tab if present
  const hrTab = page.getByRole("tab", { name: /hr/i });
  if (await hrTab.isVisible({ timeout: 2000 }).catch(() => false)) {
    await hrTab.click();
  }
  await page.fill('input[type="email"]', HR_EMAIL);
  await page.fill('input[type="password"]', HR_PW);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/dashboard/, { timeout: 15000 });
}

async function loginAsAdmin(page: Page) {
  await page.goto(`${BASE}/admin/login`);
  await page.fill('input[name="email"]', ADMIN_EMAIL);
  await page.fill('input[name="password"]', ADMIN_PW);
  await page.fill('input[name="pin"]', ADMIN_PIN);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/admin\/dashboard/, { timeout: 15000 });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe("Chat System — Module 9", () => {
  test("1. Messages nav item appears in HR sidebar", async ({ page }) => {
    await loginAsHR(page);
    // Wait for sidebar
    const messagesLink = page.getByRole("link", { name: /messages/i });
    await expect(messagesLink).toBeVisible({ timeout: 10000 });
    await expect(messagesLink).toHaveAttribute("href", "/dashboard/messages");
  });

  test("2. HR can navigate to Messages page and view empty inbox", async ({ page }) => {
    await loginAsHR(page);
    await page.click('a[href="/dashboard/messages"]');
    await page.waitForURL(/\/dashboard\/messages/, { timeout: 10000 });

    // Inbox heading
    await expect(page.getByRole("heading", { name: /messages/i })).toBeVisible();

    // Search bar present
    await expect(
      page.getByPlaceholder(/search conversations/i)
    ).toBeVisible();
  });

  test("3. New Conversation modal opens and accepts search input", async ({ page }) => {
    await loginAsHR(page);
    await page.goto(`${BASE}/dashboard/messages`);

    // Click + button to open new chat modal
    const newChatBtn = page.getByTitle("New conversation");
    await expect(newChatBtn).toBeVisible({ timeout: 10000 });
    await newChatBtn.click();

    // Modal appears
    await expect(
      page.getByRole("heading", { name: /new conversation/i })
    ).toBeVisible();

    // Search box auto-focused
    const searchInput = page.getByPlaceholder(/search by name or email/i);
    await expect(searchInput).toBeVisible();

    // Type a query
    await searchInput.fill("candidate");
    // Wait a bit for search debounce
    await page.waitForTimeout(500);

    // Close modal
    await page.keyboard.press("Escape");
  });

  test("4. Candidate can navigate to Messages page", async ({ page }) => {
    await loginAsCandidate(page);

    // Messages link in sidebar
    const messagesLink = page.getByRole("link", { name: /messages/i });
    await expect(messagesLink).toBeVisible({ timeout: 10000 });

    await messagesLink.click();
    await page.waitForURL(/\/dashboard\/messages/, { timeout: 10000 });

    // Inbox shown
    await expect(page.getByText(/no conversations yet/i).or(
      page.getByPlaceholder(/search conversations/i)
    )).toBeVisible();
  });

  test("5. Admin Chat Monitor page loads with stats", async ({ page }) => {
    await loginAsAdmin(page);

    // Chat Monitor in admin sidebar
    const chatLink = page.getByRole("link", { name: /chat monitor/i });
    await expect(chatLink).toBeVisible({ timeout: 10000 });
    await chatLink.click();

    await page.waitForURL(/\/admin\/chat/, { timeout: 10000 });
    await expect(
      page.getByRole("heading", { name: /chat monitor/i })
    ).toBeVisible();

    // Stats cards present
    await expect(page.getByText(/messages today/i)).toBeVisible();
    await expect(page.getByText(/total conversations/i)).toBeVisible();
  });
});
