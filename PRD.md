# Product Requirements Document

## Personalized Job Radar

**Working title:** Job Search
**Document status:** MVP definition
**Primary user:** Ankita Sinha
**Product type:** Single-user web application
**Initial job family:** Product Management
**Primary geography:** United States
**Primary location context:** California, New York
**Last updated:** July 16, 2026

---

# 1. Executive Summary

Job Radar is a personalized job-discovery system that continuously searches a broad range of internet sources for Product Management openings, evaluates each opening against Ankita's professional background and preferences, removes duplicate and stale listings, and presents the strongest new matches in one place.

The initial product is not a general-purpose job board, applicant-tracking system, resume writer, or automated application agent. It is a focused personal radar designed to answer one question:

> What newly available Product Management roles are genuinely worth Ankita's attention?

The MVP will create a static candidate profile from Ankita's resume and a short preferences file. It will regularly gather public job postings from company career sites, applicant-tracking systems, major job boards, startup job boards, niche industry boards, recruiter sites, and search-engine results.

Each normalized posting will receive a personalized fit score and a concise explanation covering:

* Why the role appears relevant
* Which parts of Ankita's background match
* Potential concerns or missing qualifications
* Whether the role is new, recently updated, duplicated, or possibly stale
* The recommended action: review, strong match, possible match, or dismiss

The MVP succeeds when it discovers strong, relevant opportunities that Ankita would probably not have found through a single job board, while reducing the time required to search for jobs manually.

---

# 2. Problem Statement

Product Management roles are distributed across hundreds of sources. No single job board offers complete coverage, and the same opening often appears repeatedly across company websites, aggregators, recruiters, and reposting services.

Existing job alerts also produce significant noise. Their matching is usually driven by title and keyword filters rather than a meaningful understanding of a candidate's experience, seniority, interests, and constraints.

For an experienced Product Manager, this creates several problems:

1. **Fragmented discovery**
   Relevant jobs may appear on a company career page, niche board, recruiter site, or applicant-tracking system before appearing on a major platform.

2. **Duplicate listings**
   The same job may appear multiple times with slightly different titles, descriptions, locations, or URLs.

3. **Weak personalization**
   Most alerts do not distinguish between jobs that merely contain "Product Manager" and jobs that meaningfully match the candidate.

4. **Poor seniority matching**
   Product titles are inconsistent. A "Product Manager" role at one company may be equivalent to a Senior or Principal PM role elsewhere.

5. **High review burden**
   The user must repeatedly read similar descriptions to determine whether a role is relevant.

6. **Stale and low-quality listings**
   Reposted, expired, already-filled, misleading, or low-information listings waste the user's time.

7. **Missed adjacent opportunities**
   Relevant positions may use titles such as Platform Product Lead, Technical Product Manager, Product Director, Product Strategy Lead, or AI Product Lead.

Job Radar will reduce this fragmentation and noise by providing one personalized, deduplicated, ranked stream of opportunities.

---

# 3. Product Vision

Create a personal career intelligence system that monitors the market on the user's behalf and reliably surfaces the Product Management opportunities most worthy of attention.

The longer-term vision may eventually include networking signals, company intelligence, application preparation, and career planning. The MVP is intentionally limited to job discovery and evaluation.

---

# 4. Product Goals

## 4.1 Primary goals

The MVP must:

1. Search a broad and diverse collection of public internet sources.
2. Find Product Management roles that match Ankita's background.
3. Identify relevant roles even when the title is unconventional.
4. Normalize listings into a common format.
5. Detect and consolidate duplicate listings.
6. Rank listings based on personalized fit.
7. Explain why each role is or is not a strong match.
8. Show only new or meaningfully updated opportunities.
9. Preserve the original source and application link.
10. Allow Ankita to save or dismiss listings.
11. Use feedback to improve future results.
12. Reduce the amount of time spent manually searching.

## 4.2 Secondary goals

The MVP should:

* Show where and when a listing was first discovered.
* Distinguish direct company listings from third-party copies.
* Prefer the original company application page when available.
* Identify possible concerns such as lower seniority, mandatory relocation, or missing domain experience.
* Make it easy to understand why one role ranks above another.
* Maintain a searchable history of previously seen jobs.

---

# 5. Non-Goals

The MVP will not:

* Submit applications automatically.
* Fill out application forms.
* Write or tailor resumes.
* Write cover letters.
* Generate interview answers.
* Track interviews or application stages.
* Act as a general applicant-tracking system.
* Search for every possible profession.
* Support multiple users.
* Provide employer-facing recruiting functionality.
* Scrape authenticated LinkedIn pages.
* Require access to private job-board accounts.
* Send messages to recruiters or hiring managers.
* Estimate the user's probability of receiving an offer.
* Guarantee complete coverage of every available Product Management role.
* Make employment decisions on the user's behalf.

These functions may be considered after the discovery and matching system proves useful.

---

# 6. Target User

## 6.1 Initial user

The MVP is designed exclusively for Ankita Sinha.

The system does not require general-purpose onboarding, multi-user permissions, billing, team features, or configurable personas.

## 6.2 Initial professional profile

