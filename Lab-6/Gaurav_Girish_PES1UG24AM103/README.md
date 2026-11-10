# Lab 6: Code and Branch Coverage Analysis

**Name:** Gaurav Girish  **SRN:** PES1UG24AM103
**Assigned repo:** https://github.com/SETAPESU26/L6_L7_37_irrigation_scheduler
**Module under test:** `irrigation_scheduler.py` — decides when a field zone
needs watering, how much water it needs, and builds a schedule within a budget
**Tools:** coverage 7.17.2, pytest 9.2.0 (Python 3.13.0)

## Results

| Metric | Result | Target |
|--------|--------|--------|
| Code (line) coverage | **100%** — 38/38 statements, 15 tests | at least 90% |
| Branch coverage | **100%** — 28/28 arcs, `BrPart 0`, 39 tests | at least 90% |

Both suites pass with no failures, and nothing is listed under `Missing`.

## Setup

```
pip install coverage pytest
```

## Commands

Code (line) coverage:

```
coverage run --source=irrigation_scheduler -m pytest CodeCoverageTest_PES1UG24AM103_irrigation_scheduler.py
coverage report -m
```

Branch coverage:

```
coverage run --branch --source=irrigation_scheduler -m pytest BranchCoverageTest_PES1UG24AM103_irrigation_scheduler.py
coverage report -m
```

`--source=irrigation_scheduler` keeps the test files themselves out of the
report, so the percentage describes the application module only.

## The finding

The line-coverage suite reports a clean **100%**. Re-running that same suite
with `--branch` drops it to **98%**, with one arc missing — `35->43`, the `for`
loop in `schedule()` running out of zones and falling through to `return plan`.
Every line-coverage test leaves that loop through `break` instead, so both lines
count as executed while the path between them never runs.

Injecting faults into the module one at a time confirms the gap is real rather
than cosmetic: the line suite catches **4 of 13** injected bugs, the branch
suite catches **13 of 13**. The nine it misses are all off-by-one errors on
decision boundaries, plus a `break` changed to `continue`.

Full working in `analysis.md`.

## Contents

| File | Description |
|------|-------------|
| `irrigation_scheduler.py` | The module under test, unchanged from the assigned repo |
| `CodeCoverageTest_PES1UG24AM103_irrigation_scheduler.py` | Code coverage suite — 15 tests, one per statement and return path |
| `BranchCoverageTest_PES1UG24AM103_irrigation_scheduler.py` | Branch coverage suite — 39 tests, both outcomes and the boundary of every decision |
| `test_irrigation_scheduler.py` | Starter test file, extended with the same cases |
| `analysis.md` | Full analysis — line vs branch, boundary table, fault-injection results |
| `screenshots/CodeCoverage_PES1UG24AM103.png` | Terminal output — line coverage, 100% |
| `screenshots/BranchCoverage_PES1UG24AM103.png` | Terminal output — branch coverage, 100% |
| `screenshots/LineVsBranch_PES1UG24AM103.png` | Terminal output — both metrics on the same suite, showing the 98% / `35->43` gap |

## Commits, one per coverage type

| Commit | Contents |
|--------|----------|
| Add code (line) coverage test cases | Code coverage suite, extended starter file, line coverage screenshot |
| Add branch coverage test cases | Branch coverage suite, extended starter file, branch and comparison screenshots, analysis |
