# Lab 7: Fuzzing for Input Validation Bugs

**Name:** Gaurav Girish  **SRN:** PES1UG24AM103
**Assigned repo:** https://github.com/SETAPESU26/L6_L7_37_irrigation_scheduler
**Module under test:** `irrigation_scheduler.py` (the `lab7/` module) — parses a
field zone, averages soil-moisture readings and estimates the water a plot needs
**Tools:** hypothesis 6.170.15, pytest 9.2.0 (Python 3.13.0)

## Results

| Metric | Before the fix | After the fix |
|--------|----------------|---------------|
| Fuzz suite | 54 failed, 5 passed | **59 passed** |
| Distinct crashes reported by Hypothesis | 11 — 4 + 3 + 4 across the three functions | **0** |
| Nonsense values accepted silently | 14 recorded | **0** |
| Behaviour on malformed input | traceback, process exits | message printed, prompt re-asked |
| Behaviour on valid input | correct | unchanged — still correct |

The test file is **identical** in Step 4 and Step 6. The same 59 tests that
report 54 failures against the original module pass against the hardened one.

## Setup

```
pip install hypothesis pytest
```

## Commands

```
python3 irrigation_scheduler.py
python3 -m pytest test_irrigation_scheduler.py
```

To reproduce the failing run from Step 4, against the original module:

```
cd before && python3 -m pytest test_irrigation_scheduler.py
```

`pytest.ini` keeps `before/` out of collection, so `pytest` in this folder
tests the fixed module and reports 59 passed.

## What the fuzzer found

Two separate families of defect, and the second is the more interesting one.

**Family A — uncontrolled crashes.** Nine cases in which an exception escapes to
the caller. Hypothesis shrank them to minimal inputs: `None` (`AttributeError`
from `.split`), `b''` (`TypeError`), `''` and `':'` and `'|'` (`ValueError` from
unpacking and from `float()`), `'1,,3'` and `'one,two'` and `'12.5'`
(`ValueError` from `int()`), `'a:1:2'` (too many values to unpack).

**Family B — nonsense accepted silently.** Fourteen inputs that raise nothing at
all and return a physically meaningless answer: an area of `-120` m², an area of
`0`, `float()` accepting the literals `'nan'`, `'inf'` and `'1e400'` (the last
overflowing to infinity), non-ASCII digits parsing as numbers, soil moisture of
`-5 %` and `101 %`, `nan` slipping through `max(need, 0)`, a return type that
changes between `float` and `int`, and a 100,000-element reading list processed
in full. These are the ones a plain "it must not crash" property would miss
entirely, which is why every property here also asserts post-conditions on the
value returned.

One candidate turned out **not** to be a bug, and fuzzing is what settled it.
The `sum(values) // len(values)` looks like a `ZeroDivisionError` waiting to
happen, but no input reaches it: `str.split` always returns at least one field.
The division is safe only by accident, so the hardened version checks the list
is non-empty anyway rather than relying on that accident.

## The fix

`InvalidInputError(ValueError)` is now the only exception the public functions
raise, which is what lets a caller — or a fuzz test — tell a deliberate
rejection apart from a crash. Validation uses explicit ASCII-only regular
expressions instead of trusting `float()` and `int()`, both of which accept
`'nan'`, `'inf'`, `'1e400'`, `'1_000'` and non-ASCII digits. Each quantity is
given the range it can physically take: area in `0 < a ≤ 1e6` m², moisture in
`0 ≤ r ≤ 100` percent, rainfall in `0 ≤ r ≤ 1000` mm, raw input at most 500
characters.

For valid input the arithmetic is untouched — `name.title()`,
`sum(values) // len(values)` and `area * 5 - rainfall` are exactly as they were,
which is what the six "behaviour on valid input" tests exist to guarantee.

Beyond the 200 examples per property that pytest runs, the three properties were
re-run with a wider strategy and 6,000 examples each — 18,000 generated inputs,
0 violations. The six worked examples in the module docstrings pass under
`python3 -m doctest irrigation_scheduler.py`.

## A note on file names

The handout calls the files `processor.py` and `test_processor.py`. In the
repository assigned to this SRN they are `irrigation_scheduler.py` and
`test_irrigation_scheduler.py`, and those names are used throughout. Every
command is otherwise the one given in the handout.

## Contents

| File | Description |
|------|-------------|
| `Lab7_Fuzz_Testing_Report_PES1UG24AM103.pdf` | The report — screenshots for Steps 2, 4, 5 and 6, the defect tables, and both source listings |
| `irrigation_scheduler.py` | **Deliverable 2** — the fixed application script |
| `test_irrigation_scheduler.py` | **Deliverable 3** — the completed Hypothesis suite, 59 tests |
| `irrigation_scheduler_BEFORE_fix.py` | The original buggy module, kept for reference |
| `pytest.ini` | Keeps `before/` out of collection |
| `before/` | The original module plus the same test file, so the Step 2 and Step 4 runs stay reproducible |
| `screenshots/` | The 19 screenshot images used in the report |
| `transcripts/` | The plain-text terminal transcripts the screenshots were rendered from |

## The test suite, in four groups

| Group | Tests | What it asserts |
|-------|-------|-----------------|
| No-crash properties | 3 | The three names from the starter file. Each function either accepts the input and satisfies its post-conditions, or rejects it with `InvalidInputError` |
| Behaviour on valid input | 6 | Hardening did not change the answer — round-trip of name and area, whitespace tolerance, the average and the water estimate against reference implementations |
| Regression tests | 48 | The concrete inputs Hypothesis shrank to, pinned one per case |
| Oversized input | 2 | A 100,000-element reading list and a 100,000-character zone name are refused, not processed |
