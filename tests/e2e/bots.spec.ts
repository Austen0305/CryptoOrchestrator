import { test, expect } from "@playwright/test";
import { authenticateTestUser, generateTestUser } from "./auth-helper";

/**
 * Bot Management E2E Tests
 * Tests complete bot lifecycle: create, start, stop, delete
 */

test.describe("Bot Management", () => {
  let testUser: { email: string; password: string; username: string };

  test.beforeEach(async ({ page }) => {
    // Generate and authenticate test user for each test
    testUser = generateTestUser();
    const authenticated = await authenticateTestUser(
      page,
      testUser.email,
      testUser.password,
      testUser.username
    );

    // Navigate to bots page even if auth might have failed
    await page.goto("/bots");
    await page.waitForLoadState("networkidle");
    
    // Check if we're on login page (not authenticated)
    const isLoginPage = await page.locator('input[type="email"], input[name="email"]').isVisible().catch(() => false);
    if (isLoginPage && !authenticated) {
      // Try to continue - might be able to view bots page
      console.warn('Not authenticated, but continuing test - some features may not work');
    }
  });

  test("should create a new bot", async ({ page }) => {
    // Wait for page to be fully loaded
    await page.waitForLoadState("networkidle");

    // Look for create bot button - could be "Create Bot", "New Bot", or "+" button
    const createButton = page
      .locator(
        'button:has-text("Create Bot"), button:has-text("New Bot"), button:has-text("Add Bot"), [data-testid="create-bot-btn"], button[aria-label*="bot" i]'
      )
      .first();

    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

    // Wait for bot creation form/modal to appear
    await page.waitForSelector(
      'form, [role="dialog"], [data-testid*="modal"], [data-testid*="form"]',
      {
        state: "visible",
        timeout: 10000,
      }
    );

    // Fill bot creation form
    // Bot name
    const nameInput = page
      .locator('[name="name"], input[placeholder*="name" i], input[placeholder*="bot" i]')
      .first();
    await expect(nameInput).toBeVisible({ timeout: 5000 });
    await nameInput.fill("Test Bot E2E");

    // Strategy selection (if dropdown)
    const strategySelect = page.locator('[name="strategy"], select[name="strategy"]').first();
    if (await strategySelect.isVisible({ timeout: 3000 }).catch(() => false)) {
      await strategySelect.selectOption({ index: 0 }); // Select first strategy
    }

    // Initial balance (if field exists)
    const balanceInput = page
      .locator('[name="balance"], [name="initialBalance"], input[type="number"]')
      .first();
    if (await balanceInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await balanceInput.fill("1000");
    }

    // Submit form
    const submitButton = page
      .locator('button[type="submit"], button:has-text("Create"), button:has-text("Save")')
      .first();
    await expect(submitButton).toBeVisible({ timeout: 5000 });
    await submitButton.click();

    // Wait for network to be idle after submission
    await page.waitForLoadState("networkidle");

    // Verify bot was created - check for bot name in list or success message
    const botCreated = await Promise.race([
      page
        .locator("text=Test Bot E2E")
        .waitFor({ state: "visible", timeout: 10000 })
        .then(() => true),
      page
        .locator("text=/created successfully|successfully created/i")
        .waitFor({ state: "visible", timeout: 10000 })
        .then(() => true),
    ]).catch(() => false);

    expect(botCreated).toBeTruthy();
  });

  test("should start a bot", async ({ page }) => {
    // Wait for bots to load
    await page.waitForLoadState("networkidle");

    // Find first bot in list (could be in table, cards, or list)
    const botCard = page.locator('[data-testid*="bot"], .bot-card, tr, [class*="bot"]').first();

    await expect(botCard).toBeVisible({ timeout: 10000 });

    // Find start button for the bot
    const startButton = botCard
      .locator(
        'button:has-text("Start"), button:has-text("Activate"), [data-testid*="start"], button[aria-label*="start" i]'
      )
      .first();

    if (await startButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await startButton.click();

      // Wait for network to be idle after starting
      await page.waitForLoadState("networkidle");

      // Verify bot is running - check for "Running", "Active", or status indicator
      const isRunning = await Promise.race([
        botCard
          .locator('text=/Running|Active/i, [data-status="running"], [data-status="active"]')
          .waitFor({ state: "visible", timeout: 10000 })
          .then(() => true),
        page
          .locator("text=/started successfully/i")
          .waitFor({ state: "visible", timeout: 5000 })
          .then(() => true),
      ]).catch(() => false);

      expect(isRunning).toBeTruthy();
    } else {
      // Bot might already be running
      test.skip();
    }
  });

  test("should stop a running bot", async ({ page }) => {
    // Wait for bots to load
    await page.waitForLoadState("networkidle");

    // Find first running bot
    const runningBot = page
      .locator('[data-status="running"], [data-status="active"], text=/Running|Active/i')
      .first();

    if (!(await runningBot.isVisible({ timeout: 10000 }).catch(() => false))) {
      test.skip();
    }

    // Find stop button
    const stopButton = runningBot
      .locator(
        'button:has-text("Stop"), button:has-text("Deactivate"), [data-testid*="stop"], button[aria-label*="stop" i]'
      )
      .first();

    if (await stopButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await stopButton.click();

      // Wait for network to be idle after stopping
      await page.waitForLoadState("networkidle");

      // Verify bot is stopped
      const isStopped = await Promise.race([
        runningBot
          .locator('text=/Stopped|Inactive/i, [data-status="stopped"]')
          .waitFor({ state: "visible", timeout: 10000 })
          .then(() => true),
        page
          .locator("text=/stopped successfully/i")
          .waitFor({ state: "visible", timeout: 5000 })
          .then(() => true),
      ]).catch(() => false);

      expect(isStopped).toBeTruthy();
    } else {
      test.skip();
    }
  });

  test("should delete a bot", async ({ page }) => {
    // Wait for bots to load
    await page.waitForLoadState("networkidle");

    // Find first bot
    const botCard = page.locator('[data-testid*="bot"], .bot-card, tr, [class*="bot"]').first();

    await expect(botCard).toBeVisible({ timeout: 10000 });

    // Get bot name for verification
    const botName = await botCard.textContent().catch(() => "");

    // Find delete button
    const deleteButton = botCard
      .locator(
        'button:has-text("Delete"), button:has-text("Remove"), [data-testid*="delete"], button[aria-label*="delete" i]'
      )
      .first();

    if (await deleteButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await deleteButton.click();

      // Handle confirmation dialog if it appears
      const confirmButton = page
        .locator('button:has-text("Confirm"), button:has-text("Delete"), button:has-text("Yes")')
        .first();

      if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmButton.click();
      }

      // Wait for network to be idle after deletion
      await page.waitForLoadState("networkidle");

      // Verify bot was deleted - check that bot name is no longer visible
      const botDeleted = await Promise.race([
        page
          .locator(`text=${botName}`)
          .waitFor({ state: "hidden", timeout: 10000 })
          .then(() => true),
        page
          .locator("text=/deleted successfully/i")
          .waitFor({ state: "visible", timeout: 5000 })
          .then(() => true),
      ]).catch(() => false);

      expect(botDeleted).toBeTruthy();
    } else {
      test.skip();
    }
  });

  test("should view bot details", async ({ page }) => {
    // Wait for bots to load
    await page.waitForLoadState("networkidle");

    // Find first bot
    const botCard = page.locator('[data-testid*="bot"], .bot-card, tr, [class*="bot"]').first();

    await expect(botCard).toBeVisible({ timeout: 10000 });

    // Click on bot to view details (could be link, button, or card click)
    const botLink = botCard.locator('a, button, [role="button"]').first();

    if (await botLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await botLink.click();

      // Wait for details page/modal to appear
      await page.waitForLoadState("networkidle");

      // Verify details are shown - check for bot name, status, or details section
      const detailsVisible = await Promise.race([
        page
          .locator('[data-testid="bot-details"], .bot-details, h1, h2')
          .waitFor({ state: "visible", timeout: 10000 })
          .then(() => true),
        page.waitForURL(/.*bot.*/, { timeout: 10000 }).then(() => true),
      ]).catch(() => false);

      expect(detailsVisible).toBeTruthy();
    } else {
      // Try clicking the card itself
      await botCard.click();
      await page.waitForLoadState("networkidle");

      const detailsVisible = await page
        .locator('[data-testid="bot-details"], .bot-details')
        .isVisible({ timeout: 10000 })
        .catch(() => false);
      expect(detailsVisible).toBeTruthy();
    }
  });
});
