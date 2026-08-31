"""Capture & Teaming stage, who's already winning, who could I team with, who do I call.
See PLANNING.md §2. Currently: Companies + Entities. Growing to
include Partners, Company-contact, Contacts, and Recompetes (early-signal use).
"""
from __future__ import annotations

import json
from typing import Optional

from ..core import mcp, _get
from mcp.types import ToolAnnotations


# ─── Companies (won at least one award) ───────────────────────────────────

@mcp.tool(title="Search Companies", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def search_companies(
    q: Optional[str] = None,
    naics: Optional[str] = None,
    agency: Optional[str] = None,
    naics_small: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Search companies that have WON at least one federal award, by name, across both
    SAM Award Notices and FPDS prime contracts. For ALL registered SAM firms (won an
    award or not), use search_entities instead.

    Capture & Teaming tool, Pro only. Case-insensitive substring match on the name.

    - q: name substring, min 2 chars, REQUIRED, naics/agency/naics_small only narrow an
      existing name search, they don't work standalone (for a direct UEI lookup use
      get_company_profile instead)
    - naics: 6-digit code, filters to companies with 1+ award in this NAICS
    - agency: top-level agency name (e.g. "DEPT OF DEFENSE"), filters to companies with
      1+ award from this agency
    - naics_small: exact 6-digit NAICS code (e.g. "236220"), SBA DSBS small-business
      determination for this NAICS (Pro), pairs award history with actual eligibility,
      distinct from SAM's self-reported flag
    - limit: max 100

    Returns each company's `uei`, the SAME identifier every other Capture/Teaming tool
    takes as `uei` (get_company_profile, get_company_awards, get_company_peers,
    check_exclusion, get_company_contact). `total_value`/`total_awards` cover SAM Award
    Notices only; `fpds_obligated_total`/`fpds_transaction_count` cover the broader FPDS
    prime-contract activity independently, a contractor can show $0 in one and millions
    in the other, check both.
    """
    params = {"q": q, "naics": naics, "agency": agency, "naics_small": naics_small,
              "limit": limit, "offset": offset}
    data = await _get("/api/v1/companies/search", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool(title="Get Company Profile", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def get_company_profile(uei: str) -> str:
    """Get one company's aggregate profile: SAM registration (legal name, address, NAICS,
    PSC, certifications) combined with award-history totals.

    Capture & Teaming tool, Pro only. This is the SUMMARY view, for the full paginated
    list of individual awards use get_company_awards; for similar/competitor firms use
    get_company_peers.

    - uei: 12-character Unique Entity ID (from search_companies, search_opportunities'
      `award_uei_sam`, or any other tool that returns a `uei` field)

    IMPORTANT scope note: `total_awards`/`total_value`/`avg_value` here count SAM Award
    Notices ONLY (roughly 10-30% of federal obligations), NOT the company's total
    federal contract value. A contractor active only in FPDS shows `total_value: 0` here
    by design; check the FPDS-sourced fields for the fuller picture.
    """
    data = await _get(f"/api/v1/companies/{uei}")
    return json.dumps(data, indent=2, default=str)


@mcp.tool(title="Get Company Awards", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def get_company_awards(
    uei: str,
    limit: int = 50,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> str:
    """Get the full paginated award history for one company (every individual award,
    not just the summary totals get_company_profile gives you).

    Capture & Teaming tool, Pro only.

    - uei: 12-character Unique Entity ID
    - sort_by: award_date | award_amount
    - sort_order: asc | desc
    - limit: max 1000

    Each row's `notice_id` is the same identifier get_opportunity takes, for pulling the
    full original notice behind an award, but it's `null` on FPDS-sourced rows
    (`source: "fpds_prime_contract"`), since those contracts were never posted as SAM
    opportunities. Only `source: "sam_award_notice"` rows have one.
    """
    params = {"limit": limit, "offset": offset, "sort_by": sort_by, "sort_order": sort_order}
    data = await _get(f"/api/v1/companies/{uei}/awards", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool(title="Get Company Peers", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def get_company_peers(uei: str, limit: int = 10) -> str:
    """Find companies similar to this one by NAICS + agency overlap, the competitive
    landscape around a firm, not its own history.

    Capture & Teaming tool, Pro only. Use this to answer "who else competes where this
    company competes," distinct from get_company_profile (this firm's own stats) or
    search_companies (open name search).

    - uei: 12-character Unique Entity ID
    - limit: max 50

    Returns each peer's `uei`, chain into get_company_profile or check_exclusion for any
    of them.
    """
    data = await _get(f"/api/v1/companies/{uei}/peers", {"limit": limit})
    return json.dumps(data, indent=2, default=str)


# ─── Entities (the full SAM registry, award or not) ───────────────────────

@mcp.tool(title="Search Entities", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def search_entities(
    q: Optional[str] = None,
    naics: Optional[str] = None,
    state: Optional[str] = None,
    business_type: Optional[str] = None,
    active_only: bool = False,
    naics_small: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Search ALL SAM-registered entities by name (won a federal award or not). For
    companies that have actually WON an award, use search_companies instead, it has
    richer award-history fields; use this one when you need the full registry, including
    firms with no award history yet.

    Capture & Teaming tool. `q` alone works on every plan; the other filters are Pro.

    - q: name substring, min 2 chars
    - naics: NAICS code, no Y/N suffix (Pro)
    - state: 2-letter US state (Pro)
    - business_type: SAM business-type code, e.g. "8W" (WOSB), "QF" (SDVOSB), "27"
      (self-cert SDB) (Pro), an unrecognized code returns 400 with the full valid list
    - active_only: only Active registrations (Pro)
    - naics_small: exact 6-digit NAICS code (e.g. "236220"), SBA DSBS small-business
      determination for this NAICS (Pro)
    - limit: max 100

    Returns each entity's `uei`, the same identifier get_entity, get_company_profile,
    check_exclusion, and get_company_contact all take as `uei`.
    """
    params = {"q": q, "naics": naics, "state": state, "business_type": business_type,
              "active_only": active_only, "naics_small": naics_small,
              "limit": limit, "offset": offset}
    data = await _get("/api/v1/entities/search", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool(title="Get Entities Expiring", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def get_entities_expiring(
    within_days: int = 60,
    state: Optional[str] = None,
    naics: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Find SAM registrations expiring within N days, a monitoring/list question,
    distinct from a name lookup. A lapsed registration makes a firm invisible to
    contracting officers and ineligible for award, so this is useful both for
    self-monitoring and for spotting teammates/subs whose registration needs renewal.

    Capture & Teaming tool, Pro only.

    - within_days: 1-365, default 60
    - state / naics: optional narrowing filters
    - limit: max 500

    Returns each entity's `uei`, chain into get_entity for the full registration record.
    """
    params = {"within_days": within_days, "state": state, "naics": naics,
              "limit": limit, "offset": offset}
    data = await _get("/api/v1/entities/expiring", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool(title="Get Entity", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def get_entity(uei: Optional[str] = None, cage_code: Optional[str] = None) -> str:
    """Get one SAM entity's full registration record by UEI or CAGE code, the same
    question, two different keys, so this is one tool, not two.

    Capture & Teaming tool. Provide exactly one of `uei` or `cage_code`.

    - uei: 12-character Unique Entity ID (from search_entities, search_companies, or any
      other tool's `uei` field)
    - cage_code: CAGE code (from a contract/award record's `cage_code` field)

    Free tier (Developer). Returns the same shape either way.
    """
    if cage_code and not uei:
        data = await _get(f"/api/v1/entities/by-cage/{cage_code}")
    else:
        data = await _get(f"/api/v1/entities/{uei}")
    return json.dumps(data, indent=2, default=str)


# ─── Partners (teaming) ────────────────────────────────────────────────────

@mcp.tool(title="Search Partners", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def search_partners(
    naics: Optional[str] = None,
    agency: Optional[str] = None,
    state: Optional[str] = None,
    set_aside: Optional[str] = None,
    psc: Optional[str] = None,
    keywords: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Find teaming/partner firms with REAL past performance, by NAICS + agency + state +
    set-aside, who's actually done this kind of work, not just who's registered for it.

    Capture & Teaming tool, Pro only. This is the "who could I team with" question,
    distinct from search_companies (open name search) or get_company_peers (similar to
    ONE specific company).

    - naics: 6-digit code, exact
    - agency: name/acronym, crosswalk-resolved (e.g. "Army", "Navy", "USACE")
    - state: place-of-performance, 2-letter
    - set_aside: sdvosb | vosb | wosb | woman_owned | hubzone | 8a | sdb | minority_owned
    - psc: Product/Service Code, exact
    - keywords: matches the award description
    - limit: max 50

    Returns each firm's `uei`, chain into get_company_profile, check_exclusion, or
    get_company_contact. NOTE: this tool's `agencies` field is an array of sub-agency
    names with no agency CODE, it does not chain into contract-level `awarding_agency_code`
    filters directly.
    """
    params = {"naics": naics, "agency": agency, "state": state, "set_aside": set_aside,
              "psc": psc, "keywords": keywords, "limit": limit, "offset": offset}
    data = await _get("/api/v1/partners/search", params)
    return json.dumps(data, indent=2, default=str)


# ─── Company-contact resolver ──────────────────────────────────────────────

@mcp.tool(title="Get Company Contact", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def get_company_contact(uei: str) -> str:
    """Resolve a vendor's REAL decision-maker contact, SAM registration agents
    (third-party filing services) are filtered out, so this is the actual point of
    contact at the company, not their SAM paperwork filer.

    Capture & Teaming tool, Pro only. Distinct from search_contacts (finds a
    CONTRACTING OFFICER at an agency, the buyer side), this is the vendor/teammate side.

    - uei: 12-character Unique Entity ID

    Rate-limited more tightly than other tools (separate IP + key burst limits), avoid
    calling this in a tight loop across many UEIs at once.
    """
    data = await _get(f"/api/v1/company-contact/{uei}")
    return json.dumps(data, indent=2, default=str)


# ─── Contacts (buyer intel, contracting officers) ─────────────────────────

@mcp.tool(title="Search Contacts", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def search_contacts(
    name: Optional[str] = None,
    agency: Optional[str] = None,
    state: Optional[str] = None,
    email: Optional[str] = None,
) -> str:
    """Look up a CONTRACTING OFFICER's contact info, the buyer side, distinct from
    get_company_contact (the vendor/teammate side).

    Capture & Teaming tool, Pro only (`contacts_access`). A RESOLVER, not a directory, you cannot list/browse all contacts through this tool, only look up a specific one.

    Two modes, provide one:
    - name (+ optional agency, state for disambiguation): substring match, returns up to 5
    - email: exact match, returns one record, useful when you already have an email on
      file and want the current name/agency/phone for it

    Returns 404 if nothing matches, 402 if the caller's plan doesn't include contacts_access.
    """
    params = {"name": name, "agency": agency, "state": state, "email": email}
    data = await _get("/api/v1/contacts/lookup", params)
    return json.dumps(data, indent=2, default=str)


# ─── Recompetes (also an early Capture signal; see Post-Award for the monitoring use) ──

@mcp.tool(title="Search Recompetes", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def search_recompetes(
    naics: Optional[str] = None,
    agency: Optional[str] = None,
    set_aside: Optional[str] = None,
    state: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    ends_after_months: int = 0,
    ends_within_months: int = 18,
    date_anchor: str = "current_end",
    options_exhausted_only: bool = False,
    incumbent_excluded: Optional[bool] = None,
    sort_by: str = "ends_soonest",
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Find contracts entering recompete within a window, a market read for NEW business
    (who else's contract is about to be up for grabs), and also useful post-award to watch
    your OWN contract's expiration (see get_recompete for the single-contract form of that).

    Capture & Teaming / Post-Award tool, Pro only, factual, never scored (no win-probability
    guess, just the facts: option runway, offer count, incumbent history).

    - naics: exactly 6 digits
    - agency: name substring
    - ends_after_months / ends_within_months: the window, e.g. 0-18 = "ending in the next
      18 months," set ends_after_months higher (e.g. 6) to skip the too-late-to-influence band
    - date_anchor: current_end (next decision point) | potential_end (guaranteed recompete,
      all options used)
    - options_exhausted_only: true = only contracts whose options are ~exhausted (the
      high-confidence "must recompete" subset)
    - incumbent_excluded: true = only recompetes whose incumbent is CURRENTLY on the SAM
      exclusions list (can't legally win the recompete); false = only clean incumbents;
      omit for both
    - sort_by: ends_soonest | value | mod_churn | de_obligated

    Returns each row's `agency_code`/`sub_agency_code` alongside the published `agency`/
    `sub_agency` names, and `award_id_piid`, pass that to get_recompete for the full
    incumbent-vulnerability read, or to get_contract/get_vehicle for the raw FPDS record.
    `incumbent_uei` is the same identifier every Capture/Teaming tool takes as `uei`. NOTE:
    get_recompete (the single-PIID detail form) does not yet carry agency_code/sub_agency_code,
    only this search does.
    """
    params = {"naics": naics, "agency": agency, "set_aside": set_aside, "state": state,
              "amount_min": amount_min, "amount_max": amount_max,
              "ends_after_months": ends_after_months, "ends_within_months": ends_within_months,
              "date_anchor": date_anchor, "options_exhausted_only": options_exhausted_only,
              "incumbent_excluded": incumbent_excluded,
              "sort_by": sort_by, "limit": limit, "offset": offset}
    data = await _get("/api/v1/recompetes", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool(title="Get Recompete", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def get_recompete(piid: str) -> str:
    """Get one recompeting/expiring contract by PIID, plus incumbent-vulnerability
    signals (cert-lapse, lone-holder, single-agency dependence) composed from the
    incumbent's DSBS certifications and FPDS obligation history.

    Capture & Teaming / Post-Award tool, Pro only. Factual, signals-not-scores, no
    win-probability guess. Not windowed, a direct ID lookup (unlike search_recompetes).

    - piid: from search_recompetes, get_contract, or get_vehicle

    `incumbent_uei` in the response is the same identifier every Capture/Teaming tool
    takes as `uei`.
    """
    data = await _get(f"/api/v1/recompetes/{piid}")
    return json.dumps(data, indent=2, default=str)
