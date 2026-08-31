"""Bid & Proposal / Negotiate stage, what should this cost, what's the labor rate, is
my team's registration current. See PLANNING.md §2. Currently: Pricing/labor rates.
Growing to include Wage Determinations and Vendor Risk.
"""
from __future__ import annotations

import json
from typing import Optional

from ..core import mcp, _get


# ─── Contract Price Benchmarks ─────────────────────────────────────────────

@mcp.tool()
async def get_price_benchmark(
    naics: str,
    set_aside: Optional[str] = None,
    psc: Optional[str] = None,
    pricing_type: Optional[str] = None,
    agency: Optional[str] = None,
    value_basis: str = "current",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> str:
    """Get the percentile distribution of comparable contract VALUE for a NAICS, broken
    out by pricing type. A price-analysis / market-range read for the Negotiate stage,
    not a win predictor. Factual, not scored.

    Bid & Proposal / Negotiate tool, Pro only. Pair with get_price_position to see where
    YOUR specific value sits, or get_labor_rate_benchmark for the labor-cost input.

    - naics: 6-digit code, required
    - set_aside: exact code, e.g. "8A", "SBA", "SDVOSBC", "WOSB", "HZC", "NONE"
    - psc: 1-4 alphanumeric Product/Service Code, finer scope than NAICS
    - pricing_type: pin one, e.g. "FIRM FIXED PRICE", "TIME AND MATERIALS", a rarer
      pricing arrangement can surface as a raw, undecoded single-letter FPDS code
      (e.g. "J", "Y", "Z") instead of a readable name; that's passthrough source data,
      not an error
    - agency: name / acronym / CGAC code, narrows the comparable set to that agency
    - value_basis: current (default) | potential | obligated
    - date_from/date_to: filters on the FPDS transaction's `action_date` (when a
      modification/closeout action was recorded), NOT the award date or period of
      performance, a years-old contract can appear as a "current" comparable via a
      recent action on it

    IMPORTANT: pricing type shifts the median 8x-3000x within a NAICS, use the
    per-pricing-type blocks (`pricing_types`), not `combined`, for a meaningful
    comparable. `combined` is blended context only, not a real number to price against.
    """
    params = {"naics": naics, "set_aside": set_aside, "psc": psc, "pricing_type": pricing_type,
              "agency": agency, "value_basis": value_basis, "date_from": date_from, "date_to": date_to}
    data = await _get("/api/v1/pricing/benchmark", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_price_position(
    naics: str,
    value: str,
    set_aside: Optional[str] = None,
    psc: Optional[str] = None,
    pricing_type: Optional[str] = None,
    agency: Optional[str] = None,
    value_basis: str = "current",
    sample_limit: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> str:
    """Get where YOUR specific contract/bid value sits (percentile rank) against real
    comparable contracts, plus a sample of the nearest ones by value.

    Bid & Proposal / Negotiate tool, Pro only. This is the "is my number reasonable"
    check, distinct from get_price_benchmark, which gives the market range without
    placing any one number in it.

    - naics: 6-digit code, required
    - value: YOUR contract/bid value in dollars, e.g. "2200000" or "$2,200,000", required
    - set_aside / psc / pricing_type / agency / value_basis / date_from / date_to: same as
      get_price_benchmark, narrows the comparable set the same way (see its docstring for
      the `pricing_type` raw-code and `date_from`/`date_to` action_date caveats)
    - sample_limit: how many nearest comparable contracts to return, max 25

    Each sample contract's `recipient_uei` and `award_id_piid` chain into
    get_company_profile / get_contract for a closer look at a specific comparable.
    Factual positioning, not a recommendation on what to bid.
    """
    params = {"naics": naics, "value": value, "set_aside": set_aside, "psc": psc,
              "pricing_type": pricing_type, "agency": agency, "value_basis": value_basis,
              "sample_limit": sample_limit, "date_from": date_from, "date_to": date_to}
    data = await _get("/api/v1/pricing/position", params)
    return json.dumps(data, indent=2, default=str)


# ─── Labor Rate Benchmarks ──────────────────────────────────────────────────

@mcp.tool()
async def get_labor_rate_benchmark(
    labor_category: str,
    match: str = "contains",
    education_level: Optional[str] = None,
    min_experience: Optional[int] = None,
    max_experience: Optional[int] = None,
    naics: Optional[str] = None,
    vendor: Optional[str] = None,
    worksite: Optional[str] = None,
    business_size: Optional[str] = None,
    security_clearance: Optional[str] = None,
    value_basis: str = "current",
    sample_limit: int = 10,
) -> str:
    """Get the awarded labor-rate (should-cost) benchmark for a labor category, from GSA
    CALC, the labor-cost input for a proposal, paired with get_price_benchmark's
    contract-value read.

    Bid & Proposal / Negotiate tool, Pro only.

    - labor_category: required, e.g. "Senior Software Engineer"
    - match: contains (default, substring) | exact
    - education_level: HS | AA | BA | MA | PHD | OTHER
    - min_experience / max_experience: years, 0-60
    - naics: 6-digit, via the SIN bridge
    - vendor: substring match, use for a competitor's or your own rate-card lookup
    - worksite: Customer | Contractor | Virtual
    - business_size: S (small business) | O (other than small)
    - security_clearance: Yes | No
    - value_basis: current (default) | next_year | second_year, the escalated out-year
      rate directly, a distinct enum from get_price_benchmark's current/potential/obligated
    - sample_limit: how many comparable rates to return, max 25

    Use `vendor` with a specific company name (e.g. from search_companies) to check a
    known competitor's or teammate's actual awarded rate card.

    Response includes `rate_distribution` (hourly percentiles p10-p90 + min/max/avg),
    `escalation` (median year-over-year ceiling-rate growth for next_year and
    second_year, the real input for pricing an out-year, not a guessed 2-3% flat
    escalator), `category_breakdown`, and `rates_sample` (individual comparable rate rows).
    """
    params = {"labor_category": labor_category, "match": match, "education_level": education_level,
              "min_experience": min_experience, "max_experience": max_experience, "naics": naics,
              "vendor": vendor, "worksite": worksite, "business_size": business_size,
              "security_clearance": security_clearance, "value_basis": value_basis,
              "sample_limit": sample_limit}
    data = await _get("/api/v1/pricing/labor-rates", params)
    return json.dumps(data, indent=2, default=str)


# ─── Wage Determinations ────────────────────────────────────────────────────

@mcp.tool()
async def search_wage_determinations(
    type: Optional[str] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    wd_number: Optional[str] = None,
    active_only: bool = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    construction_type: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search Davis-Bacon (DBA), Service Contract Act (SCA), and CBA wage
    determinations by jurisdiction, number, or revision date.

    Bid & Proposal / Negotiate tool. For "which WDs apply where I'm bidding" use
    get_wds_by_location instead (the compliance shortcut); use this one when you need
    to browse/filter broadly or track revisions over time.

    - type: DBA | SCA | CBA
    - state: 2-letter US state code
    - county: substring
    - wd_number: substring (e.g. "AK2026", "1994-2371")
    - active_only: only currently-effective WDs
    - date_from/date_to: modified-date window, YYYY-MM-DD
    - construction_type: DBA only, Building | Heavy | Highway | Residential
    - sort_by: modified_date | publish_date | wd_number | revision_number
    - limit: max 100

    Returns each WD's identifier, pass to get_wage_determination for the full
    classification/rate detail.
    """
    params = {"type": type, "state": state, "county": county, "wd_number": wd_number,
              "active_only": active_only, "date_from": date_from, "date_to": date_to,
              "construction_type": construction_type, "sort_by": sort_by,
              "sort_order": sort_order, "limit": limit, "offset": offset}
    data = await _get("/api/v1/wage-determinations/search", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_wds_by_location(
    state: str, county: Optional[str] = None, type: Optional[str] = None,
    limit: int = 25, offset: int = 0,
) -> str:
    """The compliance shortcut: "I'm bidding a contract in this state/county, which
    wage determinations apply?" Returns every currently-active DBA, SCA, and CBA record
    covering that jurisdiction.

    Bid & Proposal / Negotiate tool. Statewide DBAs are included regardless of `county`
    (they apply everywhere in the state). No date filter, this answers "what's in
    force here right now," not a historical query (use search_wage_determinations for that).

    - state: 2-letter US state code, required
    - county: optional; omit for statewide only
    - type: DBA | SCA | CBA, filter to one type; omit for all. Rows default-sort with
      CBA first alphabetically, which can bury the DBA/SCA coverage a construction or
      services bidder actually wants (e.g. VA/Fairfax is 47 CBA vs 6 SCA vs 5 DBA), use
      this to skip straight to the type you need instead of paging past CBAs.
    - limit: max 100
    """
    params = {"state": state, "county": county, "type": type, "limit": limit, "offset": offset}
    data = await _get("/api/v1/wage-determinations/by-location", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_wage_rates(
    classification: Optional[str] = None,
    type: Optional[str] = None,
    occupation_code: Optional[str] = None,
    wd_number: Optional[str] = None,
    state: Optional[str] = None,
    active_only: bool = False,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Query prevailing-wage rates ACROSS wage determinations, by occupation, "what
    does a given trade actually pay," distinct from search_wage_determinations /
    get_wds_by_location which answer "which WDs apply."

    Bid & Proposal / Negotiate tool. Each row is one classification's hourly base wage
    plus fringe, tied to the WD it came from. For the aggregated distribution/floor
    across many WDs at once, use get_wage_rate_summary instead of paging through this.

    - classification: trade/occupation name substring, e.g. "Electrician"
    - type: DBA | SCA (CBAs have no rate table)
    - occupation_code: SCA 5-digit code, e.g. "23210"
    - wd_number: exact
    - state: 2-letter, via the WD's jurisdictions
    - sort_by: base_rate | classification | wd_number
    - limit: max 100
    """
    params = {"classification": classification, "type": type, "occupation_code": occupation_code,
              "wd_number": wd_number, "state": state, "active_only": active_only,
              "sort_by": sort_by, "sort_order": sort_order, "limit": limit, "offset": offset}
    data = await _get("/api/v1/wage-determinations/rates", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_wage_rate_summary(
    occupation_code: Optional[str] = None,
    classification: Optional[str] = None,
    type: str = "SCA",
    state: Optional[str] = None,
) -> str:
    """Get the labor-cost FLOOR for one occupation, aggregated across wage
    determinations: base hourly percentiles + Health & Welfare fringe + how many WDs
    set it, what a services bidder needs to price loaded labor, which on an SCA
    contract drives the bid far more than the award value.

    Bid & Proposal / Negotiate tool, the DISTRIBUTION view, distinct from get_wage_rates
    (individual county rate lines). Pair with get_labor_rate_benchmark for the awarded
    (as-bid) rate comparison, this tool gives the regulatory floor instead.

    - occupation_code: SCA 5-digit code, e.g. "11150" (Janitor), "27101" (Guard), the
      precise key, prefer this when known
    - classification: name substring, e.g. "Guard", used when no occupation_code is given
    - type: SCA (default) | DBA (CBAs have no rate table)
    - state: 2-letter, scope to WDs covering that state

    Response includes `distinct_classifications` (COUNT DISTINCT of matched titles), a broad `classification` substring can blend several distinct, differently-paid
    titles into one distribution (e.g. "Computer" spans 10 titles from $10-$53/hr);
    this discloses whether the returned label is one occupation or a blend. Prefer
    `occupation_code` over `classification` whenever the pay spread matters.
    """
    params = {"occupation_code": occupation_code, "classification": classification,
              "type": type, "state": state}
    data = await _get("/api/v1/wage-determinations/rate-summary", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_wage_determination(wd_id: str) -> str:
    """Get one wage determination's full record: location array, every classification's
    hourly wage + fringe, and (for CBAs) the contractor/union detail block.

    Bid & Proposal / Negotiate tool.

    - wd_id: the internal sgs id (e.g. "43309") OR the human-readable WD number (e.g.
      "AK20260001"), from search_wage_determinations, get_wds_by_location, or get_wage_rates
    """
    data = await _get(f"/api/v1/wage-determinations/{wd_id}")
    return json.dumps(data, indent=2, default=str)


# ─── Vendor Risk ─────────────────────────────────────────────────────────────

@mcp.tool()
async def get_vendor_risk_report(uei: str) -> str:
    """Get a 7-signal vendor risk report for one UEI, screening facts for teaming or
    subcontracting due diligence, before you commit to a partner.

    Bid & Proposal / Negotiate tool, Pro only. Distinct from check_exclusion (a binary
    debarment check), this is a broader risk-signal read.

    - uei: 12-character Unique Entity ID (from search_companies, search_entities,
      search_partners, or any other tool's `uei` field)

    The 7 signals (under `signals`): exclusion_status, address_cluster (other entities
    registered at the same address), name_variant_cluster, individual_exclusions_at_address,
    wave_membership, timing_gap, dual_cage. Check `triage` first, it's a pre-computed
    summary (`category`, `label`, `reasons`) so you don't have to interpret all 7 signals
    yourself; `category: "clean"` with empty `reasons` means nothing surfaced.

    Also includes `contract_exposure` (FPDS obligated total, distinct contracts, top
    agencies) and `subaward_exposure` (as-prime/as-sub FFATA payment history), how much
    is actually at stake with this vendor, alongside the risk signals themselves.
    """
    data = await _get(f"/api/v1/vendor-risk/{uei}")
    return json.dumps(data, indent=2, default=str)
