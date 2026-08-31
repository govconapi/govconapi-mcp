"""Cross-cutting helper, not tied to one lifecycle stage. Every stage's tools take an
`agency` filter, and SAM's raw agency strings are close to unusable without this."""
from __future__ import annotations

import json
import re

from ..core import mcp, _get


@mcp.tool()
async def lookup_agency(query: str) -> str:
    """Resolve an agency acronym or partial name to canonical SAM.gov agency strings.

    SAM.gov stores agency names like "HOMELAND SECURITY, DEPARTMENT OF.FEDERAL
    EMERGENCY MANAGEMENT AGENCY..." not "FEMA". Use this to find the right
    substring to use as the `agency` filter on search_opportunities, search_companies,
    or most other tools that take an `agency` parameter. EXCEPTION: search_forecasts'
    `agency` filter uses its own natural-language agency names (e.g. "Department of
    Health and Human Services"), not this SAM-hierarchy string, this tool's suggestion
    will not match there.

    - query: acronym (FEMA, DoD, NASA), partial name, or full agency name

    Returns matching agencies grouped by canonical name with the suggested
    filter value to use. `suggested_filter_value` is the CANONICAL grouping, which can
    be much broader than one component of it (e.g. a sub-agency's contracting office
    grouped under its parent's canonical name), if the match count looks too high, use
    one of that group's own `raw_variations` entries instead for a narrower filter.
    """
    # Acronym hints help map common shorthand to canonical phrases the data uses
    HINTS = {
        "fema": "federal emergency management",
        "dod": "defense", "usda": "agriculture", "doj": "justice",
        "dot": "transportation", "hhs": "health and human", "dhs": "homeland security",
        "epa": "environmental protection", "nasa": "aeronautics", "nih": "health",
        "va": "veterans", "irs": "internal revenue", "sec": "securities exchange",
        "fbi": "investigation", "cia": "intelligence", "dea": "drug enforcement",
        "atf": "alcohol tobacco", "nsa": "national security", "usps": "postal",
        "faa": "aviation", "fcc": "communications", "fda": "food and drug",
        "usaid": "international development", "ssa": "social security",
        "cms": "medicare medicaid", "cdc": "disease control",
        "osha": "occupational safety", "uscg": "coast guard",
        "usaf": "air force", "usmc": "marine", "doe": "energy",
        "hud": "housing urban", "doi": "interior", "dol": "labor",
    }

    raw = await _get("/api/agency-crosswalk")
    rows = raw.get("data", [])

    q = query.lower().strip()
    expansion = HINTS.get(q)

    def haystack(r: dict) -> str:
        return (
            f"{r.get('raw_agency_text','')} "
            f"{r.get('canonical_agency','')} "
            f"{r.get('department','')}"
        ).lower()

    def matches(r: dict) -> bool:
        h = haystack(r)
        if expansion:
            return expansion in h
        if len(q) <= 4:
            # Word-boundary match for short queries to avoid e.g. "EPA" in "dEPArtment"
            return bool(re.search(rf"(^|[^a-z]){re.escape(q)}($|[^a-z])", h))
        return q in h

    matched = [r for r in rows if matches(r)]

    # Group by canonical name
    groups: dict[str, dict] = {}
    for row in matched:
        key = row.get("canonical_agency") or row.get("raw_agency_text") or "(unknown)"
        g = groups.setdefault(key, {
            "canonical_agency": key,
            "department": row.get("department", ""),
            "suggested_filter_value": key,
            "total_contracts": 0,
            "variation_count": 0,
            "raw_variations": [],
        })
        g["total_contracts"] += int(row.get("frequency") or 0)
        g["variation_count"] += 1
        g["raw_variations"].append({
            "raw": row.get("raw_agency_text", ""),
            "frequency": row.get("frequency", 0),
        })

    grouped = sorted(groups.values(), key=lambda x: -x["total_contracts"])

    # Trim raw_variations to top 5 per group
    for g in grouped:
        g["raw_variations"] = sorted(g["raw_variations"], key=lambda x: -(x.get("frequency") or 0))[:5]

    return json.dumps({
        "query": query,
        "expansion_used": expansion,
        "match_count": len(matched),
        "agency_count": len(grouped),
        "agencies": grouped[:15],
    }, indent=2, default=str)