The first candidate profile should represent an experienced Product Manager with strengths and interests that include:

* Technical product management
* Data products and analytics
* AI-assisted products and developer tools
* Platform and infrastructure products
* Zero-to-one product development
* Product strategy
* Complex enterprise workflows
* Civic and public-interest technology
* Healthcare technology
* User-centered product design
* Translating between business, engineering, design, and customer needs

The profile should remain editable. The resume and preferences file, rather than assumptions embedded in code, must be the authoritative sources.

## 6.3 Initial seniority targets

The radar should primarily seek:

* Senior Product Manager
* Lead Product Manager
* Principal Product Manager
* Staff Product Manager
* Technical Product Manager
* Platform Product Manager
* AI Product Manager

Plain "Product Manager" roles may be included when the responsibilities, compensation, company structure, or required experience indicate an appropriate level.

Junior, Associate, Assistant, Internship, and early-career Product Manager roles should be excluded.

## 6.4 Initial location assumptions

The initial search should prioritize:

1. Fully remote roles available to candidates in the United States
2. San Francisco-area roles
3. Hybrid roles within a practical San Jose commuting area
4. Select New York City or San Francisco roles when the in-office expectation is limited and the opportunity is unusually strong

The user must be able to edit these assumptions in the preferences file.

## 6.5 Employment type

The default MVP search should focus on permanent, full-time employment.

Contract, fractional, consulting, advisory, and founding-product opportunities should not appear in the primary feed unless explicitly enabled.

---

# 7. Jobs to Be Done

## Primary job

> When new Product Management roles are posted across the internet, help me quickly identify the ones that best match my background so I do not need to search multiple sites every day.

## Supporting jobs

> Help me discover strong opportunities that use unexpected titles.

> Help me avoid reviewing the same role repeatedly across different sites.

> Help me understand why a job is relevant before I read the full description.

> Help me recognize meaningful gaps or concerns before I decide to apply.

> Help me distinguish genuinely new jobs from stale repostings.

> Help me tune the radar by telling it why I saved or dismissed previous results.

---

# 8. Product Principles

## 8.1 Source breadth over source dependence

The radar should not rely on a single job board or provider. Its value comes partly from finding roles across many different source types.

## 8.2 Direct sources are preferred

When the same role appears on multiple sites, the direct company career page or official applicant-tracking page should be treated as canonical.

## 8.3 Relevance over volume

The product should not maximize the number of listings shown. It should maximize the number of listings that merit the user's attention.

## 8.4 Explain the ranking

A score without an explanation is insufficient. Every recommended role must show why it matched and what may be missing.

## 8.5 The user remains in control

The system may discover, classify, summarize, and recommend. It will not apply, contact anyone, or represent the user without explicit future authorization.

## 8.6 Feedback should be lightweight

The user should be able to improve future results without completing long forms or repeatedly editing filters.

## 8.7 Newness matters

A radar should focus on change. Previously seen roles should not reappear unless the listing has changed meaningfully.

---

# 9. MVP Scope

The MVP consists of six core capabilities:

1. Candidate profile creation
2. Multi-source job discovery
3. Job normalization and deduplication
4. Personalized matching and ranking
5. Radar dashboard
6. Save, dismiss, and feedback controls

A daily email digest is included only if it can be implemented without materially delaying the core dashboard.

---

# 10. Candidate Profile

## 10.1 Profile inputs

The system will create the initial candidate profile from:

* A current resume
* A short structured preferences file
* Optional manually entered notes describing desired work

LinkedIn integration is not required for the MVP. A LinkedIn PDF export may be accepted as a document input.

## 10.2 Resume extraction

The system should extract and store:

* Past job titles
* Employers
* Employment dates
* Years of relevant experience
* Product domains
* Industries
* Product types
* Technical skills
* Management experience
* Leadership scope
* Major accomplishments
* Common keywords
* Tools and platforms
* Education
* Certifications, if applicable

The extracted profile must be reviewable and editable.

## 10.3 Preferences file

The preferences file should support:

* Desired job titles
* Acceptable adjacent titles
* Minimum and maximum seniority
* Preferred industries
* Acceptable industries
* Excluded industries
* Preferred company stages
* Preferred company sizes
* Geographic preferences
* Remote and hybrid preferences
* Maximum expected office frequency
* Visa sponsorship requirement (sponsorship must be available)
* Minimum base salary
* Minimum total compensation, if known
* Employment types
* Required benefits or conditions
* Hard exclusions
* Positive keywords
* Negative keywords
* Companies of interest
* Companies to exclude

## 10.4 Profile format

For the MVP, the profile may be stored as editable JSON, YAML, or database records. A full graphical profile editor is not required.

Example conceptual structure:

```yaml
target_roles:
  - Senior Product Manager
  - Principal Product Manager
  - Director of Product
  - Technical Product Manager
  - AI Product Manager
  - Data Product Manager
  - Platform Product Manager

preferred_domains:
  - artificial intelligence
  - developer tools
  - data and analytics
  - enterprise software
  - healthcare technology

location:
  home: California, CA
  remote_us: preferred
  local_hybrid: accepted
  nyc_dc_hybrid: exceptional_matches_only

excluded_seniority:
  - associate
  - junior
  - internship

employment_types:
  - full-time
```

