# Lab 6 — Code and Branch Coverage Analysis

**Name:** Gaurav Girish
**SRN:** PES1UG24AM103
**Assigned repo:** https://github.com/SETAPESU26/L6_L7_37_irrigation_scheduler
**Module under test:** `irrigation_scheduler.py`

---

## 1. Setup

```
pip install coverage pytest
```

## 2. Commands used

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

`--source=irrigation_scheduler` restricts the report to the application module so
that the test files themselves are not counted in the percentage.

## 3. Results

### 4.1 Code (line) coverage — 100 %

```
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
irrigation_scheduler.py      38      0   100%
-------------------------------------------------------
TOTAL                        38      0   100%
```

15 tests, all passing. Every one of the 38 executable statements is reached:
all three `should_irrigate()` early exits, all four `return` paths, every
`litres` assignment and both temperature scalings in `water_volume()`, the
`raise ValueError`, and the `continue` / `break` / `append` statements inside
`schedule()`.

### 4.2 Branch coverage — 100 %

```
Name                      Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------
irrigation_scheduler.py      38      0     28      0   100%
---------------------------------------------------------------------
TOTAL                        38      0     28      0   100%
```

39 tests, all passing. All 28 branch arcs are taken, with `BrPart = 0` (no
partially-covered decisions) and nothing listed under `Missing`.

## 4. Analysis — why line coverage was not enough

The two suites were measured against the **same module**, which makes the
difference between the metrics measurable rather than theoretical.

Running the *code-coverage* suite a second time with `--branch` gives:

```
Name                      Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------
irrigation_scheduler.py      38      0     28      1    98%   35->43
---------------------------------------------------------------------
TOTAL                        38      0     28      1    98%
```

100 % of lines, but only 98 % of branches, with one arc missing: `35->43`.

Lines 33–43 of the module are:

```python
33  def schedule(zones, budget):
34      plan = []
35      for name, area, moisture, rain, stage, temp in zones:
36          if not should_irrigate(moisture, rain, stage):
37              continue
38          need = water_volume(area, stage, temp)
39          if need > budget:
40              break
41          budget -= need
42          plan.append(name)
43      return plan
```

`35->43` is the arc where the **`for` loop finishes normally** — the zone list is
exhausted and control falls through to `return plan`. The code-coverage suite
never takes it, because each of its `schedule()` tests ends by hitting `break`
on line 40. `break` jumps straight to line 43 without the loop ever running out
of items, so lines 35 and 43 are both marked as executed while the arc between
them is not. This is precisely the blind spot the lab describes: a statement can
be reached without every route into it being tested.

The branch suite closes the gap with two tests that cannot be motivated by line
coverage at all, since they execute no new statement:

* `test_schedule_empty_zone_list` — `zones = []`, so the loop body is never entered.
* `test_schedule_runs_to_completion` — a single affordable zone, so the loop runs out of items instead of breaking.

The same reasoning drove the rest of the branch suite. Every decision in this
module is a **threshold comparison**, so each one was tested on both sides and
exactly *on* the boundary:

| Decision | True case | False case | Boundary tested |
|----------|-----------|------------|-----------------|
| `moisture >= 60` | 70 | 59 | 60 |
| `rain_mm >= 10` | 12 | 9 | 10 |
| `stage == "seedling"` | `"seedling"` | `"flowering"` | — |
| `moisture < 45` | 40 | 50 | 45 |
| `stage == "flowering"` | `"flowering"` | `"vegetative"` | — |
| `moisture < 55` | 50 | 58 | 55 |
| `rain_mm >= 5` | 6 | 4 | 5 |
| `moisture < 40` | 39 | 50 | 40 |
| `area_m2 <= 0` | 0, −5 | 1 | 0 |
| `temp_c > 35` | 40 | 25 | 35 |
| `temp_c < 10` | 5 | 25 | 10 |
| `need > budget` | 500 vs 50 | 20 vs 45 | need == budget (20 vs 20) |
| `not should_irrigate(...)` | wet zone skipped | dry zone watered | — |
| `for ... in zones` | zone processed | empty list / list exhausted | — |

The boundary cases are the practical payoff of chasing branch coverage. Three of
them — `moisture == 45`, `temp_c == 35` and `need == budget` — are exactly the
inputs where an off-by-one in the comparison operator would change the result,
and none of them is required to reach 100 % line coverage.

## 5. Additional validation — does the extra coverage actually catch bugs?

Coverage only says which code ran, not whether a test would notice if that code
were wrong. To check that the branch suite is genuinely stronger and not just
longer, each decision in `irrigation_scheduler.py` was deliberately broken one
at a time (`>=` changed to `>`, `<` to `<=`, a rate constant altered, `break`
changed to `continue`) and both suites were re-run against each faulty version.
A suite "kills" a fault if at least one of its tests fails.

| Injected fault | Line suite | Branch suite |
|----------------|-----------|--------------|
| `rain_mm >= 10` → `> 10` | survived | killed |
| `moisture < 45` → `<= 45` | survived | killed |
| `moisture < 55` → `<= 55` | survived | killed |
| `rain_mm >= 5` → `> 5` | survived | killed |
| `moisture < 40` → `<= 40` | survived | killed |
| `area_m2 <= 0` → `< 0` | killed | killed |
| `temp_c > 35` → `>= 35` | survived | killed |
| `temp_c < 10` → `<= 10` | survived | killed |
| `need > budget` → `>= budget` | survived | killed |
| `litres = 2` → `3` | killed | killed |
| `litres = 5` → `6` | killed | killed |
| `litres = 4` → `3` | killed | killed |
| `break` → `continue` | survived | killed |
| **Total** | **4 / 13** | **13 / 13** |

The line suite reports 100 % coverage yet misses 9 of the 13 injected faults —
every one of them an off-by-one on a decision boundary, plus the `break` that
stops the schedule. The branch suite catches all 13.

One further mutation, `moisture >= 60` → `moisture > 60`, survives both suites.
That one is not a gap in the tests: 60 is higher than every other threshold in
the function (45, 55 and 40), so an input of exactly 60 returns `False` whether
it exits early or falls through the rest of the logic. The two versions are
indistinguishable for all inputs, i.e. an *equivalent mutant*, which no test can
kill.

## 6. Conclusion

* **Line coverage: 100 %** (38/38 statements) with 15 tests.
* **Branch coverage: 100 %** (28/28 arcs, 0 partial) with 39 tests.
* Line coverage alone reported a perfect 100 % while a real decision path — the
  loop-exhaustion arc in `schedule()` — had never been executed. Branch coverage
  exposed it. Line coverage measures *what was reached*; branch coverage
  measures *how it was reached*, which is the stricter and more useful signal.
