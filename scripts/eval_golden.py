"""Golden-set eval: score golden_set.jsonl and report tier agreement vs labels.

Predictions are pipeline-faithful: hard filters run first (a filtered job is
predicted "hard-reject" without an LLM call); everything else gets LLM-scored.
Expected "hard-reject" also accepts a scored tier of "hidden" (<40) — both mean
"never shown" in the real pipeline.

Gate (BUILDSPEC): >= 80% exact tier agreement (18/22).
Run: python scripts/eval_golden.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from radar import config  # noqa: E402

config.bootstrap_env()

import anthropic  # noqa: E402

from radar import score as scorer  # noqa: E402
from radar.filters import hard_filter  # noqa: E402
from radar.models import Job  # noqa: E402

ADJACENT = {("excellent", "strong"), ("strong", "excellent"),
            ("strong", "possible"), ("possible", "strong"),
            ("possible", "weak"), ("weak", "possible"),
            ("weak", "hidden"), ("hidden", "weak"),
            ("weak", "hard-reject"), ("hard-reject", "weak")}


def matches(got: str, expected: str) -> bool:
    if got == expected:
        return True
    return expected == "hard-reject" and got == "hidden"


def main():
    golden_path = config.ROOT / "golden_set.jsonl"
    if not golden_path.exists():
        sys.exit("golden_set.jsonl not found — run scripts/build_golden_set.py first.")
    weights = config.load_weights()
    client = anthropic.Anthropic()
    system_blocks = scorer.build_system_blocks()

    exact = adjacent = n = 0
    for line in golden_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        expected = rec.pop("expected_tier")
        rec.pop("label_reason", None)
        job = Job.model_validate(rec)

        filter_reason = hard_filter(job)
        if filter_reason:
            got, detail = "hard-reject", f"filter:{filter_reason}"
        else:
            ev = scorer.evaluate_job(client, job, weights, system_blocks)
            got, detail = ev["tier"], f"score {ev['overall']}"

        n += 1
        ok = matches(got, expected)
        near = ok or (got, expected) in ADJACENT
        exact += ok
        adjacent += near
        mark = "MATCH" if ok else ("near " if near else "MISS ")
        print(f"{mark} {job.company:<13} {job.title[:42]:<44} "
              f"expected={expected:<11} got={got:<11} ({detail})")

    gate = -(-n * 8 // 10)  # ceil(0.8 * n)
    print(f"\nexact tier agreement:    {exact}/{n}")
    print(f"exact-or-adjacent:       {adjacent}/{n}")
    print(f"GATE (>={gate}/{n} exact):    "
          + ("PASS" if exact >= gate else "not yet — tune prompt/weights"))


if __name__ == "__main__":
    main()
