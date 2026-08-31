"""Award & Compliance stage, the SAM Award Notice slice specifically.

NOTE (per PLANNING.md §4, resolved 2026-08-28): this wraps
/api/v1/awards/search, which queries `opportunities WHERE notice_type='Award Notice'`, a SPARSE, self-reported SAM subset (~52K of 541K opportunities). It is kept as its own
tool, not merged with the future search_contracts (FPDS/USAspending, 10.6M+ transactions,
comprehensive) behind a `source` flag, because the two sources don't share a schema or a
completeness guarantee. Use search_awards for "was this SAM solicitation's award notice
published"; use search_contracts (once built) for "who actually won and how much."
"""
from __future__ import annotations

import json
from typing import Optional

from ..core import mcp, _get


@mcp.tool()
async def search_awards(
    awardee: Optional[str] = None,
    uei: Optional[str] = None,
    naics: Optional[str] = None,
    agency: Optional[str] = None,
    value_min: Optional[float] = None,
    value_max: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Search SAM Award Notices (who won, how much, when), a SPARSE, self-reported
    subset of federal awards (~52K notices), NOT the comprehensive federal award record.
    ~60% of contractors here have only a single notice; a diversified contractor's real
    award book is usually much bigger than what shows here. For the comprehensive,
    authoritative award record (10.6M+ FPDS/USAspending transactions), use
    search_contracts instead, reach for THIS tool specifically when the question is
    about a SAM-noticed award, not the company's overall federal business.

    - awardee: company name (partial match)
    - uei: Unique Entity ID
    - naics: 6-digit NAICS code
    - agency: agency name substring
    - value_min / value_max: USD
    - date_from / date_to: YYYY-MM-DD
    - limit: max 1000
    """
    params = {
        "awardee": awardee, "uei": uei, "naics": naics, "agency": agency,
        "value_min": value_min, "value_max": value_max,
        "date_from": date_from, "date_to": date_to,
        "limit": limit, "offset": offset,
    }
    data = await _get("/api/v1/awards/search", params)
    return json.dumps(data, indent=2, default=str)
