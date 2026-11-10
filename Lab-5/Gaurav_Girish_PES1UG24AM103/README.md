# Lab 5: Static Code Analysis

**Name:** Gaurav Girish  **SRN:** PES1UG24AM103
**Assigned repo:** https://github.com/SETAPESU26/L5_37_todo_manager
**Program:** `todo_manager.py` — a to-do list and task manager
**Tools:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.5.0 (Python 3.13.0)

## Results

| Tool | Before | After | Target |
|------|--------|-------|--------|
| Pylint | 5.09/10, 27 messages | **10.00/10**, 0 messages | above 9.5 |
| Bandit | 4 findings — 1 High, 1 Medium, 2 Low | **0 findings**, no `#nosec` | all handled |
| Flake8 | 4 errors — E225, E303, E261, E231 | **0 errors** (report is empty) | all handled |

Fifteen issues are documented and all fifteen are fixed, against a required
minimum of four. The program still runs with no input and prints the same
information as before.

## Contents

| File | Description |
|------|-------------|
| `todo_manager.py` | Cleaned program: Pylint 10.00/10, no Bandit findings, no Flake8 errors |
| `issues.md` | Issue table — type, line numbers, description and fix approach for all 15 issues, ordered by severity |
| `reflection.md` | Answers to the four reflection questions |
| `pylint_report_before.txt` | Pylint before — 5.09/10, 27 messages |
| `bandit_report_before.txt` | Bandit before — 1 High, 1 Medium, 2 Low |
| `flake8_report_before.txt` | Flake8 before — 4 errors |
| `pylint_report.txt` | Pylint after — 10.00/10 |
| `bandit_report.txt` | Bandit after — "No issues identified" |
| `flake8_report.txt` | Flake8 after — empty, because nothing is reported |

## Commits, one per tool

| Commit | Contents |
|--------|----------|
| Add Lab 5 starting point | `todo_manager.py` exactly as provided, so the fix commits show a diff |
| Fix Pylint issues | C0114, C0116, C0103 ×14, W0102, R1710, W1514, `__main__` guard |
| Fix Bandit issues | B605 (High), B301 (Medium), B403, B311 |
| Fix Flake8 issues | E225, E303, E261, E231 |

## The three most significant fixes

1. **B605, High, CWE-78 — command injection.** `os.system("mail -s 'Pending tasks' " + address + " < tasks.json")` built a shell command by string concatenation, so an address like `a@b.com; rm -rf ~` would have been run by the shell. Fixed by removing the shell entirely: the message is composed with `email.message.EmailMessage` and sent with `smtplib`. Using `subprocess.run` instead would have traded the one High finding for three Low ones (B404, B603, B607), which is why that route was rejected.
2. **B301, Medium, CWE-502 — insecure deserialization.** `pickle.load` executes code embedded in the data, so anyone able to write `tasks.pkl` could run code as this user. The store is now JSON, a data-only format.
3. **W0102 — mutable default argument.** `labels=[]` is evaluated once at definition time, so all four demo calls shared one list, which accumulated `['high', 'medium', 'low', 'high']` — and was then discarded without ever being stored. The default is now `None`, a fresh list is built per call, and the labels are stored on the task.

## Reproduce

```
python -m venv venv && source venv/bin/activate
python -m pip install pylint bandit flake8
python todo_manager.py
python -m pylint todo_manager.py
python -m bandit -r todo_manager.py
python -m flake8 todo_manager.py
```
