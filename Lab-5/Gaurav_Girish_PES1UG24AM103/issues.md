# Lab 5: Static Code Analysis — Identified Issues

**Name:** Gaurav Girish
**SRN:** PES1UG24AM103
**Repository:** L5_37_todo_manager
**File analysed:** `todo_manager.py`
**Tools:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.5.0 (Python 3.13.0, inside `venv`)

---

## 1. Results summary

| Tool | Before | After |
|------|--------|-------|
| Pylint | **5.09/10**, 27 messages | **10.00/10**, 0 messages |
| Bandit | **4 findings** — 1 High, 1 Medium, 2 Low | **0 findings** (no `#nosec` used) |
| Flake8 | **4 errors** — E225, E303, E261, E231 | **0 errors** (report file is empty) |

Commands used for both the before and the after reports:

```
python -m pylint todo_manager.py > pylint_report.txt
python -m bandit -r todo_manager.py > bandit_report.txt
python -m flake8 todo_manager.py > flake8_report.txt
```

Report files in this repository:

| Stage | Pylint | Bandit | Flake8 |
|-------|--------|--------|--------|
| Before | `pylint_report_before.txt` | `bandit_report_before.txt` | `flake8_report_before.txt` |
| After | `pylint_report.txt` | `bandit_report.txt` | `flake8_report.txt` |

---

## 2. Issue table

Line numbers refer to the **original** `todo_manager.py`. Rows are ordered by
severity, highest first, as the handout requires. Fifteen issues are documented
and all fifteen are fixed, against a required minimum of four.

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Bandit **B605** `start_process_with_a_shell` — **High**, CWE-78 | Security (command injection) | 57 | `os.system("mail -s 'Pending tasks' " + address + " < tasks.json")` builds a shell command by string concatenation. A caller-supplied address such as `a@b.com; rm -rf ~` is executed by the shell as a second command. | Removed the shell entirely. `remind_by_email` now builds an `email.message.EmailMessage` and sends it with `smtplib`, so no process is spawned. The address is validated to reject CR/LF, which also closes off email header injection. |
| Bandit **B301** `pickle.load` — **Medium**, CWE-502 | Security (insecure deserialization) | 47 | Unpickling executes constructor code embedded in the data, so anyone who can write `tasks.pkl` can run arbitrary code as this user. | Replaced the pickle store with JSON, a data-only format that cannot carry executable payloads. `save_tasks`/`load_tasks` now use `tasks_store.json`; task ids are cast back to `int` on load because JSON object keys are always strings. |
| Pylint **W0102** `dangerous-default-value` | Bug (mutable default argument) | 11 | `labels=[]` is evaluated once at definition time, so every call that omits `labels` shares one list. `labels.append(priority)` therefore accumulated `["high", "medium", "low", "high"]` across the four demo calls. | Default changed to `None`; a fresh list is built per call with `list(labels) if labels else []`. |
| Pylint **W0102** (same line, second defect) | Bug (dead code) | 13 | The mutated `labels` list was never stored in the task dictionary, so the argument had no effect at all — the bug above was invisible from the output. | The per-task list is now stored under a `"labels"` key, which makes the parameter do what its name promises. |
| Bandit **B403** `import pickle` — **Low**, CWE-502 | Security (risky import) | 3 | Advisory warning that the module is a deserialization risk. | The import was deleted along with its last use. |
| Bandit **B311** `random.choice` — **Low**, CWE-330 | Security (weak randomness) | 70 | `random` is a Mersenne Twister PRNG: its output is predictable once enough values are observed, so it must not be used where unpredictability matters. | Replaced with `secrets.choice`, which draws from the operating system's CSPRNG. `import random` removed. |
| Pylint **R1710** `inconsistent-return-statements` | Bug (inconsistent control flow) | 33–36 | `findTask` returned an id on a match but fell off the end on no match, returning `None` implicitly. A reader cannot tell whether that was intended, and the demo relied on it silently. | Added an explicit `return None` after the loop and documented it in the docstring, so every exit path returns a value deliberately. |
| Pylint **W1514** `unspecified-encoding` | Portability bug | 51 | `open(fileName, "w")` uses the platform's default encoding, so the same program writes different bytes on different machines and can raise `UnicodeEncodeError` on non-ASCII titles. | Every text-mode `open` now passes `encoding="utf-8"` explicitly. |
| Pylint **C0103** `invalid-name` (14 occurrences) | Style (naming convention) | 11, 12, 19, 27, 33, 34, 40, 45, 50, 55 | Functions, arguments and locals used camelCase (`addTask`, `taskId`, `fileName`), which violates the snake_case convention of PEP 8. | Renamed throughout: `addTask`→`add_task`, `completeTask`→`complete_task`, `pendingTasks`→`pending_tasks`, `findTask`→`find_task`, `saveTasks`→`save_tasks`, `loadTasks`→`load_tasks`, `exportJson`→`export_json`, `remindByEmail`→`remind_by_email`, `taskId`→`task_id`, `fileName`→`file_name`. |
| Pylint **C0114/C0116** `missing-module-docstring`, `missing-function-docstring` (10 occurrences) | Documentation | 1, 11, 19, 27, 33, 40, 45, 50, 55, 60 | Neither the module nor any of the nine functions was documented, so the contract of each function had to be inferred from its body. | Added a module docstring and a docstring for all nine functions, stating return values and the `None`/empty-match behaviour. |
| Module-level call to `main()` | Design | 79 | The demo ran on import, so merely importing the module created tasks and wrote files — which also makes the module untestable. | Guarded with `if __name__ == "__main__": main()`. |
| Flake8 **E225** `missing whitespace around operator` | Style | 12 | `taskId=len(tasks) + 1` — no spaces around `=`. | Written as `task_id = len(tasks) + 1`. |
| Flake8 **E303** `too many blank lines (3)` | Style | 40 | Three blank lines between `findTask` and `saveTasks`; PEP 8 allows two between top-level definitions. | Reduced to two blank lines. |
| Flake8 **E261** `at least two spaces before inline comment` | Style | 69 | `find_task("gym")) # returns None silently` — one space before `#`. | Two spaces before the `#`, and the comment reworded to `# None, no match`. |
| Flake8 **E231** `missing whitespace after ','` | Style | 74 | `print("Tasks restored from file:",len(restored))`. | Space added after the comma. |

---

## 3. Commits

One commit per tool, as the handout requires:

| # | Commit | Contents |
|---|--------|----------|
| 1 | `Fix Pylint issues: docstrings, snake_case naming, mutable default arg` | C0114, C0116, C0103, W0102, R1710, W1514, `__main__` guard |
| 2 | `Fix Bandit issues: remove shell command, pickle storage and weak RNG` | B605, B301, B403, B311 |
| 3 | `Fix Flake8 issues: PEP 8 whitespace and blank-line violations` | E225, E303, E261, E231 |

---

## 4. Behaviour after the fixes

The program still runs with no input and prints the same information:

```
No task with id 99
Pending tasks: ['Submit lab report', 'Book train tickets', 'Call plumber']
Task id for 'plumber': 3
Task id for 'gym': None
Try this next: Book train tickets
Tasks restored from file: 4
Exported tasks to tasks.json
```

Two intentional differences, both consequences of the security fixes:

1. The task store is `tasks_store.json` instead of `tasks.pkl` (B301). The
   JSON export is still written to `tasks.json`, so the last line is unchanged.
2. `Try this next:` is now drawn with `secrets.choice` (B311), so the suggested
   task varies between runs — exactly as it did with `random.choice`.

Each task dictionary also carries a `"labels"` key now, which is the data that
the original `labels` argument built and then threw away.
