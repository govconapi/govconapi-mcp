# GovCon API MCP: the 53 tools

Every tool is one call against `https://govconapi.com`. Organised by GovCon lifecycle stage rather than by
our internal routing, so you do not need to know our URL structure to know which tool answers your question.

**Plan markers.** **`Pro`** returns HTTP 402 on the Developer plan. *`Pro fields`* works on Developer with
specific fields or filters gated. Unmarked tools work on any plan including the 14-day free trial.

---

## Market research (12 tools)

*Where a naics gets bought, by whom, and how contested it is.*

### `discover_offices`

Find which contracting offices buy a NAICS code, ranked, each with its own win-facts.

Parameters: `naics`, `sort`, `limit`

### `get_office_profile`

Get one contracting office's full buying profile: obligations, competition, set-aside lean, and
every NAICS it buys.

Parameters: `office_code`

### `list_organizations`

Search the federal agency organization tree (~907 departments/agencies/offices).

Parameters: `type`, `cgac`, `parent_id`, `hierarchy_level`, `is_active`, `search`, `limit`, `offset`

### `get_organization`

Get one federal organization's full record, with its parent, immediate children, and full ancestor
chain (root department down to immediate parent) all included in one call.

Parameters: `organization_id`

### `get_org_relationships`

Get JUST an organization's immediate children or its ancestor chain, without the rest of the record
(get_organization already includes both if you need everything).

Parameters: `organization_id`, `direction`

### `search_forecasts` *`Pro fields`*

Search agency procurement forecasts, the only FORWARD-LOOKING layer in this API. These are pre-
solicitation: work an agency has planned but hasn't posted an opportunity for yet.

Parameters: `source`, `agency`, `naics`, `set_aside`, `state`, `est_award_fy`, `est_award_quarter`, `amount_min`, `amount_max`, `status`, `is_recompete`, `keywords`, `active_only`, `sort_by`, `sort_order`, `limit`, `offset`

### `find_naics_codes`

Discover NAICS codes by current federal spending and small-business set-aside leverage, use this
when you don't already know which NAICS code to look at.

Parameters: `sector`, `prefix`, `min_market`, `max_competitors`, `set_aside_family`, `keywords`, `sort_by`, `sort_order`, `limit`, `offset`

### `get_naics_leaderboard`

Browse curated, ranked NAICS market leaderboards, a fixed set of named rankings, distinct from
find_naics_codes' open filtered search.

Parameters: `board`, `limit`

### `get_naics_market`

Get the federal market profile for one NAICS code: spending, competition, set-aside leverage, top
buyers, and top incumbents.

Parameters: `code`

### `get_naics_positioning`

Get the language and set-aside makeup for a NAICS code's SOLICITATION side: the phrase vocabulary
contracting officers actually use in notices, the set-aside share of notices, and the top soliciting
agencies, over the last 24 months of SAM opportunities.

Parameters: `code`

### `get_naics_simplified_acquisition`

Get the award-value breakdown for a NAICS code over the last 12 months of FPDS prime awards: counts
of micro / simplified-acquisition / above-SAT awards, and which offices are making simplified-
acquisition-band awards, with distinct-firm and set-aside counts for that band.

Parameters: `code`

### `get_naics_competition`

Get how contested a NAICS market is, over the whole FPDS prime-award market: offers received per
award, single-bidder share, top place-of-performance states, award-volume trend by quarter, the
share of recent winners holding only one or two awards (the long-tail signal that a market ISN'T
locked up by incumbents), and the winner-cert socioeconomic mix (the dollar share going to firms
holding each set-aside certification, e.g. 8(a), SDVOSB, WOSB, HUBZone).

Parameters: `code`

---

## Opportunity discovery (3 tools)

*What is live right now that matches my capability.*

### `search_opportunities`

Search federal contract opportunities (SAM.gov data) with filters.