---

# 11. Source Strategy

## 11.1 Source categories

The radar should search as many compliant, technically reliable public sources as practical.

### Tier 1: Direct employer sources

* Company career pages
* Official applicant-tracking-system pages
* Public company job APIs or feeds
* Structured job data embedded in company pages
* Company-specific RSS or JSON feeds where available

Common applicant-tracking ecosystems may include:

* Greenhouse
* Lever
* Ashby
* Workday
* SmartRecruiters
* Jobvite
* iCIMS
* BambooHR
* Oracle recruiting systems
* SuccessFactors

### Tier 2: Major aggregators

* General job-search engines
* Large public job boards
* Search-engine job results
* Public pages indexed from recruiter and staffing sites

### Tier 3: Startup and technology sources

* Startup job boards
* Venture-capital portfolio job boards
* Accelerator company job pages
* Technology-community job boards
* Remote-work job boards

### Tier 4: Industry-specific sources

* Product Management job boards
* AI and machine-learning job boards
* Developer-tool communities
* Healthcare-technology job boards
* Public-interest and civic-technology boards
* Government digital-service opportunities
* Nonprofit technology boards
* Data and analytics communities

### Tier 5: Discovery queries

The system should run targeted search-engine queries designed to uncover jobs that are not reliably indexed by standard feeds.

Examples:

* `"principal product manager" "remote" "apply"`
* `"director of product" "California"`
* `site:boards.greenhouse.io "product manager" "AI"`
* `site:jobs.lever.co "platform product manager"`
* `"technical product manager" "United States" "careers"`

## 11.2 Source registry

Every source should be represented in a registry containing:

* Source name
* Source type
* Base URL
* Retrieval method
* Search frequency
* Last successful retrieval
* Last error
* Number of jobs retrieved
* Number of unique jobs produced
* Duplicate rate
* Match yield
* Reliability status
* Terms or access restrictions
* Whether the source provides direct or third-party listings

## 11.3 Source prioritization

Sources should be prioritized according to:

1. Historical number of strong matches
2. Listing freshness
3. Directness
4. Data quality
5. Reliability
6. Duplicate rate
7. Technical retrieval cost

A source with low volume but frequent high-quality matches should remain valuable.

## 11.4 Compliance

The MVP should:

* Use public pages, feeds, APIs, and permitted search results.
* Respect robots directives and reasonable request limits.
* Avoid bypassing authentication, access controls, or anti-bot systems.
* Avoid storing unnecessary copied content.
* Link users back to the original posting.
* Retain only the information necessary for matching and history.
* Permit individual sources to be disabled quickly.

The source strategy should favor sustainable retrieval methods over brittle scraping.

---

# 12. Job Discovery

## 12.1 Search generation

The system should generate a portfolio of searches rather than a single keyword query.

Searches should combine:

* Seniority variants
* Product title variants
* Domain terms
* Location terms
* Remote-work terms
* Applicant-tracking domains
* Target company names
* Industry terms

## 12.2 Title expansion

The title-matching system should recognize relevant variations, including:

* Product Lead
* Product Strategy Lead
* HealthCare Product Lead
* Healthcare Data Product Lead
* AI Product Lead
* Forward Deployed Product Manager
* Platform Product Manager

Title expansion should not automatically make every listing relevant. Responsibilities and qualifications must also match.

## 12.3 Search cadence

The MVP should run a complete search at least once daily.

High-yield direct sources may be checked more frequently, subject to technical and access constraints.

Each run should store:

* Search start time
* Search completion time
* Sources attempted
* Sources completed
* Errors
* Listings found
* New unique jobs
* Updated jobs
* Strong matches
* Possible matches

## 12.4 Historical awareness

The system must maintain a history of discovered listings so it can distinguish:

* New role
* Previously seen role
* Updated role
* Reposted role
* Removed role
* Expired role
* Duplicate role from another source

---

# 13. Job Normalization

Every retrieved listing should be converted into a standard job record.

## 13.1 Required normalized fields

* Internal job ID
* Title
* Normalized title
* Company
* Normalized company name
* Location
* Remote status
* Employment type
* Department
* Seniority
* Salary minimum
* Salary maximum
* Salary currency
* Description
* Responsibilities
* Required qualifications
* Preferred qualifications
* Industry
* Product domain
* Date posted
* Date first discovered
* Date last verified
* Source name
* Source type
* Source URL
* Canonical application URL
* Applicant-tracking system
* Listing status
* Match score
* Match tier
* Match explanation
* Concerns
* User disposition

## 13.2 Missing information

The system must not invent missing information.

Unknown salary, remote status, posting date, or employment type should be labeled as unknown.

Inferred fields should be visibly distinguishable from fields stated in the posting.

---

# 14. Deduplication

## 14.1 Duplicate detection

The system should identify duplicates using a combination of:

* Canonical URL
* Applicant-tracking job ID
* Company
* Normalized title
* Location
* Description similarity
* Responsibilities similarity
* Posting date
* Salary range
* Source relationships

