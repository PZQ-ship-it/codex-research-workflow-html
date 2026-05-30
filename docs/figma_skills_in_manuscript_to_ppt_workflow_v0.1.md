# Figma Context MCP in Manuscript-to-PPT Workflow v0.2

## 1. Migration Decision

This document supersedes the earlier official-Figma-MCP design notes.

Default providers:

- Use `GLips/Figma-Context-MCP`, now commonly surfaced as Framelink Figma MCP / `figma-developer-mcp`.
- Configure it in Codex as `figma_context`.
- Treat it as a read-only design-context and image-download layer.
- Configure official Figma MCP separately as `figma_write` for explicit official write or exempt-tool lanes.

Default non-goal:

- Do not use official Figma Remote MCP as the normal context-reading workflow path.
- Do not make `figma-use` or `use_figma` mandatory in `manuscript-to-ppt-workflow`.
- Do not promise that the workflow can create or update Figma frames unless the user explicitly opts into an official-write exception.

Reason:

- The official MCP path is quota-limited in practice.
- The open-source GLips/Framelink server is the target migration path for reading Figma context without spending official MCP calls.
- The PPT workflow needs reliable local PPTX output and screenshot QA more than Figma write-back.

## 2. New Capability Model

Figma capabilities are split into two separate lanes:

| Lane | Default provider | Default status | Purpose |
|---|---|---|---|
| Figma context | GLips/Framelink `figma-developer-mcp` | enabled when needed | Read file/node layout, style, and downloadable image context. |
| Figma write/edit | official Figma MCP as `figma_write` | disabled | Create or update Figma files/frames only after explicit user confirmation. |

This distinction is important. GLips/Framelink is not a drop-in replacement for `use_figma`. It should guide local PPTX, HTML, SVG, PNG, or screenshot workflows rather than editing Figma by default.

## 3. Capability Routing Matrix

Use this matrix when deciding whether a Figma-related task should use the open-source MCP, the official MCP, or stay out of the default PPT workflow.

| Capability or task | Default route | Provider/tool | Why |
|---|---|---|---|
| Read Figma file/node structure, text, layout, colors, components, and styles | Open-source | GLips/Framelink `get_figma_data` | This is the main purpose of `figma-developer-mcp`; avoids official MCP read-call quota. |
| Download Figma image/vector assets for local reuse | Open-source | GLips/Framelink `download_figma_images` | Writes only to local `image-dir`, not to Figma; suitable for PPTX/HTML asset workflows. |
| Use a Figma file as template/style/design-system reference for a PPT deck | Open-source, separate experiment | `figma-context-mcp` plus local PPTX/HTML/SVG tooling | The default PPT workflow does not spawn a Figma polish agent; Figma remains a reference source. |
| Repair selected PPT slides using Figma-derived spacing, hierarchy, typography, or assets | Open-source first | GLips/Framelink context + local PPTX/HTML/SVG tooling | The repair should happen locally unless the user explicitly asks to edit Figma. |
| Capture a live web app or local HTML UI into editable Figma layers | Official only | `generate_figma_design` / Code to canvas | This is an official remote MCP write/capture feature; GLips cannot create Figma layers. |
| Create or edit native Figma frames, pages, components, variants, variables, styles, auto layout, or Slides content | Official only, explicit | `use_figma` + `figma-use` | Requires official write-to-canvas, Full seat for Figma file writes, and edit permission. |
| Create a new blank Figma Design/FigJam/Slides file | Official only, explicit | `create_new_file` | Remote-only official tool; not available in GLips. |
| Upload local PNG/JPG/GIF/WebP into a Figma file or set an image fill | Official only, explicit | `upload_assets` | Writes assets into Figma; not supported by GLips. |
| Generate FigJam flowchart, ERD, sequence, state, Gantt, or architecture diagrams | Official only, optional | `generate_diagram` | Official FigJam generation; useful for diagrams, but not part of PPT default path. |
| Search Figma design libraries for components, variables, and styles | Official only, read-budget aware | `search_design_system`, `get_libraries` | Requires official remote MCP/library access and may consume read quota. Use only when library reuse matters. |
| Read official design context with screenshots/code-oriented output | Prefer open-source; official only when needed | GLips `get_figma_data`; official `get_design_context`, `get_metadata`, `get_screenshot`, `get_variable_defs` | GLips covers most context reads. Official reads can be richer but consume official read quota. |
| Code Connect mapping lookup/suggestions | Official only, optional | `get_code_connect_map`, `get_code_connect_suggestions`, `get_context_for_code_connect` | Specific to Figma Code Connect workflows, not PPT generation. |
| Write Code Connect mappings | Official only, optional | `add_code_connect_map`, `send_code_connect_mappings` | Official write-side Code Connect tools; outside the PPT default path. |
| Check authenticated user, plans, and seat types | Official only, diagnostic | `whoami` | Use only to diagnose official MCP permission/seat issues. |
| Full-deck Figma rebuild | Do not use by default | none | Too expensive, harms PPTX editability, and makes Figma a hard dependency. |