Parameters: `naics`, `psc`, `naics_multiple`, `agency`, `keywords`, `state`, `set_aside`, `notice_type`, `posted_after`, `due_before`, `due_after`, `date_from`, `date_to`, `value_min`, `value_max`, `has_attachments`, `sort_by`, `sort_order`, `limit`, `offset`

### `get_opportunity`

Fetch a single contract opportunity by its notice_id.

Parameters: `notice_id`

### `recent_changes`

List opportunities added or updated since a timestamp.

Parameters: `since`, `limit`, `offset`

---

## Agencies (1 tool)

*Resolve an agency name or acronym to the canonical sam.gov string.*

### `lookup_agency`

Resolve an agency acronym or partial name to canonical SAM.gov agency strings.

Parameters: `query`

---

## Capture and teaming (12 tools)

*Who is already winning here, who to team with, who to call.*

### `search_companies` **`Pro`**

Search companies that have WON at least one federal award, by name, across both SAM Award Notices
and FPDS prime contracts. For ALL registered SAM firms (won an award or not), use search_entities
instead.

Parameters: `q`, `naics`, `agency`, `naics_small`, `limit`, `offset`

### `get_company_profile` **`Pro`**

Get one company's aggregate profile: SAM registration (legal name, address, NAICS, PSC,
certifications) combined with award-history totals.

Parameters: `uei`

### `get_company_awards` **`Pro`**

Get the full paginated award history for one company (every individual award, not just the summary
totals get_company_profile gives you).

Parameters: `uei`, `limit`, `offset`, `sort_by`, `sort_order`

### `get_company_peers` **`Pro`**

Find companies similar to this one by NAICS + agency overlap, the competitive landscape around a
firm, not its own history.

Parameters: `uei`, `limit`

### `search_entities` *`Pro fields`*

Search ALL SAM-registered entities by name (won a federal award or not). For companies that have
actually WON an award, use search_companies instead, it has richer award-history fields; use this
one when you need the full registry, including firms with no award history yet.

Parameters: `q`, `naics`, `state`, `business_type`, `active_only`, `naics_small`, `limit`, `offset`

### `get_entities_expiring` **`Pro`**

Find SAM registrations expiring within N days, a monitoring/list question, distinct from a name
lookup. A lapsed registration makes a firm invisible to contracting officers and ineligible for
award, so this is useful both for self-monitoring and for spotting teammates/subs whose registration
needs renewal.

Parameters: `within_days`, `state`, `naics`, `limit`, `offset`

### `get_entity`

Get one SAM entity's full registration record by UEI or CAGE code, the same question, two different
keys, so this is one tool, not two.

Parameters: `uei`, `cage_code`

### `search_partners` **`Pro`**

Find teaming/partner firms with REAL past performance, by NAICS + agency + state + set-aside, who's
actually done this kind of work, not just who's registered for it.

Parameters: `naics`, `agency`, `state`, `set_aside`, `psc`, `keywords`, `limit`, `offset`

### `get_company_contact` **`Pro`**

Resolve a vendor's REAL decision-maker contact, SAM registration agents (third-party filing
services) are filtered out, so this is the actual point of contact at the company, not their SAM
paperwork filer.

Parameters: `uei`

### `search_contacts` **`Pro`**

Look up a CONTRACTING OFFICER's contact info, the buyer side, distinct from get_company_contact (the
vendor/teammate side).

Parameters: `name`, `agency`, `state`, `email`

### `search_recompetes` **`Pro`**

Find contracts entering recompete within a window, a market read for NEW business (who else's
contract is about to be up for grabs), and also useful post-award to watch your OWN contract's
expiration (see get_recompete for the single-contract form of that).

Parameters: `naics`, `agency`, `set_aside`, `state`, `amount_min`, `amount_max`, `ends_after_months`, `ends_within_months`, `date_anchor`, `options_exhausted_only`, `incumbent_excluded`, `sort_by`, `limit`, `offset`

### `get_recompete` **`Pro`**

Get one recompeting/expiring contract by PIID, plus incumbent-vulnerability signals (cert-lapse,
lone-holder, single-agency dependence) composed from the incumbent's DSBS certifications and FPDS
obligation history.