## 14.2 Canonical record selection

When duplicates are found, the canonical record should be selected in this order:

1. Official company career page
2. Official applicant-tracking page
3. Authorized recruiter or staffing page
4. Major aggregator
5. Other third-party source

## 14.3 Duplicate presentation

The dashboard should display one primary card per unique job.

The card may indicate:

* Number of sources where the role was found
* Original source
* Other known sources
* Whether the listing appears to have been reposted

## 14.4 Reposting logic

A reposted job should not automatically be treated as new.

It may return to the new-results feed only when:

* The description changed substantially
* The location changed
* The compensation changed
* The required qualifications changed
* The original listing had been absent for a defined period
* The company issued a new official job identifier

---

# 15. Matching and Ranking

## 15.1 Matching approach

The MVP should use a hybrid model combining:

* Hard filters
* Structured rules
* Keyword and taxonomy matching
* Semantic similarity
* LLM-generated analysis
* User-feedback adjustments

The LLM should assist with interpretation and explanation. It should not be the sole source of the score.

## 15.2 Hard filters

A listing should be excluded or placed in a separate rejected state when it clearly violates a non-negotiable condition.

Initial hard filters should include:

* Junior, Associate, Assistant, or Internship seniority
* Non-Product roles with no meaningful product ownership
* Roles unavailable to candidates based in the United States
* Postings that explicitly exclude visa sponsorship (for example "unable to sponsor," "must be authorized to work without sponsorship," "U.S. citizens only," security-clearance or ITAR/U.S.-persons requirements). Postings that are silent on sponsorship are not excluded; the match analysis should flag sponsorship as unconfirmed instead.
* Mandatory relocation outside approved locations
* Primarily commission-based compensation
* Part-time or temporary employment when full-time is required
* Explicit required credentials that the candidate does not possess, when truly mandatory
* Clearly below-minimum compensation when a salary floor is configured

Hard-filtered jobs should be retained in logs for debugging but should not appear in the main feed.

## 15.3 Personalized score

Every eligible role should receive a score from 0 to 100.

### Initial weighting

| Dimension                           |  Weight |
| ----------------------------------- | ------: |
| Functional and responsibility match |      25 |
| Seniority and scope match           |      15 |
| Product-domain match                |      15 |
| Skills and experience match         |      15 |
| Location and work-arrangement match |      10 |
| Industry and mission match          |       8 |
| Compensation match                  |       5 |
| Company and product-stage match     |       4 |
| Posting freshness                   |       3 |
| **Total**                           | **100** |

Weights must be configurable without code changes.

## 15.4 Score dimensions

### Functional and responsibility match

Measures whether the actual work resembles Ankita's experience, including:

* Product strategy
* Roadmap ownership
* Customer discovery
* Technical collaboration
* Data-informed decision-making
* Cross-functional leadership
* Zero-to-one development
* Platform or enterprise product work
* Organizational influence

### Seniority and scope match

Measures:

* Years of experience requested
* Individual-contributor versus management scope
* Strategic responsibility
* Ownership breadth
* Organizational level
* Team leadership
* Executive interaction
* Budget or portfolio responsibility

### Product-domain match

Measures alignment with:

* AI products
* Developer tools
* Data and analytics
* Enterprise platforms
* Healthcare technology
* Public-interest technology
* Complex workflow products

### Skills and experience match

Compares required and preferred qualifications with the candidate profile.

It should distinguish:

* Strong demonstrated experience
* Transferable experience
* Partial experience
* Missing preferred qualification
* Missing required qualification

### Location and work arrangement

Highest scores should go to:

* Remote U.S. roles
* Suitable California roles

Lower scores may apply to:

* Frequent travel
* Ambiguous remote status
* Hybrid roles in more distant markets
* Roles requiring regular presence in New York or California.

### Industry and mission match

Measures whether the company's business and mission fit expressed preferences.

### Compensation match

Uses published compensation when available.

A missing salary should reduce confidence, not automatically disqualify the job.

### Freshness

Newer postings should receive a small ranking advantage. Freshness should not overpower professional fit.

## 15.5 Match tiers

* **Excellent match:** 85–100
* **Strong match:** 75–84
* **Possible match:** 60–74
* **Weak match:** 40–59
* **Do not show:** Below 40 or hard-filtered

The default dashboard should emphasize excellent and strong matches.

Possible matches should be available in a secondary section.

## 15.6 Match explanation

Every visible job must include a concise personalized analysis.

Required format:

**Why it matches**

* Two to four specific connections between the role and the candidate profile

**Potential concerns**

* Zero to three meaningful gaps, uncertainties, or constraints

**Recommendation**

* Strongly review
* Review
* Consider
* Low priority

The explanation should reference evidence from the posting and candidate profile. It should avoid generic statements such as "your skills are a good fit."

## 15.7 Confidence

The system should report a confidence level separate from the match score.

Confidence reflects data completeness, not job quality.

Examples:

* **High confidence:** Complete description, clear location, clear seniority, compensation provided
* **Medium confidence:** Good description but some fields missing
* **Low confidence:** Sparse listing, ambiguous location, or unclear responsibilities

