<!-- mcp-name: io.github.govconapi/govconapi -->

# GovCon API MCP

![MCP server](https://img.shields.io/badge/MCP-server-5865F2) ![53 tools](https://img.shields.io/badge/tools-53-1f6feb) ![corpus](https://img.shields.io/badge/corpus-10.8M_FPDS_transactions-1f6feb) [![from $19/mo](https://img.shields.io/badge/from-%2419%2Fmo-2ea44f)](https://govconapi.com/pricing)

**Most SAM.gov MCP servers wrap one dataset behind six to ten tools. This is 53 tools across five federal sources, already joined on the identifiers they share, including full text extracted from inside solicitation attachments.**

US federal procurement data for agents: **668,576** SAM.gov opportunities, **10,787,941** FPDS prime contract transactions, **887,310** SAM-registered entities, **225,945** FFATA subawards, **164,322** exclusions, **13,778** decided GAO protests, and **~262,000** GSA CALC labor rates. Cross-linked on UEI, CAGE, PIID and NAICS, so one question does not become five integrations.

> **Free 14-day trial, no credit card.** [Get a key](https://govconapi.com), then `pipx install govconapi-mcp`.

---

## Why this, and not the next SAM.gov wrapper

Most federal-contracting MCP servers are thin proxies over the official SAM.gov API. Four concrete differences.

- **It searches inside the documents, not just the notice.** We extracted and indexed the full text of **506,382 documents** attached to **209,095 opportunities**, 31.4 billion characters, including **57,527 files recovered from archives nested up to five levels deep** that never appear in SAM's own attachment list, and **41,764 scanned documents recovered with OCR** (measured 2026-07-16). A requirement like CMMC, a clearance level, or an option year is usually in the SOW, not the notice. Most tools structurally cannot see it.
- **Five sources, already joined.** SAM.gov opportunities and entities, FPDS contract transactions, USAspending/FFATA subawards, SAM exclusions, SBA DSBS certifications and GSA CALC rates, resolved onto shared identifiers. A wrapper hands your agent one dataset and leaves the joins to it.
- **No SAM.gov entity registration and no company UEI required.** GSA documents 10 requests/day for a non-federal user without a SAM role, and 1,000/day with one. Access here is an email and a key.
- **53 tools, organised by lifecycle stage.** Market research, opportunity discovery, capture and teaming, bid and negotiate, award and compliance. You should not have to know our URL structure to know which tool answers your question.

---

## Connect

```bash
pipx install govconapi-mcp
```

`pipx` puts the binary somewhere Claude Desktop's sandbox can spawn it. On macOS, `brew install pipx` first. With `uv`, use `uvx --from govconapi-mcp govconapi-mcp`. Python 3.10+.

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "govconapi": {
      "command": "govconapi-mcp",
      "env": { "GOVCONAPI_KEY": "gca_your_key_here" }
    }
  }
}
```

Restart Claude. For Claude Code, Cursor, VS Code, Zed and custom Python agents, see the [install reference](https://govconapi.com/mcp/tools#install).

---

## Ask it things like

> Find DoD cybersecurity solicitations posted this month over $1M.

> Which active solicitations mention CMMC anywhere in their attachments?

> Find RFPs requiring an active Secret clearance, even when the notice itself does not say so.

> Who are the entrenched incumbents in NAICS 541512, and how competitive is that market?

> Is this contract entering recompete, and is the incumbent's set-aside certification expiring first?

> Turn this UEI into a contractor profile: registration, awards, subcontracting activity, exclusions.

> Has this vendor ever been excluded from federal contracts?

---

## The 53 tools

Full reference with parameters: **[TOOLS.md](TOOLS.md)**.

| Stage | Tools | Answers |
|---|---:|---|
| Market research | 12 | where a NAICS gets bought, by whom, how contested |
| Opportunity discovery | 3 | what is live now that matches my capability |
| Capture and teaming | 12 | who is winning, who to team with, who to call |
| Bid, price and negotiate | 9 | what it should cost, labor rates, is my team clean |
| Award and compliance | 13 | who won, on what terms, was it protested |
| Agencies, awards, exclusions, identifiers | 4 | name resolution, award notices, screening, DUNS to UEI |

13 tools require Pro and return HTTP 402 on Developer. 4 more work on Developer with specific fields or filters gated. The other 36 have no plan distinction. Each is marked in TOOLS.md.

---

## What it is not

- **Not a replacement for SAM.gov as the system of record.** We normalize public federal data and preserve source provenance. For the authoritative record, or for a submission, go to SAM.gov.
- **Not real-time.** Opportunities refresh daily. If your use case turns on minute-level freshness, this is the wrong tool and we would rather you knew now.
- **Not state or local.** US federal procurement only.
- **Not a proposal writer, CRM, or BD platform.** It is a data layer. If you want an end-to-end capture suite, buy one of those instead and point it here.
- **FPDS coverage starts 2024-10-01** (FY2025 onward). Deep multi-year historical market research is a real limitation, not an oversight.
- **Source defects pass through.** SAM and FPDS contain impossible dates, $0 amounts and null UEIs. We surface them as they are and document the gotchas rather than silently cleaning them, because the corruption belongs to the system of record.

---

## Plans

| Plan | Price | Limits |
|---|---|---|
| Free trial | $0, 14 days | 25 requests/day |
| Developer | $19/mo | 1,000 requests/hour |
| Pro | $39/mo | adds the 13 Pro tools and richer fields on 4 more |

MCP access is included with every plan, including the trial. No separate tier.

---

## Troubleshooting

**`GOVCONAPI_KEY environment variable is not set`** , add it to the MCP config above and restart the client.

**`Invalid API key`** , keys start with `gca_`. Get one at [govconapi.com](https://govconapi.com).

**`At least one filter required`** , `search_opportunities` needs at least one filter (naics, keywords, state and so on). For a bulk sync, use `recent_changes` instead.

**Rate limited (429)** , free trial is 25 calls/day, Developer 1,000/hour.

**A 402 naming a specific feature** , that tool is Pro. TOOLS.md marks which.

---

## Links

- API reference: <https://govconapi.com/api-guide>
- Tool reference: <https://govconapi.com/mcp/tools>
- Machine-readable docs: <https://govconapi.com/llms.txt> and <https://govconapi.com/openapi.json>
- Support: <support@govconapi.com>

MIT licensed. Data sourced from SAM.gov, FPDS, USAspending, SBA DSBS and GSA CALC, all public federal data.
