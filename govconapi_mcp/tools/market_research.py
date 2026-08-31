"""Market Research stage, where does a NAICS get bought, by whom, how competitive is
it, and what's coming before it's even postable. See PLANNING.md §2.
"""
from __future__ import annotations

import json
from typing import Optional

from ..core import mcp, _get


# ─── Contracting Offices ──────────────────────────────────────────────────

@mcp.tool()
async def discover_offices(
    naics: str,
    sort: str = "biggest",
    limit: int = 25,
) -> str:
    """Find which contracting offices buy a NAICS code, ranked, each with its own win-facts.

    Market Research tool: answers "who actually buys this, not just which department."
    Competition and set-aside behavior vary a lot office-to-office even within one agency;
    this ranks offices instead of reporting only a department-wide average.

    - naics: 2-6 digit NAICS code, required (e.g. "541512")
    - sort: biggest (total obligations) | most_open (highest full-and-open share) |
      most_setaside (highest set-aside share)
    - limit: max 100

    Returns each office's code, name, total obligations, competition rate, and set-aside
    share for this NAICS. Pass an office's `office_code` to get_office_profile for the
    full picture of how that office buys across ALL NAICS, not just this one.
    Free on every plan. No shared identifier (UEI/PIID) links out from this tool to
    contract- or company-level tools, office_code is its own namespace.
    """
    params = {"naics": naics, "sort": sort, "limit": limit}
    data = await _get("/api/v1/offices", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_office_profile(office_code: str) -> str:
    """Get one contracting office's full buying profile: obligations, competition,
    set-aside lean, and every NAICS it buys.

    Market Research tool. Use this after discover_offices (or when you already have an
    office_code from a contract/award record) to see an office's behavior across its
    ENTIRE buying pattern, not just one NAICS.

    - office_code: the office's FPDS office code (from discover_offices or a contract record)

    Free on every plan. Returns 404 if the office has no FPDS activity on record; 503
    briefly if the office index is still building (retry).
    """
    data = await _get(f"/api/v1/offices/{office_code}")
    return json.dumps(data, indent=2, default=str)


# ─── Federal Hierarchy ────────────────────────────────────────────────────

@mcp.tool()
async def list_organizations(
    type: Optional[str] = None,
    cgac: Optional[str] = None,
    parent_id: Optional[int] = None,
    hierarchy_level: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Search the federal agency organization tree (~907 departments/agencies/offices).

    Market Research tool. Use `search` to resolve a name/acronym to an org, or
    `parent_id` to list an agency's direct sub-units. Free tier.

    - type: DEPARTMENT or AGENCY
    - cgac: Treasury account code (e.g. "097" for DoD), NOT the same code space as
      `awarding_agency_code` on contract/award tools; there is no shared identifier
      between federal_hierarchy and contract-level data, cgac requires a separate
      lookup, it does not chain directly
    - parent_id: filter to direct children of one organization_id
    - hierarchy_level: 1 = root department
    - search: matches canonical name, short name, or any alternative name (min 2 chars)
    - limit: max 1000

    Returns each org's organization_id, pass that to get_organization for the full
    record with parent/children/ancestors inline, or to list_organizations again as
    parent_id to page through its children.
    """
    params = {
        "type": type, "cgac": cgac, "parent_id": parent_id,
        "hierarchy_level": hierarchy_level, "is_active": is_active,
        "search": search, "limit": limit, "offset": offset,
    }
    data = await _get("/api/v1/federal-hierarchy/", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_organization(organization_id: int) -> str:
    """Get one federal organization's full record, with its parent, immediate children,
    and full ancestor chain (root department down to immediate parent) all included in
    one call.

    Market Research tool. This already includes what get_org_relationships would give
    you separately, use this first; only call get_org_relationships if you want JUST
    the children or JUST the ancestors without the rest of the record (a narrower,
    cheaper call for e.g. listing every sub-agency of a department).

    - organization_id: from list_organizations

    Free tier. 404 if the organization_id doesn't exist.
    """
    data = await _get(f"/api/v1/federal-hierarchy/{organization_id}")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_org_relationships(organization_id: int, direction: str = "children") -> str:
    """Get JUST an organization's immediate children or its ancestor chain, without the
    rest of the record (get_organization already includes both if you need everything).

    Market Research tool, narrow form: e.g. "list every sub-agency under DoD" doesn't
    need DoD's own full record, just its children.

    - organization_id: from list_organizations or get_organization
    - direction: "children" (immediate sub-organizations) | "ancestors" (root department
      down to immediate parent; empty if this org is already a root department)

    Free tier. 404 (ancestors direction only) if organization_id doesn't exist.
    """
    path = "children" if direction == "children" else "ancestors"
    data = await _get(f"/api/v1/federal-hierarchy/{organization_id}/{path}")
    return json.dumps(data, indent=2, default=str)


# ─── Procurement Forecasts ────────────────────────────────────────────────

@mcp.tool()
async def search_forecasts(
    source: Optional[str] = None,
    agency: Optional[str] = None,
    naics: Optional[str] = None,
    set_aside: Optional[str] = None,
    state: Optional[str] = None,
    est_award_fy: Optional[int] = None,
    est_award_quarter: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    status: Optional[str] = None,
    is_recompete: Optional[bool] = None,
    keywords: Optional[str] = None,
    active_only: bool = True,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> str:
    """Search agency procurement forecasts, the only FORWARD-LOOKING layer in this API.
    These are pre-solicitation: work an agency has planned but hasn't posted an
    opportunity for yet.

    Market Research tool. Use this to find what's coming before it's postable, not what's
    live now (for live notices, use search_opportunities instead).

    - source: fco | dhs | hhs (which agency forecast feed)
    - naics: 2-6 digit code, prefix match (e.g. "5415" matches 541511, 541512...)
    - is_recompete: true = only forecasts that name a current incumbent (see below)
    - amount_min/amount_max: USD, matched against the forecast's value range
    - active_only: default true, excludes already-awarded/cancelled forecasts
    - keywords: full-text search over title + description
    - sort_by: est_award_fy | est_solicitation_date | value_high | agency | last_updated_date

    Recompete signal: when `is_recompete` is true, each row's `incumbent_piid` is the SAME
    identifier `get_contract` and `get_vehicle` take as `piid`, chain into either to see who
    currently holds it, its value, and when it expires (Pro accounts get this pre-joined
    inline as `incumbent_award`, so check that field before making the extra call).
    Direct-line PoC contact fields (poc_email, poc_phone, co_email, sb_specialist_email/phone)
    are Pro-gated; poc_name stays visible on every plan.
    """
    params = {
        "source": source, "agency": agency, "naics": naics, "set_aside": set_aside,
        "state": state, "est_award_fy": est_award_fy, "est_award_quarter": est_award_quarter,
        "amount_min": amount_min, "amount_max": amount_max, "status": status,
        "is_recompete": is_recompete, "keywords": keywords, "active_only": active_only,
        "sort_by": sort_by, "sort_order": sort_order, "limit": limit, "offset": offset,
    }
    data = await _get("/api/v1/forecasts/search", params)
    return json.dumps(data, indent=2, default=str)


# ─── NAICS / Market Pulse ─────────────────────────────────────────────────

@mcp.tool()
async def find_naics_codes(
    sector: Optional[str] = None,
    prefix: Optional[str] = None,
    min_market: Optional[float] = None,
    max_competitors: Optional[int] = None,
    set_aside_family: Optional[str] = None,
    keywords: Optional[str] = None,
    sort_by: str = "market",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Discover NAICS codes by current federal spending and small-business set-aside
    leverage, use this when you don't already know which NAICS code to look at.

    Market Research tool, the entry point into the NAICS/Market Pulse tools below.

    - sector: 2-digit NAICS sector prefix (e.g. "54")
    - prefix: any-length NAICS prefix (e.g. "5415")
    - min_market: minimum FY2025+ obligated dollars
    - max_competitors: maximum distinct winning firms (a low number = a thin, less-contested market)
    - set_aside_family: total_small_business | 8a | sdvosb | wosb | hubzone | veteran | native
    - keywords: matches the NAICS description text
    - sort_by: market (size) | competitors | setaside_pct (aggregate small-business share
      across ALL families; when set_aside_family is also set, sorts by THAT family's own
      share instead, read each row's `family_share_pct` for the honest per-family number,
      populated only when set_aside_family is set)

    Returns each matching code's `naics_code`, pass that to get_naics_market,
    get_naics_positioning, get_naics_simplified_acquisition, or get_naics_competition for
    the deeper reads below. 503 briefly if the market index is still building.
    """
    params = {
        "sector": sector, "prefix": prefix, "min_market": min_market,
        "max_competitors": max_competitors, "set_aside_family": set_aside_family,
        "keywords": keywords, "sort_by": sort_by, "sort_order": sort_order,
        "limit": limit, "offset": offset,
    }
    data = await _get("/api/v1/naics", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_naics_leaderboard(board: str, limit: int = 30) -> str:
    """Browse curated, ranked NAICS market leaderboards, a fixed set of named rankings,
    distinct from find_naics_codes' open filtered search.

    Market Research tool.

    - board: the named ranking to view , "biggest" | "least_crowded" | "most_open" |
      "most_locked" | "setaside_total_small_business" | "setaside_8a" | "setaside_sdvosb" |
      "setaside_wosb" | "setaside_hubzone" | "setaside_veteran" | "setaside_native"
    - limit: max 100

    Returns each ranked NAICS code's `naics_code`, pass that to get_naics_market or the
    other NAICS tools below. 400 if `board` isn't a recognized name; 503 briefly if the
    market index is still building.
    """
    data = await _get(f"/api/v1/naics/leaderboard/{board}", {"limit": limit})
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_naics_market(code: str) -> str:
    """Get the federal market profile for one NAICS code: spending, competition,
    set-aside leverage, top buyers, and top incumbents.

    Market Research tool, the AWARD side of a market (who's winning, how much). Pair with
    get_naics_positioning for the SOLICITATION side (the language contracting officers
    use), get_naics_simplified_acquisition for the small-buy value bands, and
    get_naics_competition for the deeper contestability read.

    - code: 2-6 digit NAICS code

    `size_standard` is null (`size_standard_status: "pending_sba_table"`), the SBA
    small-business size threshold isn't part of this dataset. Check SBA's table directly
    for small-business eligibility rather than relying on this response for it.

    Free tier. 404 if there's no FY2025+ federal contract activity for this code.
    """
    data = await _get(f"/api/v1/naics/{code}")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_naics_positioning(code: str) -> str:
    """Get the language and set-aside makeup for a NAICS code's SOLICITATION side: the
    phrase vocabulary contracting officers actually use in notices, the set-aside share
    of notices, and the top soliciting agencies, over the last 24 months of SAM
    opportunities.

    Market Research / Capture tool. This is what to put in a SAM/DSBS profile or
    capability statement so contracting officers find you. Pair with get_naics_market for
    the award side (spending, incumbents, competition) of the same NAICS.

    - code: 2-6 digit NAICS code

    Free tier. 404 if there's no SAM opportunity activity for this code in the last 24 months.
    """
    data = await _get(f"/api/v1/naics/{code}/positioning")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_naics_simplified_acquisition(code: str) -> str:
    """Get the award-value breakdown for a NAICS code over the last 12 months of FPDS
    prime awards: counts of micro / simplified-acquisition / above-SAT awards, and which
    offices are making simplified-acquisition-band awards, with distinct-firm and
    set-aside counts for that band.

    Market Research tool, the SMALL-BUY value-band read (FAR Part 13 context: the
    $15k-$350k simplified-acquisition band is reserved for small business under FAR
    19.502-2(a)'s Rule of Two). Pair with get_naics_positioning (the language) and
    get_naics_market (the whole-market picture) for the same code.

    - code: 2-6 digit NAICS code

    Free tier. Factual, never scored, the facts only, no recommendation on whether to
    pursue this band. 404 if there's no FPDS prime-award activity for this code in the
    last 12 months.
    """
    data = await _get(f"/api/v1/naics/{code}/simplified-acquisition")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_naics_competition(code: str) -> str:
    """Get how contested a NAICS market is, over the whole FPDS prime-award market: offers
    received per award, single-bidder share, top place-of-performance states, award-volume
    trend by quarter, the share of recent winners holding only one or two awards (the
    long-tail signal that a market ISN'T locked up by incumbents), and the winner-cert
    socioeconomic mix (the dollar share going to firms holding each set-aside
    certification, e.g. 8(a), SDVOSB, WOSB, HUBZone).

    Market Research / Capture tool, the CONTESTABILITY read , the facts a would-be
    competitor needs before committing a capture cycle to this market. Distinct from
    get_naics_market (size + concentration), get_naics_simplified_acquisition (the
    small-buy value bands), and get_naics_positioning (the language).

    - code: 2-6 digit NAICS code

    Free tier. Factual, never scored. 404 if there's no FPDS prime-award activity for this
    code in the last 12 months.
    """
    data = await _get(f"/api/v1/naics/{code}/competition")
    return json.dumps(data, indent=2, default=str)