---

# 16. User Feedback

## 16.1 Available actions

Each listing should support:

* Save
* Dismiss
* Mark as applied
* Open original listing
* Restore dismissed listing

"Mark as applied" is included only as a disposition, not as a full application-tracking workflow.

## 16.2 Dismissal reasons

When dismissing a role, the user may optionally select:

* Too junior
* Too senior
* Wrong product domain
* Wrong industry
* Wrong location
* Not truly remote
* Compensation too low
* Company not interesting
* Responsibilities not appealing
* Missing required qualification
* Duplicate
* Stale or expired
* Other

The interaction should require no more than one extra click.

## 16.3 Learning from feedback

The system should use repeated feedback to adjust ranking.

Examples:

* Repeated dismissal of advertising-technology roles lowers that domain's weight.
* Repeated saving of developer-tool roles raises that domain's weight.
* Repeated dismissal of roles requiring three office days per week creates a stronger hybrid-work penalty.
* Repeated dismissal of ordinary Product Manager titles as too junior strengthens the seniority filter.

The MVP may implement these adjustments as transparent rule changes rather than a trained machine-learning model.

## 16.4 Manual controls

The user must be able to inspect and reset learned preferences.

The radar should never silently make an entire category permanently invisible based on a single dismissal.

---

# 17. Radar Dashboard

## 17.1 Primary screen

The default screen should be a ranked feed of newly discovered jobs.

The page header should show:

* Date and time of last completed scan
* Number of sources checked
* Number of raw listings found
* Number of unique new jobs
* Number of strong matches
* Any source failures

## 17.2 Feed sections

The initial dashboard should contain:

1. **Excellent matches**
2. **Strong matches**
3. **Possible matches**
4. **Saved**
5. **Previously seen**
6. **Dismissed**

Only the first three sections need to appear in the primary navigation for the first implementation.

## 17.3 Job card

Each job card should show:

* Job title
* Company
* Location
* Remote or hybrid status
* Compensation, when available
* Match score
* Match tier
* Confidence
* Date first seen
* Source
* Why it matches
* Potential concerns
* Save button
* Dismiss button
* Applied button
* Link to the canonical posting

## 17.4 Job detail view

Selecting a job should open a detail page or expandable panel containing:

* Full normalized job information
* Longer personalized analysis
* Responsibilities
* Required qualifications
* Preferred qualifications
* Score breakdown
* Missing or uncertain information
* Source history
* Duplicate sources
* Date first seen
* Date last verified
* Original posting link

## 17.5 Filters

The MVP should support simple filters for:

* Match tier
* Date discovered
* Job title
* Company
* Location
* Remote status
* Salary known or unknown
* Domain
* Industry
* Saved, dismissed, or applied status

## 17.6 Sorting

Supported sorting:

* Best match
* Newest discovered
* Newest posted
* Highest compensation
* Company name

Best match should be the default.

---

# 18. Daily Digest

A daily digest is desirable but subordinate to the web dashboard.

When enabled, the digest should include:

* Number of sources checked
* Number of new unique jobs found
* Up to ten highest-ranked new matches
* Title, company, location, score, and short match explanation
* Direct link to the dashboard or canonical application page

The digest should not include previously seen jobs unless they changed meaningfully.

If no strong matches were found, it should say so rather than filling the digest with weak results.

---

# 19. Freshness and Listing Status

## 19.1 Status values

Each job should have one of the following statuses:

* Active
* Possibly active
* Removed
* Expired
* Reposted
* Unable to verify

## 19.2 Verification

The system should periodically revisit canonical links.

A listing may be marked removed when:

* The official page returns a clear not-found response
* The employer states that the role is closed
* The job no longer appears in an official feed
* The application page is unavailable across repeated checks

A temporary network or source failure should not immediately mark a listing expired.

## 19.3 Stale listing indicators

Potential stale-listing signals include:

* Listing age beyond a configurable threshold
* Repeated reposting without meaningful changes
* Third-party listing remains after official listing disappears
* Application link redirects to a generic careers page
* Job identifier no longer exists
* Contradictory posting dates across sources

The system should label uncertainty rather than claiming a job is a "ghost job" without sufficient evidence.

---

# 20. Administrative and Operational Tools

Because the MVP has only one user, administration may be handled through a simple internal page or configuration files.

Required operational functions:

* Trigger a scan manually
* View scan history
* View failed sources
* Retry a failed source
* Enable or disable a source
* Edit source frequency
* Inspect raw and normalized job data
* Merge or separate duplicate jobs
* Recalculate match scores
* Edit profile and preference weights
* Reprocess a listing
* Delete stored job data

---

# 21. Data Model

## 21.1 CandidateProfile

* `id`
* `name`
* `resume_text`
* `resume_version`
* `experience_summary`
* `skills`
* `industries`
* `domains`
* `titles`
* `education`
* `leadership_scope`
* `location_preferences`
* `compensation_preferences`
* `positive_preferences`
* `negative_preferences`
* `hard_filters`
* `created_at`
* `updated_at`

## 21.2 Source

