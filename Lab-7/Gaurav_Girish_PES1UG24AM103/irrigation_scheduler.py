# =============================================================================
#  Lab 7 - Fuzzing for Input Validation Bugs
#  Name  : Gaurav Girish
#  SRN   : PES1UG24AM103
#  Repo  : L6_L7_37_irrigation_scheduler
#  File  : irrigation_scheduler.py   (hardened - Step 5)
# =============================================================================
"""Irrigation scheduler: parse field zones, average soil moisture, estimate water.

WHAT CHANGED AND WHY
--------------------
The original version trusted its input completely. It called ``str.split`` on
whatever it was handed, unpacked the result into a fixed number of names, and
fed the pieces straight to ``float()`` and ``int()``. Fuzzing the three
functions with Hypothesis exposed two separate families of defect:

1. CRASHES - an unhandled exception escapes to the caller
     ``AttributeError``     ``parse_zone(None)``          - None has no .split
     ``TypeError``          ``parse_zone(b'')``           - bytes vs str
     ``ValueError``         ``parse_zone('')``            - not enough values
     ``ValueError``         ``parse_zone('north:abc')``   - bad float literal
     ``ValueError``         ``parse_zone('a:1:2')``       - too many values
     ``ValueError``         ``moisture_average('1,,3')``  - bad int literal
     ``ValueError``         ``moisture_average('')``      - bad int literal

   The ``// len(values)`` in ``moisture_average`` looks like a
   ``ZeroDivisionError`` waiting to happen, and fuzzing settled the question:
   it is unreachable, because ``str.split`` always returns at least one field.
   The division is safe only by accident, so the hardened version checks the
   list is non-empty anyway rather than relying on that accident.

2. SILENT ACCEPTANCE OF NONSENSE - no crash, but the answer is meaningless
     ``parse_zone('north:-120')``   -> an area of minus 120 square metres
     ``parse_zone('north:nan')``    -> float() accepts 'nan'
     ``parse_zone('north:1e400')``  -> overflows to an infinite area
     ``parse_zone('north:\u0664\u0663')``  -> non-ASCII digits accepted quietly
     ``moisture_average('-5')``     -> soil moisture of minus five percent
     ``moisture_average('101')``    -> moisture above 100 percent
     ``water_needed('nan|8')``      -> NaN slips through ``max(need, 0)``
     a 100 000-element reading list -> unbounded work for one line of input

THE CONTRACT NOW GUARANTEED
---------------------------
Every public function either returns a result that satisfies its documented
post-conditions, or raises ``InvalidInputError`` with a message a user can act
on. No other exception can escape. Validation is done up front (fail fast),
the accepted domain is stated explicitly, and the arithmetic for valid input is
byte-for-byte the behaviour of the original code.

ACCEPTED DOMAIN
---------------
  zone name         letters / digits / space / '-' / '_', must start with a
                    letter, 1..50 characters, surrounding spaces ignored
  area              plain decimal metres squared, 0 < area <= 1 000 000
  moisture reading  whole percentage, 0 <= reading <= 100, at most 100 readings
  rainfall          plain decimal millimetres, 0 <= rainfall <= 1000
  any raw input     a str of at most 500 characters

Exponent forms ('1e400'), the special literals 'nan' / 'inf', thousands
underscores ('1_000') and non-ASCII digit characters are deliberately refused:
``float()`` and ``int()`` all accept them, and every one of them was a bug.
"""

import math
import re

# --- limits of the accepted domain ------------------------------------------
MAX_INPUT_LEN = 500          # characters of raw input
MAX_NAME_LEN = 50            # characters of a zone name
MAX_AREA_M2 = 1_000_000.0    # one square kilometre
MAX_RAINFALL_MM = 1_000.0
MIN_MOISTURE = 0             # percent
MAX_MOISTURE = 100           # percent
MAX_READINGS = 100           # readings in one CSV line
LITRES_PER_M2 = 5            # water requirement factor (unchanged)

# --- strict ASCII-only literal patterns -------------------------------------
# These are deliberately stricter than float() and int(). Both built-ins accept
# 'nan', 'inf', '1e400', '1_000' and non-ASCII digits such as '\u0664\u0663',
# and every one of those was a bug found by fuzzing.
_DECIMAL_RE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)")
_INTEGER_RE = re.compile(r"[+-]?[0-9]+")
_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9 _-]*")


class InvalidInputError(ValueError):
    """Raised when input fails validation.

    This is the only exception the public functions of this module raise, which
    is what lets a caller - or a fuzz test - tell a deliberate rejection apart
    from a crash. It subclasses ``ValueError`` so existing ``except ValueError``
    handlers keep working.
    """


# -----------------------------------------------------------------------------
# Internal validation helpers
# -----------------------------------------------------------------------------
def _require_text(value, field):
    """Return ``value`` if it is a string of a sane length, else reject it."""
    if not isinstance(value, str):
        raise InvalidInputError(
            f"{field} must be given as text, got {type(value).__name__}"
        )
    if len(value) > MAX_INPUT_LEN:
        raise InvalidInputError(
            f"{field} is too long ({len(value)} characters, limit {MAX_INPUT_LEN})"
        )
    return value


def _split_once(text, separator, field, example):
    """Split ``text`` on ``separator``, insisting on exactly one separator."""
    parts = text.split(separator)
    if len(parts) != 2:
        found = len(parts) - 1
        raise InvalidInputError(
            f"{field} must contain exactly one '{separator}' separator "
            f"(found {found}); expected something like {example!r}"
        )
    return parts[0], parts[1]


