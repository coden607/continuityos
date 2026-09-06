import { mkdir, writeFile } from "node:fs/promises";
import process from "node:process";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";

const baseURL = process.env.CONTINUITY_BROWSER_URL || "http://127.0.0.1:4173/";
const revision = process.env.GITHUB_SHA || process.env.CONTINUITY_REVISION;
if (!revision) throw new Error("browser evidence requires an exact revision");

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();

await page.addInitScript(() => {
  window.__continuityVitals = { lcp_ms: 0, cls: 0, inp_ms: 0 };
  new PerformanceObserver(list => {
    for (const entry of list.getEntries()) {
      window.__continuityVitals.lcp_ms = Math.max(window.__continuityVitals.lcp_ms, entry.startTime || 0);
    }
  }).observe({ type: "largest-contentful-paint", buffered: true });
  new PerformanceObserver(list => {
    for (const entry of list.getEntries()) {
      if (!entry.hadRecentInput) window.__continuityVitals.cls += entry.value || 0;
    }
  }).observe({ type: "layout-shift", buffered: true });
  try {
    new PerformanceObserver(list => {
      for (const entry of list.getEntries()) {
        window.__continuityVitals.inp_ms = Math.max(window.__continuityVitals.inp_ms, entry.duration || 0);
      }
    }).observe({ type: "event", buffered: true, durationThreshold: 0 });
  } catch {}
});

const consoleErrors = [];
const requestFailures = [];
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("requestfailed", request => {
  requestFailures.push(`${request.method()} ${request.url()} ${request.failure()?.errorText || "failed"}`);
});

await page.goto(baseURL, { waitUntil: "networkidle" });
await page.locator("#health-badge").waitFor({ state: "visible" });
await page.locator("#api-base").fill("http://127.0.0.1:8000");
await page.locator("#save-api").click();
await page.locator("#prompt").fill("browser release smoke test");
await page.locator("#execute").click();
await page.waitForFunction(() => !document.querySelector("#result")?.textContent?.includes("Executing"));

const resultText = await page.locator("#result").textContent();
const healthState = await page.locator("#health-badge").getAttribute("data-state");
const axe = await new AxeBuilder({ page }).analyze();
const seriousA11y = axe.violations.filter(v => ["serious", "critical"].includes(v.impact));

const ready = await page.evaluate(async () => {
  if (!("serviceWorker" in navigator)) return false;
  await navigator.serviceWorker.ready;
  return Boolean(navigator.serviceWorker.controller || (await navigator.serviceWorker.getRegistration()));
});
if (!ready) throw new Error("service worker did not become ready");

const performance = await page.evaluate(() => ({ ...window.__continuityVitals }));
for (const key of ["lcp_ms", "cls", "inp_ms"]) {
  if (!Number.isFinite(performance[key])) performance[key] = 0;
}

const onlineRequestFailures = [...requestFailures];
await context.setOffline(true);
let offlinePassed = true;
try {
  await page.reload({ waitUntil: "domcontentloaded", timeout: 15000 });
  await page.locator("#execute-form").waitFor({ state: "visible" });
} catch {
  offlinePassed = false;
}
await context.setOffline(false);

const e2ePassed =
  consoleErrors.length === 0 &&
  onlineRequestFailures.length === 0 &&
  healthState === "healthy" &&
  Boolean(resultText) &&
  !resultText.includes("Execution failed");

const evidence = {
  revision,
  captured_at: new Date().toISOString(),
  tool: "playwright+axe-core+performance-observer",
  e2e_passed: e2ePassed,
  accessibility_passed: seriousA11y.length === 0,
  pwa_passed: ready && offlinePassed,
  performance,
  details: {
    accessibility_violations: seriousA11y.map(v => ({ id: v.id, impact: v.impact, help: v.help })),
    console_errors: consoleErrors,
    online_request_failures: onlineRequestFailures,
    runtime_health: healthState,
    execute_result: resultText,
    offline_reload_passed: offlinePassed,
  },
};

await mkdir(new URL("../../../.continuity/", import.meta.url), { recursive: true });
await writeFile(
  new URL("../../../.continuity/browser-evidence.json", import.meta.url),
  `${JSON.stringify(evidence, null, 2)}\n`,
  "utf8",
);
console.log(`CONTINUITY_BROWSER_EVIDENCE=${JSON.stringify(evidence)}`);
await browser.close();

if (!evidence.e2e_passed || !evidence.accessibility_passed || !evidence.pwa_passed) process.exitCode = 1;