* `id`
* `name`
* `source_type`
* `base_url`
* `retrieval_method`
* `enabled`
* `scan_frequency`
* `last_scan_at`
* `last_success_at`
* `status`
* `error_count`
* `configuration`

## 21.3 RawListing

* `id`
* `source_id`
* `external_job_id`
* `source_url`
* `raw_title`
* `raw_company`
* `raw_location`
* `raw_description`
* `raw_payload`
* `retrieved_at`
* `content_hash`

## 21.4 Job

* `id`
* `canonical_title`
* `normalized_title`
* `company`
* `normalized_company`
* `location`
* `remote_status`
* `employment_type`
* `seniority`
* `description`
* `responsibilities`
* `required_qualifications`
* `preferred_qualifications`
* `salary_min`
* `salary_max`
* `currency`
* `industry`
* `domain`
* `date_posted`
* `first_seen_at`
* `last_seen_at`
* `last_verified_at`
* `canonical_url`
* `status`

## 21.5 JobSourceLink

* `job_id`
* `raw_listing_id`
* `is_canonical`
* `first_seen_at`
* `last_seen_at`

## 21.6 MatchEvaluation

* `job_id`
* `candidate_profile_id`
* `overall_score`
* `match_tier`
* `confidence`
* `dimension_scores`
* `match_reasons`
* `concerns`
* `recommendation`
* `model_version`
* `rules_version`
* `evaluated_at`

## 21.7 UserDisposition

* `job_id`
* `status`
* `dismissal_reason`
* `notes`
* `created_at`
* `updated_at`

---

# 22. Functional Requirements

## FR-1: Profile ingestion

The system must accept a resume and preferences file and generate an editable candidate profile.

**Acceptance criteria**

* Resume text is successfully extracted.
* Major experience, skill, domain, and title data are represented.
* The user can correct extracted information.
* Profile changes can trigger rescoring of existing jobs.

## FR-2: Multi-source ingestion

The system must retrieve jobs from multiple source categories.

**Acceptance criteria**

* At least one direct employer or ATS source is supported.
* At least one aggregator source is supported.
* At least one startup or niche source is supported.
* Search-engine discovery queries are supported.
* Source failures do not prevent the rest of the scan from completing.

## FR-3: Job normalization

The system must convert source-specific data into the standard job schema.

**Acceptance criteria**

* Core fields are consistently stored.
* Missing values remain unknown.
* Inferred values are distinguishable from stated values.
* Original source content remains traceable.

## FR-4: Deduplication

The system must merge substantially identical listings.

**Acceptance criteria**

* Identical official and aggregator listings appear as one job.
* The official source is preferred as canonical.
* Other sources remain visible in the source history.
* False duplicate merges can be manually reversed.

## FR-5: Eligibility filtering

The system must remove jobs that violate hard requirements.

**Acceptance criteria**

* Junior and internship roles do not appear in the main feed.
* Location and employment-type exclusions are applied.
* Excluded jobs remain inspectable in operational logs.
* Filter reasons are recorded.

## FR-6: Match scoring

The system must assign each eligible role a personalized score and tier.

**Acceptance criteria**

* Scores range from 0 to 100.
* Dimension scores add to the overall result.
* Weight changes do not require application-code changes.
* The same job and profile produce reproducible structured scores within the same rules version.

## FR-7: Explanation generation

The system must provide specific match reasons and concerns.

**Acceptance criteria**

* Explanations cite actual profile and job attributes.
* Generic unsupported claims are avoided.
* Missing information is acknowledged.
* Match explanation and score do not materially contradict each other.

## FR-8: Ranked dashboard

The system must present new jobs in descending order of fit.

**Acceptance criteria**

* Excellent, strong, and possible matches are distinguishable.
* The feed defaults to unseen jobs.
* Each card links to the canonical posting.
* The user can inspect score details.

## FR-9: User feedback

The system must allow jobs to be saved, dismissed, or marked applied.

**Acceptance criteria**

* Actions persist across sessions.
* Dismissed jobs leave the default feed.
* Dismissal reasons can be captured in one additional interaction.
* The user can reverse an action.

## FR-10: Historical tracking

The system must remember previously discovered jobs.

**Acceptance criteria**

* The same unchanged job does not repeatedly appear as new.
* Meaningful changes are recorded.
* Removed jobs retain historical data.
* First-seen and last-seen timestamps are available.

## FR-11: Scheduled scanning

The system must run automatically on a configured schedule.

**Acceptance criteria**

* A daily run can be configured.
* Scan results and failures are logged.
* One source failure does not cancel the complete run.
* The user can trigger a manual scan.

## FR-12: Source observability

The system must make source health visible.

**Acceptance criteria**

* Last successful retrieval is shown.
* Repeated failures are flagged.
* Sources can be disabled.
* Unique-job yield can be measured per source.

---

# 23. Nonfunctional Requirements

## 23.1 Reliability

* Daily scans should complete even when individual sources fail.
* Failed tasks should be retryable.
* Source-specific code should be isolated to prevent one source change from breaking the system.

## 23.2 Performance

* The dashboard should load the initial feed within three seconds under normal conditions.
* Saving or dismissing a listing should feel immediate.
* Long-running ingestion and scoring work should run asynchronously from page requests.

