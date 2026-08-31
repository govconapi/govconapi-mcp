"""Opportunity Discovery stage, live SAM.gov contract notices."""
from __future__ import annotations

import json
from typing import Optional

from ..core import mcp, _get
from mcp.types import ToolAnnotations


@mcp.tool(title="Search Opportunities", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def search_opportunities(
    naics: Optional[str] = None,
    psc: Optional[str] = None,
    naics_multiple: Optional[str] = None,
    agency: Optional[str] = None,
    keywords: Optional[str] = None,
    state: Optional[str] = None,
    set_aside: Optional[str] = None,
    notice_type: Optional[str] = None,
    posted_after: Optional[str] = None,
    due_before: Optional[str] = None,
    due_after: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    value_min: Optional[float] = None,
    value_max: Optional[float] = None,
    has_attachments: Optional[bool] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Search federal contract opportunities (SAM.gov data) with filters.

    At least one filter is required. Use specific values:
    - naics: 6-digit NAICS code, e.g. "541330" (engineering services)
    - psc: 1-4 char Product Service Code, e.g. "D302" (IT services)
    - naics_multiple: comma-separated NAICS codes, e.g. "541511,541512"
    - agency: agency name substring (use full names, e.g. "FEDERAL EMERGENCY MANAGEMENT" not "FEMA"; use lookup_agency tool first)
    - keywords: full-text search across title, agency, description (min 3 chars)
    - state: 2-letter state code (CA, TX) or full name (California)
    - set_aside: a plain term (HUBZone, WOSB, 8(a), Veteran, Small Business, Indian Small
      Business, Buy Indian, ...) or an exact SAM code (SBA, SDVOSBC, HZC, ...). An
      unrecognized value returns 400 WITH THE FULL VALID-TERM LIST in the response body, retry using that list rather than guessing another synonym.
    - notice_type: Solicitation, Combined Synopsis/Solicitation, Presolicitation, Sources
      Sought, Award Notice, Justification, Justification and Approval (J&A), Special
      Notice, Sale of Surplus Property, Modification/Amendment/Cancel, Consolidate/
      (Substantially) Bundle. Comma-separate several to match any. Invalid values 400
      the same way as set_aside, the full list comes back in the error.
    - posted_after / due_before / due_after / date_from / date_to: YYYY-MM-DD. A
      date_from before your plan's history window is not silently dropped, it's
      clamped, and the response's `window` block (`clamped`, `date_from_requested`,
      `reason`) discloses exactly what happened.
    - value_min / value_max: USD amounts (only Award Notice records have values)
    - has_attachments: true/false
    - sort_by: posted_date, due_date, award_amount, title, agency, relevance (used
      automatically when keywords is set and sort_by is omitted)
    - sort_order: asc | desc (default desc), e.g. sort_by=due_date + sort_order=asc for
      "what's due soonest first"
    - limit: max 1000

    Returns JSON with `data` (matching opportunities), `pagination`, `filters_applied`,
    and (only when a date_from clamp applied) `window`. For full-database sync use the
    recent_changes tool instead. Each result's `award_uei_sam` (when present) is the same
    identifier get_entity/get_company_profile take as `uei`, and `notice_id` is what
    get_opportunity takes.
    """
    params = {
        "naics": naics, "psc": psc, "naics_multiple": naics_multiple,
        "agency": agency, "keywords": keywords, "state": state,
        "set_aside": set_aside, "notice_type": notice_type,
        "posted_after": posted_after, "due_before": due_before, "due_after": due_after,
        "date_from": date_from, "date_to": date_to,
        "value_min": value_min, "value_max": value_max,
        "has_attachments": has_attachments, "sort_by": sort_by, "sort_order": sort_order,
        "limit": limit, "offset": offset,
    }
    data = await _get("/api/v1/opportunities/search", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool(title="Get Opportunity", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def get_opportunity(notice_id: str) -> str:
    """Fetch a single contract opportunity by its notice_id.

    Returns the full record including agency, contacts, description, attachments,
    award data (if applicable), and 50+ structured fields.
    """
    data = await _get(f"/api/v1/opportunities/{notice_id}")
    return json.dumps(data, indent=2, default=str)


@mcp.tool(title="Recent Changes", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def recent_changes(
    since: str,
    limit: int = 100,
    offset: int = 0,
) -> str:
    """List opportunities added or updated since a timestamp.

    Use this for incremental sync instead of paginating through search results.
    Keyset-based, so depth doesn't degrade performance.

    - since: ISO 8601 timestamp, e.g. "2026-04-12T00:00:00Z"
    - limit: max 1000 per page

    Returns `data` (changed records), `pagination`, and `sync.server_time`, save server_time and pass it as `since` on your next call.
    """
    params = {"since": since, "limit": limit, "offset": offset}
    data = await _get("/api/v1/opportunities/delta", params)
    return json.dumps(data, indent=2, default=str)