def _to_decimal(raw, field, maximum, allow_zero):
    """Parse ``raw`` as a bounded, finite decimal number."""
    token = raw.strip()
    if not token:
        raise InvalidInputError(f"{field} is missing")
    if not _DECIMAL_RE.fullmatch(token):
        raise InvalidInputError(
            f"{field} must be a plain decimal number such as '120' or '12.5', "
            f"got {raw!r}"
        )
    value = float(token)
    if not math.isfinite(value):
        raise InvalidInputError(f"{field} must be a finite number, got {raw!r}")
    lower_ok = value >= 0 if allow_zero else value > 0
    if not lower_ok:
        wording = "zero or greater" if allow_zero else "greater than zero"
        raise InvalidInputError(f"{field} must be {wording}, got {value:g}")
    if value > maximum:
        raise InvalidInputError(f"{field} must not exceed {maximum:g}, got {value:g}")
    return value


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
def parse_zone(text):
    """Parse ``'<name>:<area>'`` into a ``(title-cased name, area)`` pair.

    >>> parse_zone("north:120")
    ('North', 120.0)
    >>> parse_zone("  south field : 240.5 ")
    ('South Field', 240.5)

    Returns a 2-tuple of a non-empty ``str`` and a finite ``float`` greater
    than zero. Raises ``InvalidInputError`` for anything else.
    """
    text = _require_text(text, "zone")
    name_part, area_part = _split_once(text, ":", "zone", "north:120")

    name = name_part.strip()
    if not name:
        raise InvalidInputError("zone name is missing; expected e.g. 'north:120'")
    if len(name) > MAX_NAME_LEN:
        raise InvalidInputError(
            f"zone name is too long ({len(name)} characters, limit {MAX_NAME_LEN})"
        )
    if not _NAME_RE.fullmatch(name):
        raise InvalidInputError(
            "zone name must start with a letter and may only contain letters, "
            f"digits, spaces, '-' and '_', got {name_part!r}"
        )

    area = _to_decimal(area_part, "zone area in m2", MAX_AREA_M2, allow_zero=False)
    return name.title(), area


def moisture_average(readings_csv):
    """Average a comma-separated list of soil-moisture percentages.

    >>> moisture_average("40,35,50")
    41
    >>> moisture_average(" 40 , 35 ")
    37

    Returns an ``int`` between 0 and 100 (floor division, as before). Raises
    ``InvalidInputError`` if the list is empty, over-long, or holds anything
    that is not a whole percentage in range.
    """
    readings_csv = _require_text(readings_csv, "moisture readings")

    fields = readings_csv.split(",")
    if len(fields) > MAX_READINGS:
        raise InvalidInputError(
            f"too many readings ({len(fields)}, limit {MAX_READINGS})"
        )

    values = []
    for position, field in enumerate(fields, start=1):
        token = field.strip()
        if not token:
            raise InvalidInputError(
                f"reading #{position} is empty; expected e.g. '40,35,50'"
            )
        if not _INTEGER_RE.fullmatch(token):
            raise InvalidInputError(
                f"reading #{position} must be a whole number, got {field!r}"
            )
        value = int(token)
        if not MIN_MOISTURE <= value <= MAX_MOISTURE:
            raise InvalidInputError(
                f"reading #{position} must be a percentage between "
                f"{MIN_MOISTURE} and {MAX_MOISTURE}, got {value}"
            )
        values.append(value)

    if not values:  # defensive: unreachable, str.split always yields one field
        raise InvalidInputError("at least one moisture reading is required")

    return sum(values) // len(values)


def water_needed(text):
    """Estimate water required from ``'<area>|<rainfall>'``.

    >>> water_needed("120|8")
    592.0
    >>> water_needed("10|500")
    0.0

    Returns a finite ``float`` of zero or more - the original returned a bare
    ``int`` 0 in the "no water needed" case, so the return type is now
    consistent. Raises ``InvalidInputError`` for anything outside the domain.
    """
    text = _require_text(text, "area|rainfall")
    area_part, rain_part = _split_once(text, "|", "area|rainfall", "120|8")

    area = _to_decimal(area_part, "plot area in m2", MAX_AREA_M2, allow_zero=False)
    rainfall = _to_decimal(
        rain_part, "rainfall in mm", MAX_RAINFALL_MM, allow_zero=True
    )

    need = area * LITRES_PER_M2 - rainfall
    return float(max(need, 0.0))


# -----------------------------------------------------------------------------
# Command-line front end
# -----------------------------------------------------------------------------
MAX_ATTEMPTS = 3


def ask(prompt, parser):
    """Prompt until ``parser`` accepts the answer, then return its result.

    Gives up after ``MAX_ATTEMPTS`` tries and returns ``None``. A closed input
    stream (Ctrl-D) or Ctrl-C ends the step cleanly instead of dumping a
    traceback - the whole point of the hardening.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n  -- input stopped, skipping this step --")
            return None
        try:
            return parser(raw)
        except InvalidInputError as exc:
            print(f"  !! Invalid input: {exc}")
            if attempt < MAX_ATTEMPTS:
                print(
                    f"     Attempt {attempt} of {MAX_ATTEMPTS} rejected, "
                    "please try again."
                )
    print(f"  !! {MAX_ATTEMPTS} invalid attempts, skipping this step.")
    return None


def main():
    print("==== Running parse_zone ====")
    result = ask("Enter zone:area in m2 (e.g. north:120): ", parse_zone)
    if result is not None:
        print("Zone and Area:", result)

    print("\n==== Running moisture_average ====")
    result = ask("Enter moisture readings as CSV (e.g. 40,35,50): ", moisture_average)
    if result is not None:
        print("Average Moisture:", result)

    print("\n==== Running water_needed ====")
    result = ask("Enter area|rainfall (e.g. 120|8): ", water_needed)
    if result is not None:
        print("Water Needed:", result)


if __name__ == "__main__":
    main()
