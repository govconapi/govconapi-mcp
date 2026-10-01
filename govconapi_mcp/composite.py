"""The six task-shaped tools: resolve, search, get, market, price, contact. The default tool set.

They reach every capability of the 53 single-purpose tools in `tools/` by calling those functions, so the
API calls, responses, plan gating and errors are the same. A model picks better from six verbs than from
fifty similar names, and the six cost about a sixth of the tokens. Descriptions only ever name these six.
`build()` makes the server; GOVCONAPI_TOOLS=all serves the 53 instead (see server.py).
"""
from __future__ import annotations

import inspect
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import core
from . import tools as _tools  # noqa: F401  (registers the 53 functions on core.mcp; the six call them)

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)

# The arguments each composite tool owns; everything else a caller sends goes to the target function.
_PAGING = ("limit", "offset")

SEARCH = {
    "opportunities": "search_opportunities",
    "opportunity_changes": "recent_changes",
    "forecasts": "search_forecasts",
    "award_notices": "search_awards",
    "contracts": "search_contracts",
    "vehicles": "search_vehicles",
    "subawards": "search_subawards",
    "recompetes": "search_recompetes",
    "companies": "search_companies",
    "entities": "search_entities",
    "expiring_registrations": "get_entities_expiring",
    "partners": "search_partners",
    "protests": "search_protests",
    "exclusions": "check_exclusion",
    "wage_determinations": "search_wage_determinations",
    "wage_determinations_by_location": "get_wds_by_location",
    "offices": "discover_offices",
}

# kind -> (function, the parameter the id goes into)
GET = {
    "opportunity": ("get_opportunity", "notice_id"),
    "contract": ("get_contract", "piid"),
    "contract_modifications": ("get_contract_modifications", "piid"),
    "contract_vehicle": ("get_contract_vehicle", "piid"),
    "vehicle": ("get_vehicle", "piid"),
    "vehicle_holders": ("get_vehicle_holders", "piid"),
    "recompete": ("get_recompete", "piid"),
    "entity": ("get_entity", "uei"),  # a 5-character id is a CAGE code, see _get_args
    "company_profile": ("get_company_profile", "uei"),
    "company_awards": ("get_company_awards", "uei"),
    "company_peers": ("get_company_peers", "uei"),
    "prime_subawards": ("get_prime_subawards", "uei"),
    "prime_relationships": ("get_prime_relationships", "uei"),
    "subaward": ("get_subaward", "subaward_sam_report_id"),
    "vendor_risk": ("get_vendor_risk_report", "uei"),
    "protests_on_solicitation": ("get_protests_on_solicitation", "solicitation_number"),
    "wage_determination": ("get_wage_determination", "wd_id"),
    "office": ("get_office_profile", "office_code"),
    "organization": ("get_organization", "organization_id"),
    "organization_relationships": ("get_org_relationships", "organization_id"),
}

RESOLVE = {
    "agency": ("lookup_agency", "query"),
    "naics": ("find_naics_codes", "keywords"),
    "company": ("search_entities", "q"),
    "identifier": ("resolve_identifier", "identifier"),
    "organization": ("list_organizations", "search"),
}

MARKET = {
    "size": "get_naics_market",
    "competition": "get_naics_competition",
    "solicitation_language": "get_naics_positioning",
    "small_buys": "get_naics_simplified_acquisition",
    "leaderboard": "get_naics_leaderboard",
    "find_codes": "find_naics_codes",
}

PRICE = {
    "benchmark": "get_price_benchmark",
    "position": "get_price_position",
    "labor_rates": "get_labor_rate_benchmark",
    "wage_rates": "get_wage_rates",
    "wage_summary": "get_wage_rate_summary",
}

CONTACT = {
    "company_decision_maker": "get_company_contact",
    "contracting_officer": "search_contacts",
}


def _fn(name: str):
    tool = core.mcp._tool_manager.get_tool(name)
    if tool is None:  # pragma: no cover - guarded at import below
        raise RuntimeError(f"composite target missing: {name}")
    return tool.fn


def _params(name: str) -> dict[str, inspect.Parameter]:
    return dict(inspect.signature(_fn(name)).parameters)