Parameters: `piid`

---

## Bid, price and negotiate (9 tools)

*What it should cost, the labor rate, whether the team is clean.*

### `get_price_benchmark`

Get the percentile distribution of comparable contract VALUE for a NAICS, broken out by pricing
type. A price-analysis / market-range read for the Negotiate stage, not a win predictor. Factual,
not scored.

Parameters: `naics`, `set_aside`, `psc`, `pricing_type`, `agency`, `value_basis`, `date_from`, `date_to`

### `get_price_position`

Get where YOUR specific contract/bid value sits (percentile rank) against real comparable contracts,
plus a sample of the nearest ones by value.

Parameters: `naics`, `value`, `set_aside`, `psc`, `pricing_type`, `agency`, `value_basis`, `sample_limit`, `date_from`, `date_to`

### `get_labor_rate_benchmark`

Get the awarded labor-rate (should-cost) benchmark for a labor category, from GSA CALC, the labor-
cost input for a proposal, paired with get_price_benchmark's contract-value read.

Parameters: `labor_category`, `match`, `education_level`, `min_experience`, `max_experience`, `naics`, `vendor`, `worksite`, `business_size`, `security_clearance`, `value_basis`, `sample_limit`

### `search_wage_determinations`

Search Davis-Bacon (DBA), Service Contract Act (SCA), and CBA wage determinations by jurisdiction,
number, or revision date.

Parameters: `type`, `state`, `county`, `wd_number`, `active_only`, `date_from`, `date_to`, `construction_type`, `sort_by`, `sort_order`, `limit`, `offset`

### `get_wds_by_location`

The compliance shortcut: "I'm bidding a contract in this state/county, which wage determinations
apply?" Returns every currently-active DBA, SCA, and CBA record covering that jurisdiction.

Parameters: `state`, `county`, `type`, `limit`, `offset`

### `get_wage_rates`

Query prevailing-wage rates ACROSS wage determinations, by occupation, "what does a given trade
actually pay," distinct from search_wage_determinations / get_wds_by_location which answer "which
WDs apply."

Parameters: `classification`, `type`, `occupation_code`, `wd_number`, `state`, `active_only`, `sort_by`, `sort_order`, `limit`, `offset`

### `get_wage_rate_summary`

Get the labor-cost FLOOR for one occupation, aggregated across wage determinations: base hourly
percentiles + Health & Welfare fringe + how many WDs set it, what a services bidder needs to price
loaded labor, which on an SCA contract drives the bid far more than the award value.

Parameters: `occupation_code`, `classification`, `type`, `state`

### `get_wage_determination`

Get one wage determination's full record: location array, every classification's hourly wage +
fringe, and (for CBAs) the contractor/union detail block.

Parameters: `wd_id`

### `get_vendor_risk_report` **`Pro`**

Get a 7-signal vendor risk report for one UEI, screening facts for teaming or subcontracting due
diligence, before you commit to a partner.

Parameters: `uei`

---

## Award and compliance (13 tools)

*Who won, on what terms, and whether it was protested.*

### `search_contracts`

