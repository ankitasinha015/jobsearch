"""Pins the D3 normalization rules — the silent-quality-bug layer."""
from radar.normalize import (infer_remote, normalize_ashby, normalize_greenhouse,
                             normalize_lever, strip_html)

CO = {"name": "Acme", "slug": "acme", "ats": "greenhouse"}


def test_greenhouse_content_is_html_escaped_html():
    # The real API returns &lt;p&gt;... — the invisible dedup/LLM poisoner
    raw = {"title": "Senior Product Manager",
           "location": {"name": "Remote - US"},
           "content": "&lt;p&gt;Own the &amp;amp; roadmap&lt;/p&gt;&lt;ul&gt;&lt;li&gt;Ship things&lt;/li&gt;&lt;/ul&gt;",
           "absolute_url": "https://x/1", "updated_at": "2026-07-01T10:00:00Z"}
    job = normalize_greenhouse(raw, CO)
    assert "<" not in job.description and "&lt;" not in job.description
    assert "Own the & roadmap" in job.description
    assert "Ship things" in job.description
    assert job.date_posted == "2026-07-01"


def test_strip_html_keeps_line_structure():
    text = strip_html("&lt;h2&gt;About&lt;/h2&gt;&lt;p&gt;First&lt;/p&gt;&lt;p&gt;Second&lt;/p&gt;")
    assert "About" in text and "First" in text
    assert text.index("First") < text.index("Second")


def test_lever_assembles_description_plus_lists():
    raw = {"text": "Product Lead", "categories": {"location": "San Francisco, CA"},
           "descriptionPlain": "Intro paragraph.",
           "lists": [{"text": "What you'll do", "content": "<li>Lead roadmap</li>"}],
           "hostedUrl": "https://jobs.lever.co/acme/1", "workplaceType": "hybrid"}
    job = normalize_lever(raw, {**CO, "ats": "lever"})
    assert "Intro paragraph." in job.description
    assert "What you'll do" in job.description and "Lead roadmap" in job.description
    assert job.remote_status == "hybrid" and job.remote_status_provenance == "stated"


def test_ashby_stated_fields_and_compensation():
    raw = {"title": "Staff Product Manager", "location": "New York",
           "descriptionPlain": "Do product things.", "isRemote": True,
           "employmentType": "FullTime",
           "compensation": {"summaryComponents": [
               {"compensationType": "Salary", "minValue": 170000.0,
                "maxValue": 210000.0, "currencyCode": "USD"}]},
           "jobUrl": "https://jobs.ashbyhq.com/acme/1", "publishedAt": "2026-07-05T00:00:00Z"}
    job = normalize_ashby(raw, {**CO, "ats": "ashby"})
    assert job.remote_status == "remote" and job.remote_status_provenance == "stated"
    assert job.salary_min == 170000 and job.salary_max == 210000 and job.currency == "USD"
    assert job.date_posted == "2026-07-05"


def test_unknown_stays_unknown_never_invented():
    raw = {"title": "Product Manager", "location": {"name": "Chicago, IL"},
           "content": "&lt;p&gt;Office based role.&lt;/p&gt;", "absolute_url": "https://x/2"}
    job = normalize_greenhouse(raw, CO)
    assert job.salary_min is None and job.salary_max is None
    assert job.remote_status == "unknown"
    assert job.remote_status_provenance == "unknown"


def test_remote_inference_is_labeled_inferred():
    status, prov = infer_remote("Senior PM (Remote)", "Anywhere", "")
    assert status == "remote" and prov == "inferred"