## 23.3 Security

* Resume and profile data must not be publicly accessible.
* Secrets and API credentials must not be stored in source control.
* Administrative access should require authentication.
* Logs should avoid unnecessary exposure of personal data.

## 23.4 Privacy

* Only data required for job matching should be stored.
* The user should be able to export or delete profile and job-history data.
* Personal profile information should not be sent to sources during retrieval.
* Model providers should receive only the content necessary for the specific evaluation request.

## 23.5 Maintainability

* Sources should use a common adapter interface.
* Matching weights should be configuration-driven.
* Prompt and rules versions should be recorded.
* Raw source data should remain available for debugging.

## 23.6 Cost controls

* Deduplicate before performing expensive semantic or LLM analysis when possible.
* Cache evaluations for unchanged listings.
* Use cheaper structured parsing methods before LLM extraction.
* Limit repeated evaluation of previously dismissed or unchanged roles.
* Track cost per scan and cost per strong match.

---

# 24. Suggested Technical Architecture

The PRD does not mandate a specific technology stack, but the MVP should use a modular architecture.

## 24.1 Core components

### Source adapters

Retrieve listings from feeds, APIs, HTML pages, or search results.

### Ingestion scheduler

Runs source adapters and records scan results.

### Parsing and normalization service

Converts raw listings into the common schema.

### Deduplication service

Links listings that represent the same role.

### Profile service

Stores the resume-derived candidate profile and preferences.

### Match engine

Applies filters, rules, semantic comparisons, and LLM analysis.

### Job database

Stores raw listings, normalized jobs, match results, history, and feedback.

### Web application

Displays the radar feed, job details, filters, and settings.

### Notification service

Optionally produces a daily email digest.

## 24.2 Suggested processing flow

1. Scheduler starts scan.
2. Source adapters retrieve listings.
3. Raw listings are stored.
4. Listings are normalized.
5. Exact duplicates are detected.
6. Near-duplicates are evaluated.
7. Existing jobs are checked for changes.
8. Hard filters are applied.
9. Eligible new or changed jobs are scored.
10. Explanations are generated.
11. Dashboard feed is updated.
12. Daily digest is produced, when enabled.
13. Source and scan metrics are recorded.

---

# 25. Analytics and Measurement

## 25.1 North-star metric

**Strong-match discovery rate**

The number of newly discovered roles per week that the user saves, applies to, or explicitly marks as a strong opportunity.

## 25.2 Primary metrics

* New unique jobs discovered per day
* Excellent matches per week
* Strong matches per week
* Percentage of surfaced jobs saved
* Percentage of surfaced jobs dismissed
* Percentage of saved jobs later marked applied
* Duplicate reduction rate
* Percentage of jobs found first through non-major sources
* Median age of a job when first discovered
* Time spent reviewing jobs per day
* Strong matches per 100 raw listings
* Strong matches per source
* Source failure rate

## 25.3 Quality metrics

* False-positive rate
* False-negative examples reported by the user
* Incorrect seniority classification rate
* Incorrect remote-status classification rate
* Duplicate merge error rate
* Percentage of explanations judged useful
* Percentage of surfaced jobs with working canonical links
* Percentage of jobs with high or medium evaluation confidence

## 25.4 Cost metrics

* Retrieval cost per daily scan
* Parsing cost per listing
* LLM cost per evaluated listing
* Total monthly infrastructure cost
* Cost per saved job
* Cost per applied job

---

# 26. MVP Success Criteria

The MVP should be evaluated during an initial two-week trial.

It will be considered promising when:

1. It consistently finds relevant Product Management opportunities from multiple source types.
2. It surfaces at least five strong or excellent matches per week, subject to actual market conditions.
3. At least one valuable role is found that the user had not already seen through normal job searching.
4. Duplicate listings are reduced enough that the user rarely reviews the same role twice.
5. Most visible match explanations are judged accurate and useful.
6. Daily review can be completed in approximately ten minutes or less.
7. At least 20% of excellent and strong matches are saved or marked applied.
8. Source failures are visible and do not prevent the rest of the scan from completing.
9. The user prefers reviewing the radar to manually checking multiple job boards.

The number of roles alone is not a sufficient success measure. A small number of high-value discoveries is preferable to a large number of weak matches.

---

# 27. MVP Release Scope

## Required for first usable release

* Resume ingestion
* Editable preferences file
* Candidate profile
* At least three distinct source categories
* Daily scheduled scanning
* Search-query generation
* Normalized job records
* Exact and near-duplicate handling
* Hard filters
* Personalized match score
* Match explanation
* Ranked web dashboard
* Canonical application links
* Save and dismiss actions
* First-seen history
* Basic source-health reporting
* Manual scan control

## Desirable but removable from first release

* Daily email digest
* Mark as applied
* Compensation normalization
* Automatic feedback-based weight adjustments
* Detailed source-history interface
* Searchable archive
* Advanced charts and analytics

---

# 28. Future Roadmap

## Phase 2: Better intelligence