Search FPDS prime contract transactions, the comprehensive, authoritative award record (10.6M+
transactions). For the sparse SAM Award Notice slice specifically, use search_awards instead (see
its docstring for when that's actually the right tool).

Parameters: `uei`, `parent_uei`, `piid`, `parent_piid`, `agency`, `naics`, `award_type_code`, `date_from`, `date_to`, `amount_min`, `amount_max`, `sort_by`, `sort_order`, `limit`, `offset`

### `get_contract` *`Pro fields`*

Get one contract's LATEST transaction plus a roll-up of obligation/value totals across every
modification.

Parameters: `piid`

### `get_contract_modifications`

Get EVERY transaction row for a contract, oldest action first, the full modification trail
(amendments, options exercised, partial terminations), not just the latest snapshot get_contract
gives you.

Parameters: `piid`, `limit`, `offset`

### `get_contract_vehicle`

Get the contract vehicle (IDIQ, GWAC, FSS schedule, or BPA) this order was placed against.

Parameters: `piid`

### `search_vehicles`

Search contract vehicles: IDIQs, GWACs, FSS schedules, BPAs, BOAs.

Parameters: `uei`, `parent_uei`, `piid`, `agency`, `naics`, `idv_type`, `active_only`, `date_from`, `date_to`, `ceiling_min`, `ceiling_max`, `sort_by`, `sort_order`, `limit`, `offset`

### `get_vehicle`

Get one contract vehicle's detail: ceiling, period, and what's been ordered through it.

Parameters: `piid`

### `get_vehicle_holders` **`Pro`**

Get who holds a vehicle AND who's actually earning through it, two distinct populations, don't
conflate them: a firm can hold a vehicle for years and earn nothing on it.

Parameters: `piid`, `limit`

### `search_subawards`

Search FFATA subawards: who primes paid as subcontractors.

Parameters: `prime_uei`, `sub_uei`, `piid`, `agency`, `naics`, `sub_name`, `date_from`, `date_to`, `amount_min`, `amount_max`, `sort_by`, `sort_order`, `limit`, `offset`

### `get_subaward`

Get one FFATA subaward report by its SAM report ID.

Parameters: `subaward_sam_report_id`

### `get_prime_subawards`

Get every subaward THIS company (as a prime) paid out, "who did they subcontract to."

Parameters: `uei`, `date_from`, `date_to`, `limit`, `offset`

### `get_prime_relationships`

Get every prime that has paid THIS company as a subcontractor, "who subcontracts to them," the
opposite direction from get_prime_subawards.

Parameters: `uei`, `date_from`, `date_to`, `limit`, `offset`

### `search_protests`

Search GAO bid protests: who protested, on which solicitation, when, and the outcome.

Parameters: `outcome`, `agency`, `status`, `case_type`, `filed_from`, `filed_to`, `case_number`, `protester`, `search`, `sort`, `limit`, `offset`

### `get_protests_on_solicitation` **`Pro`**

Get every protest filed on ONE solicitation, the contestability read for a specific opportunity or
award: any protest pending right now, and the statutory date GAO must decide by.

Parameters: `solicitation_number`

---

## Awards (SAM notices) (1 tool)

*The sparse, self-reported award-notice slice, distinct from fpds contracts.*

### `search_awards`

Search SAM Award Notices (who won, how much, when), a SPARSE, self-reported subset of federal awards
(~52K notices), NOT the comprehensive federal award record. ~60% of contractors here have only a
single notice; a diversified contractor's real award book is usually much bigger than what shows
here. For the comprehensive, authoritative award record (10.6M+ FPDS/USAspending transactions), use
search_contracts instead, reach for THIS tool specifically when the question is about a SAM-noticed
award, not the company's overall federal business.

Parameters: `awardee`, `uei`, `naics`, `agency`, `value_min`, `value_max`, `date_from`, `date_to`, `limit`, `offset`

---

## Exclusions (1 tool)

*Debarment and suspension screening.*

### `check_exclusion` *`Pro fields`*

Check the SAM.gov exclusions list (debarred / suspended entities).

Parameters: `name`, `uei`, `cage_code`, `limit`

---

## Identifiers (1 tool)

*Resolve between legacy duns and current uei.*

### `resolve_identifier`

Resolve between legacy DUNS (9 digits, or 13-digit DUNS+4) and current UEI (12 alphanumeric),
accepts either side, returns both plus the entity name.

Parameters: `identifier`

---

## Plans

| Plan | Price | Limits |
|---|---|---|
| Free trial | $0, 14 days | 25 requests/day |
| Developer | $19/mo | 1,000 requests/hour |
| Pro | $39/mo | adds the 13 `Pro` tools and richer fields on 4 more |

Keys at <https://govconapi.com>. Full REST reference at <https://govconapi.com/api-guide>.
