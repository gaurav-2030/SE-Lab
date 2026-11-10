# Lab 5: Static Code Analysis — Reflection

**Name:** Gaurav Girish
**SRN:** PES1UG24AM103
**Repository:** L5_37_todo_manager

---

### 1. Which of the three tools did you find most useful, and why?

Bandit, because it was the only tool that found a defect that mattered more than
tidiness. Pylint and Flake8 both read `os.system("mail -s 'Pending tasks' " +
address + " < tasks.json")` without complaint — to them it is a well-formed call
to a documented standard library function. Bandit flagged it as B605, High
severity, CWE-78, and that one line was the most serious problem in the file: any
caller who could influence `address` could append `; rm -rf ~` and have the shell
run it.

That said, the three tools are not substitutes for each other, and the value is
in the overlap. Pylint found the defect with the widest blast radius — the
mutable default `labels=[]`, which quietly shared one list across every call —
and Bandit cannot see that, because it is a correctness bug rather than a
vulnerability. Flake8 found the least important issues but was by far the fastest
to act on: all four of its errors were mechanical, and fixing them cost under a
minute. Ranked by severity of what they catch the order is Bandit, Pylint,
Flake8; ranked by cost of ignoring them over a project's lifetime the order is
closer to the reverse, because style drift is what makes later reviews expensive.

### 2. Were any of the reported issues false positives, and how did you decide what to fix?

None of the 35 findings was a false positive in the sense of being factually
wrong, but they were not all equally worth acting on, and two needed a judgement
call.

B403 (`import pickle`) is a bare import warning: it fires on the import
regardless of whether the module is used dangerously. Had the program only
*written* pickles it would have been close to noise. Here it pointed at a real
B301 a few lines down, so it resolved itself when the dangerous use went away.

B311 (`random.choice`) is the finding most often dismissed as a false positive,
and the argument for dismissing it is reasonable: choosing which chore to do next
is not a security decision, and a predictable suggestion harms nobody. I fixed it
anyway for two reasons. The change to `secrets.choice` costs one line and no
performance that matters at this scale, and leaving a known finding unfixed means
the next person to read the report has to re-derive the same reasoning. A report
that is *clean* is far more useful than a report with three entries everyone has
privately agreed to ignore, because nobody notices a fourth entry appearing in
the latter.

The one finding where I deliberately rejected the obvious fix was B605. The
tempting fix is `subprocess.run` with a list of arguments, which does remove the
shell. I tested it, and Bandit then reports B404, B603 and B607 — all Low — so
the High finding would have been traded for three Low ones. More importantly,
that fix keeps a dependency on an external `mail` binary. Composing the message
with `email.message.EmailMessage` and sending it via `smtplib` removes the
subprocess entirely, which is why the final Bandit report is clean without a
single `#nosec`. I took the general rule from this to be: prefer removing the
dangerous mechanism over sanitising its input, because sanitising has to be
correct every time and removal only has to be correct once.

My priority order was therefore severity first (High → Medium → Low), but with
Pylint's correctness warnings — `W0102`, `R1710`, `W1514` — promoted above
Bandit's Low findings, since a wrong answer is a worse outcome than a
theoretical weakness in a chore picker.

### 3. How does static analysis contribute to code quality and maintainability?

The sharpest demonstration in this lab is the mutable default argument. The
original program ran, printed plausible output, and would have passed a
superficial test, because `labels.append(priority)` mutated a list that was then
discarded — the bug was real but invisible. No test of the printed output could
have caught it. Pylint found it in under a second by reasoning about when the
default expression is evaluated, which is exactly the kind of reasoning humans
are bad at doing consistently over a long file.

Beyond finding individual bugs, three effects stood out:

- **It shortens the feedback loop.** Fixing `W1514` took seconds. Discovering the
  same bug as a `UnicodeEncodeError` from a user on a differently configured
  machine would have cost hours of investigation first.
- **It makes the code reviewable.** Ten missing docstrings and fourteen camelCase
  names are each trivial, but together they force every reader to infer what the
  code means instead of reading what it says. Once a file is consistent,
  reviewers spend their attention on logic, which is where it is worth spending.
- **It turns conventions into something mechanical rather than interpersonal.**
  "Two spaces before an inline comment" is a far better instruction coming from
  E261 than from a colleague, and nobody has to argue about it.

The limits are equally clear. A clean report is not a correct program. Static
analysis cannot tell that `PRIORITY_ORDER[task["priority"]]` will raise
`KeyError` on an unrecognised priority string, that `len(tasks) + 1` generates
colliding ids once a task is deleted, or that `secrets.choice` raises
`IndexError` when nothing is pending. Those need tests, review and type checking;
static analysis is the cheapest layer, not the only one.

### 4. How would you integrate these tools into a development workflow?

In three layers, each catching what escaped the one before:

1. **Editor.** Flake8 and Pylint running as the file is saved. The cheapest fix
   is the one made before the code is ever committed.
2. **Pre-commit hook.** Flake8 and Bandit on the staged files only, so the check
   stays fast enough that nobody is tempted to use `--no-verify`. Style errors
   never reach the shared history, which keeps diffs free of whitespace noise.
3. **CI on every push and pull request.** All three tools over the whole project,
   with the build failing on a Pylint score below an agreed threshold (9.5 here)
   and on any Bandit finding of Medium severity or higher. Running it in CI
   matters because that is the only layer a developer cannot skip.

Two details I would insist on. Configuration belongs in the repository, in
`.pylintrc` and `setup.cfg`, so every developer and CI get identical results —
otherwise the tools become a source of disagreement rather than a settled
baseline. And genuine exceptions should be suppressed narrowly and with a reason
(`# nosec B404: no untrusted input reaches this call`) rather than by lowering
the global threshold, because a disabled check is silent and a documented
suppression is auditable.

Adopting this on an existing codebase, I would not try to reach a clean report in
one commit. I would fail the build only on *new* findings first, then pay down
the backlog by severity — exactly the order used here: the High injection
finding, then the Medium deserialization one, then correctness warnings, then
style.
