const fs = require("fs");
const path = require("path");

const ROOT = process.env.OFFERSHOW_RUNTIME_DIR ||
  path.join(process.env.USERPROFILE || "C:\\Users\\Administrator", ".codex", "runtime", "offershow-browser");
const MAIN_PROFILE_DIR = path.join(ROOT, "profile");
const TRANSIENT_PROFILE_ROOT = path.join(ROOT, "profiles");
const OUT_DIR = path.join(ROOT, "out");
const CHROME = process.env.OFFERSHOW_CHROME || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

function loadPlaywrightCore() {
  const candidates = [
    "playwright-core",
    path.join(ROOT, "node_modules", "playwright-core"),
  ];
  const errors = [];
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (err) {
      errors.push(`${candidate}: ${err && err.message ? err.message : err}`);
    }
  }
  throw new Error(`Cannot load playwright-core. Tried: ${errors.join(" | ")}`);
}

const { chromium } = loadPlaywrightCore();

const URLS = {
  home: "https://www.offershow.cn/",
  jobsHome: "https://offershow.cn/jobs/homepage",
  offerList: "https://www.offershow.cn/jobs/offerlist",
};

function ensureDirs(profileDir) {
  fs.mkdirSync(profileDir, { recursive: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

function nowStamp() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function parseArgs(argv) {
  const args = {
    command: "check",
    url: URLS.home,
    waitMs: 0,
    query: "",
    tab: "",
    screenshot: null,
    intervalMs: 20000,
    maxRows: 80,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--") && args.command === "check") {
      args.command = arg;
      continue;
    }
    if (arg === "--url") args.url = argv[++i];
    else if (arg === "--wait-ms") args.waitMs = Number(argv[++i] || 0);
    else if (arg === "--interval-ms") args.intervalMs = Number(argv[++i] || 20000);
    else if (arg === "--max-rows") args.maxRows = Number(argv[++i] || 80);
    else if (arg === "--query") args.query = argv[++i] || "";
    else if (arg === "--tab") args.tab = argv[++i] || "";
    else if (arg === "--screenshot") args.screenshot = true;
    else if (arg === "--no-screenshot") args.screenshot = false;
    else if (arg === "--help" || arg === "-h") args.command = "help";
  }
  if (URLS[args.url]) args.url = URLS[args.url];
  return args;
}

function textSignals(text) {
  const t = (text || "").replace(/\s+/g, " ").trim();
  const hasLoggedIn = /(退出登录|个人中心|我的日程|我的简历|智能代投|投递管理|待投清单)/.test(t);
  const requiresLogin = !hasLoggedIn && /(登录|注册|验证码|手机号|微信扫码|扫码登录|login|sign in)/i.test(t);
  const hasOffer = /(offer|总包|薪资|年薪|月薪|查薪资|开奖|base|股票|期权)/i.test(t);
  const hasSearch = /(搜索|公司|岗位|城市|学历|筛选|职位|查询)/i.test(t);
  return { hasLoggedIn, requiresLogin, hasOffer, hasSearch, textLength: t.length };
}

function defaultScreenshot(args) {
  if (args.screenshot !== null) return args.screenshot;
  return args.command === "check";
}

function profileDirFor(args) {
  if (args.command === "check") {
    return path.join(TRANSIENT_PROFILE_ROOT, `check-${process.pid}-${nowStamp()}`);
  }
  if (args.command === "inspect" && args.waitMs <= 0) {
    return path.join(TRANSIENT_PROFILE_ROOT, `inspect-${process.pid}-${nowStamp()}`);
  }
  return MAIN_PROFILE_DIR;
}

async function launch(args) {
  const profileDir = profileDirFor(args);
  ensureDirs(profileDir);
  const context = await chromium.launchPersistentContext(profileDir, {
    executablePath: CHROME,
    headless: false,
    viewport: { width: 1365, height: 900 },
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const page = context.pages()[0] || await context.newPage();
  page.setDefaultTimeout(15000);
  return { context, page, profileDir };
}

async function summarize(page, label, opts = {}) {
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const title = await page.title().catch(() => "");
  const url = page.url();
  const visibleText = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
  const htmlStats = await page.evaluate(() => {
    const root = document.documentElement;
    const body = document.body;
    const scripts = Array.from(document.scripts).slice(0, 40).map((s) => s.src || "[inline]");
    const appRoots = Array.from(document.querySelectorAll("#app, #root, #__next, [id*=app], [class*=app]")).slice(0, 20).map((el) => ({
      tag: el.tagName.toLowerCase(),
      id: el.id || "",
      cls: el.className || "",
      text: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 160),
    }));
    return {
      htmlLength: root ? root.outerHTML.length : 0,
      bodyLength: body ? body.innerHTML.length : 0,
      bodyTextLength: body ? (body.innerText || "").length : 0,
      scriptCount: document.scripts.length,
      scripts,
      appRoots,
    };
  }).catch((err) => ({ error: String(err && err.message ? err.message : err) }));
  const signals = textSignals(visibleText);
  const links = await page.locator("a").evaluateAll((els) =>
    els.slice(0, 80).map((a) => ({
      text: (a.innerText || a.textContent || "").trim().slice(0, 80),
      href: a.href || "",
    }))
  ).catch(() => []);
  const inputs = await page.locator("input,textarea,select,button").evaluateAll((els) =>
    els.slice(0, 80).map((el) => ({
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute("type") || "",
      placeholder: el.getAttribute("placeholder") || "",
      text: (el.innerText || el.textContent || "").trim().slice(0, 80),
      aria: el.getAttribute("aria-label") || "",
    }))
  ).catch(() => []);
  const out = {
    label,
    collected_at: new Date().toISOString(),
    title,
    url,
    signals,
    htmlStats,
    text_excerpt: visibleText.replace(/\s+/g, " ").trim().slice(0, 1200),
    links,
    controls: inputs,
    privacy_note: "No cookie values, localStorage, auth headers, usernames, or private screenshots are printed. Screenshots are only saved when explicitly enabled or during public reachability checks.",
  };
  const file = path.join(OUT_DIR, `${nowStamp()}-${label}.json`);
  let screenshot = "";
  fs.writeFileSync(file, JSON.stringify(out, null, 2), "utf8");
  if (opts.screenshot) {
    screenshot = path.join(OUT_DIR, `${nowStamp()}-${label}.png`);
    await page.screenshot({ path: screenshot, fullPage: true }).catch(() => {});
  }
  const result = {
    ok: true,
    label,
    title,
    url,
    signals,
    htmlStats,
    output: file,
    note: out.privacy_note,
  };
  if (screenshot) result.screenshot = screenshot;
  console.log(JSON.stringify(result, null, 2));
}

async function stagePage(page, args) {
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  if ((args.tab || "").toLowerCase() === "salary" || args.tab === "薪资") {
    const salaryButton = page.getByRole("button", { name: /^薪资$/ }).first();
    if (await salaryButton.count().catch(() => 0)) {
      await salaryButton.click().catch(() => {});
      await page.waitForTimeout(1200);
    }
  }
  if (args.query) {
    const byPlaceholder = page.locator('input[placeholder*="搜索公司"], input[placeholder*="搜索公司名称"], input[placeholder*="榜单标题"], textarea').first();
    if (await byPlaceholder.count().catch(() => 0)) {
      await byPlaceholder.fill(args.query).catch(() => {});
      await page.keyboard.press("Enter").catch(() => {});
      await page.waitForTimeout(2500);
    } else {
      const candidates = await page.locator("input, textarea").count().catch(() => 0);
      if (candidates === 1) {
        await page.locator("input, textarea").first().fill(args.query).catch(() => {});
        await page.keyboard.press("Enter").catch(() => {});
        await page.waitForTimeout(2500);
      }
    }
  }
}

function redactSensitiveText(value) {
  return String(value || "")
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[redacted-email]")
    .replace(/(?:\+?86[-\s]?)?1[3-9]\d{9}/g, "[redacted-phone]")
    .replace(/(?:微信|VX|WeChat|wechat|qq|QQ)[:：\s-]*[A-Za-z0-9_-]{5,}/g, "[redacted-contact]")
    .replace(/\b[A-Za-z0-9._-]{16,}\b/g, "[redacted-long-id]");
}

function compactText(value, limit = 420) {
  const text = redactSensitiveText(value).replace(/\s+/g, " ").trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, limit)}...`;
}

function inferCandidateFields(text) {
  const t = String(text || "");
  const cityMatch = t.match(/(深圳|广州|上海|北京|杭州|香港|东莞|珠海|佛山|成都|南京|苏州|武汉|西安)/);
  const degreeMatch = t.match(/(博士|硕士|本科|研究生|不限)/);
  const salaryPeriod =
    /(总包|年包|年薪|package|TC|total)/i.test(t) ? "total_comp" :
    /(月薪|月base|base|k\/月|K\/月)/i.test(t) ? "monthly" :
    /(年base|基本年薪)/i.test(t) ? "annual_base" :
    /(薪资|开奖|offer|base|股票|期权|签字费|补贴)/i.test(t) ? "unknown" :
    "not_salary";
  const jobFamily =
    /(Agent|智能体|RAG|检索增强|知识库)/i.test(t) ? "Agent/RAG" :
    /(infra|推理|训练|CUDA|算子| serving |服务|高性能|大模型平台)/i.test(t) ? "LLM Infra" :
    /(医疗|医学|医药|影像|临床)/i.test(t) ? "医疗AI" :
    /(评测|evaluation|eval|推理|reasoning)/i.test(t) ? "LLM Reasoning/Eval" :
    /(大模型|LLM|NLP|算法|机器学习|深度学习)/i.test(t) ? "大模型算法" :
    "";
  const salarySignal = compactText((t.match(/.{0,24}(总包|年薪|月薪|base|股票|期权|签字费|补贴|开奖|offer).{0,80}/i) || [""])[0], 160);
  const companyMatch = t.match(/(?:公司|企业|雇主|厂商)[:：]?\s*([\u4e00-\u9fa5A-Za-z0-9（）()&.\-]{2,24})/);
  return {
    company: companyMatch ? compactText(companyMatch[1], 40) : "",
    city: cityMatch ? cityMatch[1] : "",
    degree: degreeMatch ? degreeMatch[1] : "",
    job_family: jobFamily,
    salary_period: salaryPeriod,
    salary_signal: salarySignal,
  };
}

async function collectVisibleCandidates(page, maxRows) {
  const raw = await page.evaluate((limit) => {
    const selector = [
      "article",
      "li",
      "tr",
      "[class*=card]",
      "[class*=item]",
      "[class*=list]",
      "[class*=salary]",
      "[class*=offer]",
      "[class*=company]",
      "[class*=rank]",
    ].join(",");
    const keywords = /(offer|薪资|总包|年薪|月薪|base|股票|期权|签字费|补贴|公司|岗位|城市|学历|博士|硕士|大模型|算法)/i;
    const nodes = Array.from(document.querySelectorAll(selector));
    const seen = new Set();
    const rows = [];
    function isVisible(el) {
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return rect.width > 20 && rect.height > 8 && style.visibility !== "hidden" && style.display !== "none";
    }
    function scoreText(text) {
      let score = 0;
      if (/(offer|薪资|总包|年薪|月薪|base|股票|期权|签字费|补贴)/i.test(text)) score += 4;
      if (/(公司|岗位|城市|学历|博士|硕士|大模型|算法)/i.test(text)) score += 2;
      if (/(深圳|广州|上海|北京|杭州|香港|博士|硕士)/.test(text)) score += 2;
      if (text.length >= 20 && text.length <= 900) score += 1;
      if (text.length > 1200) score -= 2;
      if (/(暂时没有符合条件|扫描关注|官方小程序|开通校招信息会员|校招信息会员|简历会员|机会雷达|企业入口|登录)/.test(text)) score -= 4;
      if (/(OfferShow AI网页版上线|免费领会员|求职会员卡|智能代投|告别写简历|AI简历)/i.test(text)) score -= 8;
      return score;
    }
    for (const el of nodes) {
      if (!isVisible(el)) continue;
      const text = (el.innerText || el.textContent || "").replace(/\s+/g, " ").trim();
      if (!text || !keywords.test(text)) continue;
      const key = text.slice(0, 260);
      if (seen.has(key)) continue;
      seen.add(key);
      const rect = el.getBoundingClientRect();
      const score = scoreText(text);
      if (score < 6) continue;
      if (rect.width > 1100 && /(AI OfferShow|求职日历|会员中心|暂时没有符合条件)/.test(text)) continue;
      rows.push({
        tag: el.tagName.toLowerCase(),
        class_name: String(el.className || "").slice(0, 120),
        text,
        score,
        rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) },
      });
    }
    return rows.sort((a, b) => b.score - a.score).slice(0, limit || 80);
  }, Math.max(1, maxRows || 80));
  return raw.map((row, index) => {
    const visibleHint = compactText(row.text, 520);
    return {
      candidate_id: `ovh-${String(index + 1).padStart(3, "0")}`,
      visible_hint: visibleHint,
      inferred: inferCandidateFields(row.text),
      dom_hint: {
        tag: row.tag,
        class_name: compactText(row.class_name, 120),
        score: row.score,
        rect: row.rect,
      },
    };
  });
}

async function inspect(args) {
  const { context, page, profileDir } = await launch(args);
  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 }).catch(() => {});
  await stagePage(page, args);
  if (args.waitMs > 0) {
    console.log(JSON.stringify({
      status: "browser_opened_for_inspection",
      instruction: "Optionally navigate/filter in the visible browser. This command records only DOM/resource names and redacted visible candidates.",
      profile_dir: profileDir,
      no_secrets_printed: true,
    }, null, 2));
    await page.waitForTimeout(args.waitMs);
  }
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const resourceHints = await page.evaluate(() =>
    performance.getEntriesByType("resource")
      .map((entry) => {
        try {
          const u = new URL(entry.name);
          return {
            host: u.host,
            path: u.pathname,
            initiator_type: entry.initiatorType || "",
          };
        } catch {
          return { host: "", path: String(entry.name || "").slice(0, 160), initiator_type: entry.initiatorType || "" };
        }
      })
      .filter((entry) => /offershow|api|salary|offer|uuid|js\//i.test(`${entry.host}${entry.path}`))
      .slice(0, 160)
  ).catch(() => []);
  const candidates = await collectVisibleCandidates(page, args.maxRows);
  const title = await page.title().catch(() => "");
  const out = {
    label: "inspect",
    collected_at: new Date().toISOString(),
    title,
    url: page.url(),
    resource_hints: resourceHints,
    candidate_count: candidates.length,
    candidates,
    privacy_note: "No cookies, tokens, localStorage, request headers, usernames, contacts, or screenshots are collected. Candidate hints are redacted and truncated visible text only.",
  };
  const file = path.join(OUT_DIR, `${nowStamp()}-inspect.json`);
  fs.writeFileSync(file, JSON.stringify(out, null, 2), "utf8");
  console.log(JSON.stringify({
    ok: true,
    title,
    url: out.url,
    output: file,
    resource_hints: resourceHints.slice(0, 20),
    candidate_count: candidates.length,
    candidates: candidates.slice(0, 12),
    note: out.privacy_note,
  }, null, 2));
  await context.close();
}

async function exportVisible(args) {
  const { context, page, profileDir } = await launch(args);
  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 }).catch(() => {});
  await stagePage(page, args);
  console.log(JSON.stringify({
    status: "browser_opened_for_visible_export",
    instruction: "Use the visible browser to filter Offershow. This command exports redacted/truncated visible candidate hints for later human review; it does not append ledger rows automatically.",
    profile_dir: profileDir,
    wait_ms: args.waitMs || 60000,
    query: args.query || "",
    no_secrets_printed: true,
  }, null, 2));
  if (args.waitMs > 0) await page.waitForTimeout(args.waitMs);
  const candidates = await collectVisibleCandidates(page, args.maxRows);
  const title = await page.title().catch(() => "");
  const out = {
    label: "export-visible",
    collected_at: new Date().toISOString(),
    title,
    url: page.url(),
    query: args.query || "",
    candidate_count: candidates.length,
    candidates,
    review_instruction: "Create a review CSV from this JSON, select only rows you personally verified, and write a short human_summary before appending to a salary ledger.",
    privacy_note: "No cookies, tokens, localStorage, request headers, usernames, contacts, or screenshots are collected. Candidate hints are redacted and truncated visible text only.",
  };
  const file = path.join(OUT_DIR, `${nowStamp()}-export-visible.json`);
  fs.writeFileSync(file, JSON.stringify(out, null, 2), "utf8");
  console.log(JSON.stringify({
    ok: true,
    title,
    url: out.url,
    output: file,
    candidate_count: candidates.length,
    candidates: candidates.slice(0, 12),
    note: out.privacy_note,
  }, null, 2));
  await context.close();
}

async function check(args) {
  const { context, page } = await launch(args);
  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 }).catch((err) => {
    console.log(JSON.stringify({ ok: false, stage: "goto", error: String(err.message || err) }, null, 2));
  });
  if (args.waitMs > 0) await page.waitForTimeout(args.waitMs);
  await summarize(page, "check", { screenshot: defaultScreenshot(args) });
  await context.close();
}

async function login(args) {
  const { context, page, profileDir } = await launch(args);
  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 }).catch(() => {});
  console.log(JSON.stringify({
    status: "browser_opened",
    instruction: "Complete Offershow login/CAPTCHA/MFA manually in the visible browser. This helper will only poll visible page text and save a redacted status summary.",
    profile_dir: profileDir,
    no_secrets_printed: true,
  }, null, 2));
  const deadline = Date.now() + (args.waitMs || 240000);
  let last = null;
  while (Date.now() < deadline) {
    await page.waitForTimeout(5000);
    const text = await page.locator("body").innerText({ timeout: 3000 }).catch(() => "");
    const sig = textSignals(text);
    last = sig;
    if (sig.hasLoggedIn || (!sig.requiresLogin && (sig.hasOffer || sig.hasSearch))) break;
  }
  await summarize(page, "login-status", { screenshot: defaultScreenshot(args) });
  console.log(JSON.stringify({ login_poll_result: last }, null, 2));
  await context.close();
}

async function sample(args) {
  const { context, page } = await launch(args);
  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 }).catch(() => {});
  await stagePage(page, args);
  console.log(JSON.stringify({
    status: "browser_opened_for_sampling",
    instruction: "Use the visible browser to filter Offershow. When the page shows the desired results, leave it open until polling finishes. No cookies or raw private data are printed.",
    query: args.query || "",
  }, null, 2));
  if (args.waitMs > 0) await page.waitForTimeout(args.waitMs);
  await summarize(page, "sample-visible", { screenshot: defaultScreenshot(args) });
  await context.close();
}

async function record(args) {
  const { context, page, profileDir } = await launch(args);
  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 }).catch(() => {});
  await stagePage(page, args);
  const waitMs = args.waitMs || 180000;
  const intervalMs = Math.max(5000, args.intervalMs || 20000);
  const deadline = Date.now() + waitMs;
  let count = 0;
  console.log(JSON.stringify({
    status: "browser_opened_for_recording",
    instruction: "Use the visible browser manually. This helper periodically saves redacted visible-page summaries only; it does not read cookies, tokens, localStorage, request headers, or raw private messages. Close nothing until the timer ends.",
    profile_dir: profileDir,
    wait_ms: waitMs,
    interval_ms: intervalMs,
    query: args.query || "",
  }, null, 2));
  while (Date.now() < deadline) {
    count += 1;
    await summarize(page, `record-${String(count).padStart(2, "0")}`, { screenshot: defaultScreenshot(args) });
    const remaining = deadline - Date.now();
    if (remaining <= 0) break;
    await page.waitForTimeout(Math.min(intervalMs, remaining));
  }
  await context.close();
  console.log(JSON.stringify({ ok: true, status: "recording_finished", snapshots: count, out_dir: OUT_DIR }, null, 2));
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.command === "help") {
    console.log(`Usage:
  node offershow_helper.js check --url home
  node offershow_helper.js login --url home --wait-ms 240000
  node offershow_helper.js sample --url home --tab salary --query "腾讯" --wait-ms 60000
  node offershow_helper.js record --url home --tab salary --query "腾讯" --wait-ms 180000 --interval-ms 20000
  node offershow_helper.js inspect --url home --tab salary --query "腾讯" --wait-ms 60000 --max-rows 80
  node offershow_helper.js export-visible --url home --tab salary --query "腾讯" --wait-ms 60000 --max-rows 80

URLs: home, jobsHome, offerList, or a full URL.
Screenshots: public check saves one by default; login/sample/record do not unless --screenshot is passed.
Outputs: ${OUT_DIR}
Profile: ${MAIN_PROFILE_DIR}`);
    return;
  }
  if (args.command === "login") return login(args);
  if (args.command === "sample") return sample(args);
  if (args.command === "record") return record(args);
  if (args.command === "inspect") return inspect(args);
  if (args.command === "export-visible") return exportVisible(args);
  return check(args);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, error: String(err && err.stack ? err.stack : err) }, null, 2));
  process.exitCode = 1;
});