Default decision rule:

1. If the task can be satisfied by reading Figma context or downloading assets, use GLips/Framelink.
2. If the task creates or edits Figma-native objects, it requires official MCP and explicit user confirmation.
3. If the official task is only a read convenience, avoid it unless GLips output is insufficient and the quota cost is acceptable.
4. If the task is unrelated to PPT delivery, such as Code Connect or design-system library maintenance, keep it out of the manuscript-to-PPT main chain.

Official MCP quota/permission notes:

- Official rate limits apply to MCP tools that read data from Figma.
- Official docs currently list `add_code_connect_map`, `generate_figma_design`, and `whoami` as exempt from standard read-tool rate limits.
- `use_figma` is the official write-to-canvas path, but it should still be treated as explicit-only because it requires the right seat/edit permission and beta-quality review.
- Professional with View/Collab seat can still be limited to 6/month; Professional with Dev/Full seat is much higher for read tools. Use `whoami` to confirm the actual seat when official MCP is enabled.

## 4. Workflow Policy

`manuscript-to-ppt-workflow` should record provider and policy fields instead of the old single `figma_policy`:

```yaml
figma_context_policy: disabled | optional | required
figma_write_policy: disabled | official-exempt-only | official-write-explicit
figma_context_provider: glips-framelink
figma_write_provider: figma_write
```

Recommended defaults:

```yaml
figma_context_policy: optional
figma_write_policy: disabled
figma_context_provider: glips-framelink
figma_write_provider: figma_write
```

The deep-interview gate should clarify:

- Is there a Figma file or selected node that should be used as visual reference?
- Is Figma being used for template/style context, source assets, or design-system guidance?
- Is any Figma write/edit operation required, or is read-only context enough?
- If whole-slide images are proposed, does the user accept the editability tradeoff?

If the user does not explicitly request Figma write/edit, keep `figma_write_policy: disabled`.

Use `official-exempt-only` when the intended official operation is limited to documented exempt tools such as `generate_figma_design`, `add_code_connect_map`, or `whoami`. Use `official-write-explicit` when the run may call broader write tools such as `use_figma`, `create_new_file`, `upload_assets`, or `generate_diagram`.

## 5. Skill And Agent Roles

### `figma-context-mcp`

Use this skill when a task needs Figma context through GLips/Framelink.

Responsibilities:

- verify the task is read/context only
- require a Figma file URL or node-specific URL
- fetch layout/style/node context through `figma_context`
- download only needed assets into `generated_assets/figma/`
- record source URL, file key, node id, asset paths, and limitations

### Historical `figma_layout_polish`

This native agent spec is retained as historical migration material under `agent/deprecated-native-agents/figma-layout-polish.toml.disabled`. It is not active in `.codex/agents/` and should not be part of the default manuscript-to-PPT lane.

If the workflow is deliberately changed to run a separate Figma experiment, its bounded role would be selected-page layout repair using Figma context:

- consume GLips/Framelink context, downloaded images, PPTX screenshots, and page intent
- propose or create local PPTX/layout fixes and local visual assets
- preserve editability where possible
- return before/after screenshot evidence and a traceable manifest

