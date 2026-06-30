# Source Routing

Use this file when selecting how to collect public Nowcoder evidence.

## Routes

| Route | Use For | Notes |
|---|---|---|
| Public search endpoint | Small keyword searches for posts, feed items, offer phrases, 面经, 求职进度 and company terms. | Preferred first route. It may change without notice. |
| Public search URL | Manual/browser review when endpoint fetch fails. | Example: `https://www.nowcoder.com/search?type=post&query=<query>&page=1`. |
| RSSHub-style routes | Watching broad discuss/experience surfaces when a route is deployed and current. | Treat as public metadata feed; verify links manually before citing. |
| AnySearch / web search | Cross-check or fallback when Nowcoder blocks script fetches. | Use snippets as discovery only. Open sources before citing important claims. |
| Visible browser/manual review | Use when public pages are JS-heavy, blocked, or require human review. | Do not save cookies, private screenshots, or raw private text. |

## Query Heuristics

For AI PhD career-value work, combine:

- company: `腾讯`, `华为`, `字节`, `阿里`, `百度`, `美团`, `快手`, `商汤`, `小米`, `京东`
- role family: `大模型`, `LLM`, `算法`, `推理`, `infra`, `RAG`, `Agent`, `医疗 AI`, `研究员`
- degree/seniority: `博士`, `博士后`, `校招`, `社招`, `应届`, `0-3年`
- location: `深圳`, `广州`, `香港`, `杭州`, `北京`, `上海`
- offer/salary terms: `offer`, `总包`, `base`, `股票`, `签字费`, `开奖`, `薪资`

Prefer several narrow queries over one broad query.

## Evidence Status

| Signal | Default Confidence | Upgrade Conditions |
|---|---|---|
| Public post title/snippet says `博士 offer` | Low | Link opens publicly, context matches company/city/role, and another independent source supports it. |
| Interview/JD discussion without salary | Low-medium | Multiple posts match official JD requirements. |
| Company/role naming pattern | Medium | Repeated across posts and official career pages. |
| Salary/total comp claim | Low | Needs multiple samples or independent cross-channel confirmation. |

## Third-Party Candidates Audited

Discovery in 2026-06 found these useful as design references, not bundled dependencies:

- `Infinityay/nowcoder-mcp`: Python FastMCP using public Nowcoder search/detail endpoints.
- `DevEverything01/newcoder-mcp-server`: TypeScript MCP using browser-based public search and discussion routes.
- RSSHub `lib/routes/nowcoder/*`: public route patterns for discuss, experience, interview and hots.

Do not copy third-party code into this skill unless a future task explicitly handles license/provenance and source updates.