async def _call(name: str, args: dict[str, Any], label: str) -> str:
    """Call a target function with only the arguments it accepts; anything else is refused, with the list."""
    accepted = _params(name)
    unknown = sorted(k for k in args if k not in accepted)
    if unknown:
        valid = ", ".join(k for k in accepted)
        raise ValueError(f"{label} does not take {', '.join(unknown)}. Valid: {valid}.")
    missing = sorted(k for k, p in accepted.items() if p.default is inspect.Parameter.empty and args.get(k) is None)
    if missing:
        raise ValueError(f"{label} needs {', '.join(missing)}.")
    return await _fn(name)(**{k: v for k, v in args.items() if v is not None})


def _choose(table: dict, key: str, what: str):
    if key not in table:
        raise ValueError(f"Unknown {what} '{key}'. Valid: {', '.join(table)}.")
    return table[key]


async def resolve(kind: Literal["agency", "naics", "company", "identifier", "organization"], query: str) -> str:
    """Turn what the user said into the IDs and codes the other tools take. Start here when the user names
    an agency, describes their work, or names a company.

    - agency: an agency name or acronym ("Navy", "FEMA") -> the exact `agency` value search filters expect
    - naics: words from NAICS titles ("computer", "engineering", "construction") -> matching codes with market
      size. It matches titles, not topics: for "cybersecurity" try "computer"
    - company: a company name -> SAM registrations with their UEI (a large firm has several; pick by name and
      location, or use search(companies), Pro, which ranks by award history)
    - identifier: a legacy 9-digit DUNS number -> the matching UEI and company (a CAGE code goes to get(entity))
    - organization: an agency or sub-agency name -> its organization_id in the federal hierarchy
    """
    name, param = _choose(RESOLVE, kind, "kind")
    return await _call(name, {param: query}, f"resolve({kind})")