* More source adapters
* Automatic target-company discovery
* Improved salary normalization
* Company-stage and funding information
* Company-quality signals
* Hiring-velocity detection
* Role-change alerts
* Better stale-listing detection
* More sophisticated preference learning
* Natural-language preference editing

## Phase 3: Opportunity context

* Company research briefs
* Product and market summaries
* Recent company news
* Funding and leadership changes
* Identification of likely hiring managers
* Personal-network and referral signals
* Role-specific resume-gap analysis
* "Why now?" opportunity analysis

## Phase 4: Application support

* Resume tailoring
* Cover-letter drafting
* Outreach drafting
* Application checklist
* Application tracking
* Interview preparation
* Follow-up reminders

## Phase 5: Multi-user product

* User accounts
* Generalized onboarding
* Multiple candidate profiles
* Configurable search templates
* Subscription tiers
* Privacy controls
* Team or coach access
* Shared role review
* Broader professional categories

Multi-user development should begin only after the single-user radar demonstrates repeated value.

---

# 29. Risks and Mitigations

## 29.1 Source access changes

**Risk:** Public pages and job systems may change structure or restrict automated access.

**Mitigation:**

* Isolate each source adapter.
* Prefer APIs, feeds, and structured data.
* Monitor source health.
* Maintain multiple source categories.
* Disable broken sources without stopping the system.

## 29.2 Excessive duplicates

**Risk:** Broad discovery produces many copies of the same job.

**Mitigation:**

* Normalize company names and titles.
* Prefer official identifiers.
* Use semantic description similarity.
* Preserve manual merge and unmerge controls.

## 29.3 Weak personalization

**Risk:** Results remain equivalent to ordinary keyword alerts.

**Mitigation:**

* Extract structured evidence from the resume.
* Score responsibilities, scope, and domain separately.
* Require specific explanations.
* Collect dismissal reasons.
* Review false positives during the first two weeks.

## 29.4 Over-filtering

**Risk:** Strict filters hide unconventional but valuable roles.

**Mitigation:**

* Separate hard filters from ranking preferences.
* Keep a possible-match tier.
* Record excluded jobs for inspection.
* Avoid permanent exclusion based on one dismissal.

## 29.5 LLM inconsistency

**Risk:** Evaluations or explanations vary unpredictably.

**Mitigation:**

* Combine rules with semantic analysis.
* Store model and prompt versions.
* Require structured output.
* Keep score calculations deterministic where possible.
* Cache evaluations for unchanged listings.

## 29.6 Stale listings

**Risk:** The radar recommends roles that are no longer active.

**Mitigation:**

* Prefer official listings.
* Reverify links.
* Track last-seen dates.
* Label uncertainty.
* Lower ranking for old or third-party-only listings.

## 29.7 Too much source breadth too early

**Risk:** Engineering effort is spent maintaining many low-value sources.

**Mitigation:**

* Track source yield.
* Start with several structurally different source categories.
* Add sources based on unique-job and strong-match contribution.
* Deprioritize sources that contribute mostly duplicates.

## 29.8 Misleading score precision

**Risk:** A score of 86 appears more scientifically exact than it is.

**Mitigation:**

* Emphasize match tiers and explanations.
* Show dimension breakdowns.
* Display confidence.
* Treat scores as prioritization aids, not predictions.

---

# 30. Open Configuration Decisions

These decisions do not block initial development because they can begin with configurable defaults:

* Exact minimum compensation
* Maximum acceptable hybrid-office frequency
* Whether New York and California hybrid roles appear by default
* Whether contract or fractional roles are enabled
* Relative priority of AI, developer tools, data, healthcare, and civic technology
* Maximum number of daily digest results
* Exact stale-listing threshold
* Exact score weights
* Whether ordinary Product Manager titles require a minimum compensation or experience signal

The system should expose these as preferences rather than hard-code them.

---

# 31. Initial Product Hypothesis

A personalized radar that searches more broadly than any individual job board, removes duplicates, and provides credible fit explanations will produce better opportunities with less daily effort than manual searching or ordinary keyword alerts.

The most important assumption to test is not whether the system can collect many jobs. It is whether it can consistently identify the small number of jobs that Ankita considers worth reviewing or applying to.

---

# 32. Initial End-to-End Acceptance Test

The MVP is ready for personal use when the following scenario succeeds:

1. Ankita uploads a current resume.
2. The application creates an editable candidate profile.
3. Ankita provides or edits a preferences file.
4. A scan runs across at least three source categories.
5. The system retrieves raw Product Management listings.
6. Duplicate copies are consolidated.
7. Junior and otherwise ineligible roles are filtered.
8. Eligible roles receive personalized scores.
9. The highest-ranked jobs include specific reasons and concerns.
10. Ankita opens the dashboard and sees only new or changed roles.
11. Ankita saves one role and dismisses another.
12. The actions persist.
13. The next daily scan does not present unchanged jobs as new.
14. The dismissed-job reason can influence later ranking.
15. The original company application page is available for each recommended role whenever one can be identified.

At that point, Job Radar will have completed its core job: converting a fragmented internet-wide job search into a focused, personalized stream of actionable Product Management opportunities.
