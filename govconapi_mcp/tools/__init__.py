"""Import every tool module so its @mcp.tool() decorators register onto the shared
`core.mcp` instance. One file per lifecycle stage (PLANNING.md §2),
not per API module, a customer/agent thinks "what's coming up for rebid," not
"the recompete router."

Add a new stage module here as it's built. Order doesn't matter functionally (each
module registers independently), kept in roughly lifecycle order for readability.
"""
from . import opportunities   # Opportunity Discovery (3 tools)
from . import agencies        # cross-cutting agency-name resolver (1 tool)
from . import exclusions      # cross-cutting compliance screen (1 tool)
from . import awards          # Award & Compliance, SAM Award Notice slice (1 tool)
from . import market_research # Market Research (12 tools)
from . import capture_teaming # Capture & Teaming (12 tools: Companies, Entities, Partners, Company-contact, Contacts, Recompetes)
from . import bid_negotiate   # Bid & Proposal / Negotiate (9 tools: Pricing/labor rates, Wage Determinations, Vendor Risk)
from . import award_compliance # Award & Compliance (13 tools: Contracts, Vehicles, Subawards, Protests)
from . import identifiers     # cross-cutting DUNS<->UEI resolver (1 tool)

__all__ = [
    "opportunities", "agencies", "exclusions", "awards",
    "market_research", "capture_teaming",
]
