from conftest import make_job

from radar.dedupe import dedupe_batch, is_near_dup
from radar.filters import hard_filter

PREFS = {"companies_excluded": ["Upward Health"],
         "compensation": {"min_base_salary_usd": 170000},
         "visa_sponsorship_required": True}


def test_near_dup_merges_ats_and_aggregator_copy():
    ats = make_job()
    agg = make_job(title="Senior Product Manager - AI Platform",
                   source="jobspy:indeed", source_type="aggregator", ats=None,
                   source_url="https://indeed.com/x", canonical_url="https://indeed.com/x")
    kept = dedupe_batch([agg, ats], threshold=90)
    assert len(kept) == 1
    assert kept[0].source_type == "ats"  # canonical = ATS-direct wins


def test_different_companies_never_near_dup():
    a = make_job()
    b = make_job(company="Other Corp")
    assert not is_near_dup(a, b, 90)


def test_below_threshold_not_merged():
    a = make_job()
    b = make_job(title="Senior Product Manager, Payments",
                 description="Own payments infrastructure and billing. " * 10)
    assert len(dedupe_batch([a, b], threshold=90)) == 2


def test_filter_junior_titles():
    assert hard_filter(make_job(title="Associate Product Manager"), PREFS)
    assert hard_filter(make_job(title="Product Management Intern (Summer 2027)"), PREFS)
    assert hard_filter(make_job(title="Junior PM"), PREFS)


def test_filter_non_pm_and_title_traps():
    assert hard_filter(make_job(title="Head of Product Design"), PREFS)
    assert hard_filter(make_job(title="Product Marketing Manager"), PREFS)
    assert hard_filter(make_job(title="Software Engineer"), PREFS)
    assert hard_filter(make_job(title="Director, Product Management - AI")) is None


def test_filter_non_us_geography_trap():
    # perfect title/domain, ineligible geography — golden set candidate #12
    job = make_job(title="Senior Product Manager, AI Platform Management",
                   location="Remote, Ireland; Remote, Israel; Remote, United Kingdom")
    assert hard_filter(job, PREFS) == "remote_but_not_us_eligible"
    assert hard_filter(make_job(location="Toronto", remote_status="onsite"), PREFS) == "location_not_us"
    assert hard_filter(make_job(location="Remote, US"), PREFS) is None
    assert hard_filter(make_job(location="Mountain View, CA", remote_status="onsite"), PREFS) is None


def test_salary_floor_only_when_stated():
    assert hard_filter(make_job(salary_min=90000, salary_max=120000), PREFS) == "stated_salary_below_floor"
    assert hard_filter(make_job(salary_min=None, salary_max=None), PREFS) is None  # unknown passes


def test_visa_sponsorship_explicit_exclusions_rejected():
    cases = [
        "Great role. We are unable to sponsor visas now or in the future.",
        "Must be authorized to work in the United States without the need for visa sponsorship.",
        "Applicants must be U.S. citizens only due to contract requirements.",
        "Visa sponsorship is not available for this position.",
        "This role is subject to ITAR; U.S. persons required.",
        "An active TS/SCI clearance is required.",
        "We cannot provide visa sponsorship at this time.",
    ]
    for text in cases:
        job = make_job(description="Own the roadmap. " * 5 + text)
        assert hard_filter(job, PREFS) == "no_visa_sponsorship", text


def test_visa_sponsorship_silence_and_positive_pass():
    silent = make_job()  # says nothing about sponsorship
    assert hard_filter(silent, PREFS) is None
    positive = make_job(description="Own the roadmap. " * 5
                        + "Visa sponsorship is available for qualified candidates.")
    assert hard_filter(positive, PREFS) is None
    # gate off -> even explicit language passes through
    off = dict(PREFS, visa_sponsorship_required=False)
    explicit = make_job(description="We are unable to sponsor visas.")
    assert hard_filter(explicit, off) is None


def test_excluded_company_and_employment_type():
    assert hard_filter(make_job(company="Upward Health"), PREFS) == "company_excluded"
    assert hard_filter(make_job(employment_type="contract"), PREFS) == "not_full_time"
    assert hard_filter(make_job(employment_type="unknown"), PREFS) is None
