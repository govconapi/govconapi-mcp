"""Award & Compliance stage, who won, what are the terms, was it challenged. The
comprehensive FPDS/USAspending record (10.6M+ transactions), distinct from the sparse
SAM Award Notice slice in tools/awards.py. See PLANNING.md §2, §4.
"""
from __future__ import annotations

import json
from typing import Optional

from ..core import mcp, _get


# ─── Contracts (FPDS prime awards) ─────────────────────────────────────────

@mcp.tool()
async def search_contracts(
    uei: Optional[str] = None,
    parent_uei: Optional[str] = None,
    piid: Optional[str] = None,
    parent_piid: Optional[str] = None,
    agency: Optional[str] = None,
    naics: Optional[str] = None,
    award_type_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Search FPDS prime contract transactions, the comprehensive, authoritative award
    record (10.6M+ transactions). For the sparse SAM Award Notice slice specifically, use
    search_awards instead (see its docstring for when that's actually the right tool).

    Award & Compliance tool.

    - uei / parent_uei: exact 12-char (parent_uei = corporate roll-up)
    - piid: exact award PIID; parent_piid: the vehicle/IDV it was ordered against
    - agency: name substring
    - naics: exactly 6 digits
    - award_type_code: FPDS type A | B | C | D
    - date_from/date_to: action_date window, YYYY-MM-DD
    - amount_min/amount_max: federal_action_obligation
    - sort_by: action_date | current_total_value_of_award | federal_action_obligation |
      recipient_name (default action_date). sort_order: asc | desc.
    - limit: max 250

    Data coverage starts FY2025 (~2024-10-01) and cannot go earlier on any plan, a
    `date_from` before that floor is silently clamped, not rejected; the response's
    `window` block (`clamped`, `earliest_searchable`, `reason`) discloses what actually
    ran. Contrast search_vehicles, which is NOT floored this way.

    Returns each transaction's `award_id_piid`, pass that to get_contract for the full
    roll-up, get_contract_modifications for the full history, or get_contract_vehicle for
    what vehicle it's under. `recipient_uei` chains into every Capture/Teaming tool.
    """
    params = {"uei": uei, "parent_uei": parent_uei, "piid": piid, "parent_piid": parent_piid,
              "agency": agency, "naics": naics, "award_type_code": award_type_code,
              "date_from": date_from, "date_to": date_to, "amount_min": amount_min,
              "amount_max": amount_max, "sort_by": sort_by, "sort_order": sort_order,
              "limit": limit, "offset": offset}
    data = await _get("/api/v1/contracts/search", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_contract(piid: str) -> str:
    """Get one contract's LATEST transaction plus a roll-up of obligation/value totals
    across every modification.

    Award & Compliance tool. This is the SUMMARY view, for every individual
    modification row use get_contract_modifications; for what vehicle it's under use
    get_contract_vehicle.

    - piid: award PIID (from search_contracts, search_recompetes, or a company's award
      history)

    Top-level keys: `contract` (the latest transaction), `transaction_rollup` (counts +
    obligated/value totals across every modification, transaction_count, total_obligated,
    max/latest current and potential value, first/latest action date), and `subaward_rollup`
    (Pro only; who this prime paid as subs, subaward_count, total_subcontracted,
    distinct_sub_vendors, top_subs; a legitimate `subaward_count: 0` means no subs, not
    an error). All three are siblings, not nested inside `contract`.
    """
    data = await _get(f"/api/v1/contracts/{piid}")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_contract_modifications(piid: str, limit: int = 100, offset: int = 0) -> str:
    """Get EVERY transaction row for a contract, oldest action first, the full
    modification trail (amendments, options exercised, partial terminations), not just
    the latest snapshot get_contract gives you.

    Award & Compliance tool. There's no per-request date filter, but the underlying data
    itself only carries FY2025 onward, a contract whose real history predates that floor
    will start mid-sequence (e.g. first row `P00026`, not `P00001`), with earlier
    modifications simply never ingested, not filtered out. Check the response's `window`
    block (`clamped`, `earliest_searchable`, `reason`) before treating the returned rows
    as the complete history.

    - piid: award PIID
    - limit: max 500
    """
    params = {"limit": limit, "offset": offset}
    data = await _get(f"/api/v1/contracts/{piid}/modifications", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_contract_vehicle(piid: str) -> str:
    """Get the contract vehicle (IDIQ, GWAC, FSS schedule, or BPA) this order was placed
    against.

    Award & Compliance tool. Returns the vehicle's own PIID, chain into get_vehicle for
    the vehicle's own ceiling/period detail, or get_vehicle_holders to see who else can
    compete for orders on it.

    - piid: the ORDER's PIID (not the vehicle's own PIID), from search_contracts or get_contract

    If the contract was awarded directly, not against a vehicle, returns
    `{status: "standalone", vehicle: null, message: ...}` instead, check `status` before
    reading `vehicle.award_id_piid` or chaining into get_vehicle.
    """
    data = await _get(f"/api/v1/contracts/{piid}/vehicle")
    return json.dumps(data, indent=2, default=str)


# ─── Vehicles (IDVs) ────────────────────────────────────────────────────────

@mcp.tool()
async def search_vehicles(
    uei: Optional[str] = None,
    parent_uei: Optional[str] = None,
    piid: Optional[str] = None,
    agency: Optional[str] = None,
    naics: Optional[str] = None,
    idv_type: Optional[str] = None,
    active_only: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    ceiling_min: Optional[float] = None,
    ceiling_max: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Search contract vehicles: IDIQs, GWACs, FSS schedules, BPAs, BOAs.

    Award & Compliance tool. Vehicles are long-lived and NOT limited to a rolling
    window the way prime-contract search is, a GWAC awarded years ago is still the
    vehicle you must hold today to compete for its orders.

    - uei/parent_uei: vehicle holder, exact 12-char
    - piid: vehicle PIID, exact
    - idv_type: IDC | FSS | BPA | GWAC | BOA
    - active_only: only vehicles whose period of performance hasn't ended
    - ceiling_min/ceiling_max: potential_total_value_of_award. A ceiling of `999999999999`
      (or `.99`) is FPDS's own placeholder for "no negotiated ceiling" (typical on GSA
      MAS/GWAC-style vehicles), not a literal dollar figure.
    - limit: max 250

    Returns each vehicle's `award_id_piid`, pass to get_vehicle for detail or
    get_vehicle_holders (Pro) to see who holds it and who's actually earning through it.
    """
    params = {"uei": uei, "parent_uei": parent_uei, "piid": piid, "agency": agency,
              "naics": naics, "idv_type": idv_type, "active_only": active_only,
              "date_from": date_from, "date_to": date_to, "ceiling_min": ceiling_min,
              "ceiling_max": ceiling_max, "sort_by": sort_by, "sort_order": sort_order,
              "limit": limit, "offset": offset}
    data = await _get("/api/v1/vehicles/search", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_vehicle(piid: str) -> str:
    """Get one contract vehicle's detail: ceiling, period, and what's been ordered
    through it.

    Award & Compliance tool.

    - piid: vehicle's own PIID (from search_vehicles or get_contract_vehicle)

    Also returns a `vehicle_family` block (`is_multiple_award`, `piid_count`,
    `solicitation_identifier`, `note`) disclosing whether this PIID is one award among
    several placed under the same solicitation, distinct from get_vehicle_holders' own
    `vehicle_family.piids`, which lists every sibling PIID; this one only counts them.
    NOTE: `transaction_rollup.distinct_awardees` / `orders_rollup.distinct_holders` above
    are scoped to THIS piid only and read `1` even when `vehicle_family.is_multiple_award`
    is true (FPDS gives every awardee of a multi-award vehicle its own separate PIID), use get_vehicle_holders for the real family-wide count. A ceiling of `999999999999`
    (or `.99`) is FPDS's own placeholder for "no negotiated ceiling" (typical on GSA
    MAS/GWAC-style vehicles), treat it as effectively unlimited, not a literal ~$1T figure.
    """
    data = await _get(f"/api/v1/vehicles/{piid}")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_vehicle_holders(piid: str, limit: int = 50) -> str:
    """Get who holds a vehicle AND who's actually earning through it, two distinct
    populations, don't conflate them: a firm can hold a vehicle for years and earn
    nothing on it.

    Award & Compliance tool, Pro only. The "can I even compete for this work" answer, on a multi-award vehicle, only holders can bid task orders.

    - piid: vehicle's own PIID (from search_vehicles or get_contract_vehicle)
    - limit: max 250

    Returns `awardees` (hold the vehicle) and `earners` (have actually been paid through
    it) as separate lists with counts (`awardee_count`/`earner_count`), on a real
    multi-award vehicle these can be wildly different (e.g. 1,596 awardees, 2 earners),
    which is the whole point of the distinction. Each entry's `recipient_uei` chains into
    Capture/Teaming tools. Also returns `vehicle_family.piids`: this rolls up EVERY
    related PIID under the same vehicle family, not just the one you asked for, so
    `awardee_count` reflects the whole family, not a single order.
    """
    data = await _get(f"/api/v1/vehicles/{piid}/holders", {"limit": limit})
    return json.dumps(data, indent=2, default=str)


# ─── Subawards (FFATA) ──────────────────────────────────────────────────────

@mcp.tool()
async def search_subawards(
    prime_uei: Optional[str] = None,
    sub_uei: Optional[str] = None,
    piid: Optional[str] = None,
    agency: Optional[str] = None,
    naics: Optional[str] = None,
    sub_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Search FFATA subawards: who primes paid as subcontractors.

    Award & Compliance tool. For a single company's subs-paid or primes-that-paid-them
    reverse lookups, use get_prime_subawards / get_prime_relationships instead, narrower
    and simpler when you already have one UEI.

    - prime_uei / sub_uei: exact 12-char
    - piid: the PRIME contract's PIID
    - naics: exactly 6 digits
    - sub_name: substring, min 3 chars
    - limit: max 250

    Data coverage starts FY2025 (~2024-10-01) and cannot go earlier on any plan, a
    `date_from` before that floor is silently clamped, not rejected; the response's
    `window` block (`clamped`, `earliest_searchable`, `reason`) discloses what actually
    ran.

    NOTE: this table has no `cage_code` field, you cannot CAGE-cross-check a
    subawardee through this tool, only by UEI/name.
    """
    params = {"prime_uei": prime_uei, "sub_uei": sub_uei, "piid": piid, "agency": agency,
              "naics": naics, "sub_name": sub_name, "date_from": date_from, "date_to": date_to,
              "amount_min": amount_min, "amount_max": amount_max, "sort_by": sort_by,
              "sort_order": sort_order, "limit": limit, "offset": offset}
    data = await _get("/api/v1/subawards/search", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_subaward(subaward_sam_report_id: str) -> str:
    """Get one FFATA subaward report by its SAM report ID.

    Award & Compliance tool.

    - subaward_sam_report_id: UUID, from search_subawards or a company's subaward list
    """
    data = await _get(f"/api/v1/subawards/{subaward_sam_report_id}")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_prime_subawards(
    uei: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Get every subaward THIS company (as a prime) paid out, "who did they
    subcontract to."

    Award & Compliance tool. The opposite direction from get_prime_relationships (who
    paid THIS company as a sub), both use the same `uei`, pick based on which
    direction you're asking.

    - uei: 12-character Unique Entity ID (the PRIME's UEI)
    - limit: max 250

    Includes a `summary` block (total_subaward_amount, distinct_sub_vendors,
    distinct_prime_contracts, first/last subaward date) alongside the paginated `data`
    rows, read `summary` first rather than summing the page yourself.
    """
    params = {"date_from": date_from, "date_to": date_to, "limit": limit, "offset": offset}
    data = await _get(f"/api/v1/companies/{uei}/subawards", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_prime_relationships(
    uei: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Get every prime that has paid THIS company as a subcontractor, "who
    subcontracts to them," the opposite direction from get_prime_subawards.

    Award & Compliance tool.

    - uei: 12-character Unique Entity ID (the SUB's UEI)
    - limit: max 250

    Includes a `summary` block (total_received, distinct_primes, top_primes, first/last
    subaward date) alongside the paginated `data` rows, read `summary` first.
    """
    params = {"date_from": date_from, "date_to": date_to, "limit": limit, "offset": offset}
    data = await _get(f"/api/v1/companies/{uei}/prime-relationships", params)
    return json.dumps(data, indent=2, default=str)


# ─── Bid Protests ────────────────────────────────────────────────────────────

@mcp.tool()
async def search_protests(
    outcome: Optional[str] = None,
    agency: Optional[str] = None,
    status: Optional[str] = None,
    case_type: Optional[str] = None,
    filed_from: Optional[str] = None,
    filed_to: Optional[str] = None,
    case_number: Optional[str] = None,
    protester: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "recent",
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search GAO bid protests: who protested, on which solicitation, when, and the
    outcome.

    Award & Compliance tool. `status=Open` is the live set (still pending before GAO,
    the award may be under a performance stay); filter to `outcome=Sustained` for
    protests that actually disturbed an award.

    - protester: the firm that FILED the protest (use this, not `search`, for
      competitor research, `search` also matches the agency column)
    - search: full-text over protester, agency, solicitation number, file number
    - case_number: GAO case, e.g. "B-424433", returns every docket on that case
    - outcome: Denied | Dismissed | Sustained | Withdrawn | Granted
    - status: Open | Closed
    - sort: recent (default) | oldest | filed | due (due = soonest statutory deadline first)
    - limit: max 100

    Factual, never scored. Returns each protest's solicitation number, pass to
    get_protests_on_solicitation for every protest on that same procurement.
    """
    params = {"outcome": outcome, "agency": agency, "status": status, "case_type": case_type,
              "filed_from": filed_from, "filed_to": filed_to, "case_number": case_number,
              "protester": protester, "search": search, "sort": sort, "limit": limit, "offset": offset}
    data = await _get("/api/v1/protests", params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_protests_on_solicitation(solicitation_number: str) -> str:
    """Get every protest filed on ONE solicitation, the contestability read for a
    specific opportunity or award: any protest pending right now, and the statutory date
    GAO must decide by.

    Award & Compliance tool, Pro only.

    - solicitation_number: from search_opportunities, search_contracts, or search_protests

    Returns `any_open` and `any_sustained` (pre-computed booleans, check these first
    before scanning the `protests` list yourself) and `earliest_open_due_date` (the
    nearest statutory deadline among any still-pending protest on this solicitation).

    Resolves the WHOLE GAO case: if your `solicitation_number` matches any docket of a
    case, this returns every docket across all solicitation-number spellings GAO
    recorded for that case (GAO sometimes records one case differently across its own
    dockets, e.g. an `RFQ-` prefix present on some rows, absent on others), two
    different, both-real spellings for the same case return the identical, complete set.
    """
    data = await _get(f"/api/v1/protests/{solicitation_number}")
    return json.dumps(data, indent=2, default=str)