It must not call official Figma tools unless the parent prompt explicitly sets:

```yaml
figma_write_policy: official-exempt-only
# or
figma_write_policy: official-write-explicit
```

### `figma-use`

`figma-use` is now an exception-path safety guide, not the default Figma stage.

Use it only when all of these are true:

- the user explicitly allows `figma_write_policy: official-write-explicit` for this run
- the task actually needs Figma file/frame creation or editing
- the quota/permission risk is disclosed
- the run records file key, frame ids, exported assets, and fallback notes

## 6. PPT Workflow Placement

Figma context should not participate in fact extraction or claim judgment.

Recommended order:

1. Deep-interview confirms audience, duration, template, acceptance criteria, and Figma context/write policy.
2. Main thread builds the fact ledger from source material.
3. `ppt_storyboard` creates the slide plan after facts are stable.
4. Main thread decides assets and identifies any Figma reference nodes.
5. `ppt_template_automation` generates editable PPTX draft.
6. Optional separate Figma experiment uses GLips/Framelink context only when explicitly requested.
7. `codex-visual-acceptance` or equivalent render checks verify the deck.

Do not route the whole deck through Figma.

## 7. Configuration

Recommended user-level Codex MCP config:

```toml
[mcp_servers.figma_context]
command = "cmd"
args = ["/c", "npx", "-y", "figma-developer-mcp", "--env", "%USERPROFILE%\\.codex\\skills\\figma-context-mcp\\.env", "--stdio", "--image-dir", "generated_assets\\figma", "--format", "yaml"]
```

The repo provides a one-step setup script that prompts for `FIGMA_API_KEY` without echoing it, writes it to the user-level global skill `.env`, and updates `figma_context` to load that `.env`:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\figma-context-mcp\scripts\configure_figma_api_key.ps1
```

Optional official write provider:

```toml
[mcp_servers.figma_write]
url = "https://mcp.figma.com/mcp"
```

After adding `figma_write`, run OAuth login:

```powershell
codex mcp login figma_write
```

Keep the provider names separate. `figma_context` means open-source read/context. `figma_write` means official Figma MCP and must be triggered only by an explicit write policy.

Keep the Figma token out of the repository. Prefer a user environment variable such as `FIGMA_API_KEY`. Do not print it in logs or final answers.

Smoke checks:

```powershell
npx -y figma-developer-mcp --help
npx -y figma-developer-mcp fetch --help
codex mcp list
if ($env:FIGMA_API_KEY) { "FIGMA_API_KEY_PRESENT" } else { "FIGMA_API_KEY_MISSING" }
```

`codex mcp list` should show `figma_context`. It may also show `figma_write` when official write lanes are configured, but it should not show the official server under the ambiguous default name `figma`.

If `FIGMA_API_KEY_MISSING` is reported, do not attempt a real Figma fetch. Ask the user to set the token outside the repository, then restart Codex if MCP tools were already loaded.

## 8. Acceptance Criteria

A migrated manuscript-to-PPT run is acceptable when:

- the production brief records `figma_context_policy` and `figma_write_policy`
- default Figma provider is GLips/Framelink
- no official Figma tools are called unless explicitly authorized
- official calls, when used, are routed through `figma_write` and documented as `official-exempt-only` or `official-write-explicit`
- Figma source URLs, node ids, and downloaded assets are traceable
- PPTX render QA still blocks completion on overlap, clipping, unreadable charts, missing CJK glyphs, blank pages, or out-of-bounds content
- any disabled Figma write path or missing Figma context is disclosed

## 9. References

- GLips/Figma-Context-MCP: https://github.com/GLips/Figma-Context-MCP
- Framelink quickstart: https://www.framelink.ai/docs/quickstart
- Framelink configuration: https://www.framelink.ai/docs/configuration
- Figma MCP tools and prompts: https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/
- Figma write to canvas: https://developers.figma.com/docs/figma-mcp-server/write-to-canvas/
- Figma code to canvas: https://developers.figma.com/docs/figma-mcp-server/code-to-canvas/
- Figma MCP rate limits and access: https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/