async def search(
    dataset: Literal[tuple(SEARCH)],  # type: ignore[valid-type]
    filters: dict[str, Any] | None = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Search one dataset. `filters` holds that dataset's filters; an unknown filter returns the full list.
    Agency values come from resolve(agency), NAICS codes from resolve(naics), UEIs from resolve(company).
    Dates are YYYY-MM-DD. (Pro) marks datasets that need the Pro plan. Keep `limit` small (20-50) and page with
    `offset`: rows are large. Only opportunities, forecasts and partners take `keywords`.

    - opportunities: SAM.gov notices. naics, psc, agency, keywords, state, set_aside (HUBZone, WOSB, 8(a), Veteran,
      Small Business), notice_type (Solicitation, Combined Synopsis/Solicitation, Presolicitation, Sources Sought,
      Award Notice), posted_after, due_before, due_after, value_min, value_max;
      sort_by: posted_date | due_date | award_amount | title | agency | relevance
    - opportunity_changes: notices added or changed since a time. since (ISO timestamp, required); no other filters
    - forecasts: work agencies plan to buy. agency, naics, set_aside, state, est_award_fy, keywords, is_recompete,
      source (fco | dhs | hhs); sort_by: est_award_fy | est_solicitation_date | value_high | agency
    - award_notices: SAM.gov award announcements. awardee, uei, naics, agency, value_min, value_max, date_from, date_to
    - contracts: FPDS awards. naics, agency, uei, piid, award_type_code (A | B | C | D), date_from, date_to,
      amount_min, amount_max; sort_by: action_date | current_total_value_of_award | federal_action_obligation |
      recipient_name. Find a named vehicle's orders with parent_piid
    - vehicles: IDIQs, GWACs, GSA Schedules. Needs one of uei, piid, agency, naics, idv_type (IDC | FSS | BPA |
      GWAC | BOA); active_only, ceiling_min. No name search: find a vehicle's PIID via contracts or the notice
    - subawards: who subcontracts to whom. prime_uei, sub_uei, sub_name, naics, agency, piid, date_from, date_to,
      amount_min; sort_by: subaward_action_date | subaward_amount
    - recompetes (Pro): contracts ending soon. naics, agency, set_aside, state, ends_within_months, amount_min;
      sort_by: ends_soonest | value | mod_churn | de_obligated
    - companies (Pro): firms with award history. q (name, REQUIRED), naics, agency, naics_small
    - entities: every SAM registration. q (name), naics, state, business_type (SAM code: "8W" WOSB, "QF" SDVOSB),
      naics_small (a NAICS the firm is SBA-small for), active_only
    - expiring_registrations (Pro): SAM registrations about to lapse. within_days, state, naics
    - partners (Pro): teaming partners with past performance. naics, agency, state, psc, keywords,
      set_aside (sdvosb | vosb | wosb | hubzone | 8a | sdb | minority_owned)
    - protests: GAO bid protests. agency, protester, status (Open | Closed), outcome (Denied | Dismissed | Sustained |
      Withdrawn), filed_from, filed_to; sort: recent | oldest | filed | due
    - exclusions: debarred or suspended parties. name, uei, cage_code
    - wage_determinations: type (SCA | DBA | CBA), state (2 letters), county, wd_number, active_only
    - wage_determinations_by_location: every determination for a place. state (2 letters, required), county, type
    - offices: contracting offices that buy a NAICS. naics (required); sort: biggest | most_open
    """
    name = _choose(SEARCH, dataset, "dataset")
    args = dict(filters or {})
    accepted = _params(name)
    for key, value in (("limit", limit), ("offset", offset)):
        if key in accepted and key not in args:
            args[key] = value
    return await _call(name, args, f"search({dataset})")


def _get_args(kind: str, id: str, options: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    name, param = GET[kind]
    if kind == "entity" and len(id.strip()) == 5:
        param = "cage_code"
    value: Any = id
    if param == "organization_id":
        value = int(id)
    return name, {param: value, **(options or {})}


async def get(
    kind: Literal[tuple(GET)],  # type: ignore[valid-type]
    id: str,
    options: dict[str, Any] | None = None,
) -> str:
    """Fetch one record by its ID. IDs come from search results or resolve. (Pro) needs the Pro plan.

    - opportunity: notice_id from search(opportunities)
    - contract (Pro fields), contract_modifications, contract_vehicle, recompete (Pro): a PIID from search(contracts)
      or search(recompetes). contract_vehicle is the IDIQ or schedule the contract was ordered under
    - vehicle, vehicle_holders (Pro): a vehicle PIID from search(vehicles) or get(contract_vehicle)
    - entity: a UEI (12 characters) or CAGE code (5); company_profile, company_awards, company_peers, vendor_risk
      (all Pro), prime_subawards, prime_relationships: a UEI from resolve(company)
    - subaward: subaward_sam_report_id from search(subawards)
    - protests_on_solicitation (Pro): a solicitation number from an opportunity or contract
    - wage_determination: wd_id from search(wage_determinations)
    - office: office_code from search(offices)
    - organization, organization_relationships: organization_id from resolve(organization);
      options.direction = children or ancestors for relationships
    `options` takes the record's extra arguments: company_awards {limit, offset, sort_by, sort_order},
    vehicle_holders {limit}, contract_modifications {limit, offset}, organization_relationships {direction}.
    """
    _choose(GET, kind, "kind")
    name, args = _get_args(kind, id, options)
    return await _call(name, args, f"get({kind})")


async def market(
    view: Literal[tuple(MARKET)],  # type: ignore[valid-type]
    naics: str | None = None,
    board: str | None = None,
    filters: dict[str, Any] | None = None,
) -> str:
    """How big a NAICS market is, who wins it, and how it buys, across every agency. A 6-digit `naics` for the
    per-code views, which take no filters (for one agency: search(contracts) with naics and agency).

    - size: obligated dollars, award count and concentration
    - competition: offers per award, single-bidder share, set-aside mix
    - solicitation_language: the phrases contracting officers use in that market's notices
    - small_buys: how much is bought under the micro-purchase and simplified-acquisition thresholds
    - leaderboard: ranked NAICS codes; `board` = biggest, least_crowded, most_open (no naics needed)
    - find_codes: NAICS codes by market traits; filters: keywords (matches NAICS titles, not topics: use
      "computer", not "cybersecurity"), sector, prefix, min_market, max_competitors, set_aside_family
      (total_small_business | 8a | sdvosb | wosb | hubzone), sort_by (market | competitors | setaside_pct)
    """
    name = _choose(MARKET, view, "view")
    if view == "leaderboard":
        return await _call(name, {"board": board, **(filters or {})}, "market(leaderboard)")
    if view == "find_codes":
        return await _call(name, dict(filters or {}), "market(find_codes)")
    if filters:
        # The per-code views are national: silently dropping an agency or other filter returned the national
        # market as if it were filtered (GPT review, 2026-10-01). Refuse, and say where agency views live.
        raise ValueError(f"market({view}) takes only naics and covers every agency; it has no filters. For one "
                         "agency, use search(contracts) with naics and agency, or search(offices) for its buyers.")
    if not naics:
        raise ValueError(f"market({view}) needs naics, a 6-digit NAICS code (resolve(naics) finds one).")
    return await _call(name, {"code": naics}, f"market({view})")


async def price(
    kind: Literal[tuple(PRICE)],  # type: ignore[valid-type]
    filters: dict[str, Any],
) -> str:
    """Price evidence for a bid. (Pro) needs the Pro plan.

    - benchmark (Pro): the distribution of comparable contract values. naics (required), psc, agency,
      date_from, date_to, pricing_type (shorthand: FFP | T&M | CPFF | CPAF | LH), set_aside (code: 8A | SBA |
      SDVOSBC | WOSB | HZC | NONE), value_basis (current | potential | obligated)
    - position (Pro): where a value ranks against comparable contracts. naics and value (a string, e.g.
      "2200000"), required; same optional filters as benchmark
    - labor_rates: GSA CALC ceiling hourly rates. labor_category (required), match (contains | exact),
      education_level (HS | AA | BA | MA | PHD), min_experience, max_experience, naics, vendor, worksite,
      business_size, security_clearance
    - wage_rates: SCA or Davis-Bacon hourly rates for an occupation. classification (title words, e.g.
      "Electrician"), occupation_code (SCA 5-digit), type (SCA | DBA), state, wd_number;
      sort_by: base_rate | classification | wd_number. For one place, get the WD first and read its rates
    - wage_summary: the spread of those rates. classification or occupation_code, type, state
    """
    name = _choose(PRICE, kind, "kind")
    return await _call(name, dict(filters), f"price({kind})")


async def contact(
    kind: Literal[tuple(CONTACT)],  # type: ignore[valid-type]
    uei: str | None = None,
    name: str | None = None,
    email: str | None = None,
    agency: str | None = None,
    state: str | None = None,
) -> str:
    """Who to talk to. Both need the Pro plan.

    - company_decision_maker: a company's decision-maker, from its UEI (resolve(company) finds one);
      SAM registration agents are filtered out
    - contracting_officer: a contracting officer's details from their name or email; agency and state narrow it
    """
    target = _choose(CONTACT, kind, "kind")
    if kind == "company_decision_maker":
        return await _call(target, {"uei": uei}, "contact(company_decision_maker)")
    return await _call(target, {"name": name, "email": email, "agency": agency, "state": state},
                       "contact(contracting_officer)")


def _check_targets() -> None:
    """Fail at startup, not at the first call, if the package no longer has a function a table points at."""
    names = list(SEARCH.values()) + [n for n, _ in GET.values()] + [n for n, _ in RESOLVE.values()]
    names += list(MARKET.values()) + list(PRICE.values()) + list(CONTACT.values())
    have = {t.name for t in core.mcp._tool_manager.list_tools()}
    missing = sorted(set(names) - have)
    if missing:
        raise RuntimeError(f"composite tools point at functions govconapi_mcp does not have: {missing}")
    covered = set(names)
    uncovered = sorted(have - covered)
    if uncovered:
        raise RuntimeError(f"capabilities the six do not reach: {uncovered}")


_check_targets()

TITLES = {'resolve': 'Resolve names to IDs', 'search': 'Search federal contracting data', 'get': 'Get one record', 'market': 'Analyze a NAICS market', 'price': 'Price a bid', 'contact': 'Find who to contact'}


def build(**fastmcp_kwargs) -> FastMCP:
    """A FastMCP server carrying the six. The stdio server (server.py) and the hosted connector call this."""
    server = FastMCP("govconapi", **fastmcp_kwargs)
    for fn in (resolve, search, get, market, price, contact):
        server.add_tool(fn, name=fn.__name__, title=TITLES[fn.__name__], annotations=READ_ONLY)
    return server
