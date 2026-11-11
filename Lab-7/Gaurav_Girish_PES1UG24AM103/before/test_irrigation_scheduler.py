# =============================================================================
#  Lab 7 - Fuzzing for Input Validation Bugs
#  Name  : Gaurav Girish
#  SRN   : PES1UG24AM103
#  Repo  : L6_L7_37_irrigation_scheduler
#  File  : test_irrigation_scheduler.py   (completed - Step 3)
# =============================================================================
"""Property-based (fuzz) test suite for ``irrigation_scheduler`` using Hypothesis.

THE CONTRACT BEING TESTED
-------------------------
For *every* input Hypothesis is able to invent, each public function must do
exactly one of two things:

  (a) ACCEPT  the input and return a result that satisfies the function's
              documented post-conditions, or
  (b) REJECT  the input by raising ``InvalidInputError`` - the single,
              documented validation error of the module.

Anything else is an uncontrolled crash and therefore a bug: a ``ValueError``
escaping from ``float()`` or ``int()``, an ``AttributeError`` from ``None``, a
``TypeError`` from ``bytes``, an ``IndexError``, an ``OverflowError`` - these
are the failures a fuzzer is built to find.

Silently accepting nonsense is treated as a bug too. A soil-moisture reading
of ``-999``, a field area of ``-120 m2`` or an area of ``inf`` must not sail
through unnoticed, so the post-condition checks below assert domain ranges as
well as types.

DOCUMENTED DOMAIN (quantities this module is about)
---------------------------------------------------
  * zone name        - letters / digits / space / '-' / '_', starts with a
                       letter, 1..50 characters
  * area             - a finite number of square metres, 0 < area <= 1e6
  * moisture reading - a whole percentage, 0 <= reading <= 100
  * rainfall         - finite millimetres, 0 <= rainfall <= 1000

HOW THIS FILE BEHAVES BEFORE AND AFTER THE FIX
----------------------------------------------
``InvalidInputError`` does not exist in the original buggy module, so the
import below falls back to a local placeholder class. With the placeholder in
place *nothing* counts as a deliberate rejection, which is precisely correct
for the buggy version: every malformed input shows up as a crash and the suite
fails. After Step 5 the real class is imported from the module and the same
unchanged suite passes.

Run with:  pytest test_irrigation_scheduler.py
"""

import math

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from irrigation_scheduler import moisture_average, parse_zone, water_needed

try:  # the hardened module exports its own validation error ...
    from irrigation_scheduler import InvalidInputError
except ImportError:  # ... the original buggy module does not.

    class InvalidInputError(ValueError):
        """Placeholder used while testing the un-fixed module.

        Nothing in the buggy code raises this, so every rejected input is
        correctly reported as an uncontrolled crash.
        """


# -----------------------------------------------------------------------------
# Hypothesis configuration
# -----------------------------------------------------------------------------
# deadline=None: a slow example is not the kind of bug this lab is hunting,
# and a DeadlineExceeded would be misreported as a crash by the helper below.
settings.register_profile(
    "lab7",
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
settings.load_profile("lab7")


# -----------------------------------------------------------------------------
# Fuzzing strategies
# -----------------------------------------------------------------------------
# 1. Unstructured fuzz - "throw literally anything at it", including the wrong
#    type altogether. This is the st.text() | st.none() idea from the handout,
#    widened so that type confusion is covered as well.
WILD = (
    st.text()
    | st.none()
    | st.integers()
    | st.floats()
    | st.booleans()
    | st.binary()
    | st.lists(st.integers())
    | st.dictionaries(st.text(), st.integers())
)

# 2. Structure-aware fuzz. Purely random text almost never contains a ':' or a
#    '|', so unstructured fuzzing alone keeps tripping over the very first
#    split() and never reaches the parsing code behind it. These pieces are
#    glued together with real separators so the fuzzer gets *past* the split
#    and can attack float()/int() and the arithmetic underneath.
PIECES = st.sampled_from(
    [
        "",            # empty field
        " ",           # whitespace-only field
        "north",       # a name where a number belongs
        "North West",  # name with a space
        "abc",
        "120",
        "0",           # zero area  -> a zone with no area
        "-5",          # negative   -> impossible area / moisture
        "12.5",        # float where an int belongs
        "101",         # moisture above 100%
        "nan",         # float() happily accepts these three ...
        "inf",
        "1e400",       # ... and this one silently becomes +inf
        "\u0664\u0663",  # Arabic-Indic digits: float()/int() accept them
        "\uff11\uff12",  # full-width digits: accepted too
        "+7",
        ".",
        "-",
        "1_000",       # underscore separator
        "99999999999999999999999999",
        " 120 ",
        "None",
    ]
)
STRUCTURED = st.builds(
    lambda parts, sep: sep.join(parts),
    st.lists(PIECES, min_size=1, max_size=3),
    st.sampled_from([":", "|", ",", ";", " ", ""]),
)

FUZZ = WILD | STRUCTURED

# 3. Well-formed inputs, generated from a regex, for the "it must still do the
#    right thing" properties.
VALID_NAME = st.from_regex(r"\A[A-Za-z][A-Za-z0-9 _-]{0,19}\Z", fullmatch=True)
VALID_AREA_STR = st.from_regex(r"\A0*[1-9][0-9]{0,5}(\.[0-9]{1,3})?\Z", fullmatch=True)
VALID_RAIN_STR = st.from_regex(r"\A(0|[1-9][0-9]{0,2})(\.[0-9]{1,2})?\Z", fullmatch=True)
PADDING = st.sampled_from(["", " ", "   ", "\t"])


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _short(value, limit=48):
    """``repr`` of ``value``, shortened so failure reports stay readable."""
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _call(func, raw):
    """Call ``func(raw)`` and classify what happened.

    Returns ``("ok", value)`` when the input was accepted and
    ``("rejected", exc)`` when it was deliberately refused.
    Raises ``AssertionError`` - i.e. fails the test - on any other exception,
    because that is an uncontrolled crash.
    """
    try:
        return "ok", func(raw)
    except InvalidInputError as exc:
        return "rejected", exc
    except Exception as exc:  # noqa: BLE001 - this broad catch *is* the detector
        raise AssertionError(
            "{}() crashed instead of rejecting its input\n"
            "  exception : {}: {}\n"
            "  input     : {}".format(
                func.__name__, type(exc).__name__, str(exc)[:60], _short(raw)
            )
        ) from None


def _fail(func_name, problem, raw, got):
    raise AssertionError(
        "{}() returned a result that breaks its contract\n"
        "  problem   : {}\n"
        "  returned  : {}\n"
        "  input     : {}".format(func_name, problem, _short(got), _short(raw))
    )


def _check_zone(raw, result):
    """Post-conditions for ``parse_zone``: (non-blank str, finite float > 0)."""
    if not (isinstance(result, tuple) and len(result) == 2):
        _fail("parse_zone", "not a (name, area) 2-tuple", raw, result)
    name, area = result
    if not isinstance(name, str) or not name.strip():
        _fail("parse_zone", "zone name is not a non-blank string", raw, result)
    if not isinstance(area, float):
        _fail("parse_zone", "area is not a float", raw, result)
    if not math.isfinite(area):
        _fail("parse_zone", "area is not a finite number", raw, result)
    if area <= 0:
        _fail("parse_zone", "area is not greater than zero", raw, result)


def _check_moisture(raw, average):
    """Post-conditions for ``moisture_average``: an int in 0..100."""
    if not isinstance(average, int) or isinstance(average, bool):
        _fail("moisture_average", "average is not an int", raw, average)
    if not 0 <= average <= 100:
        _fail("moisture_average", "average is outside 0-100 percent", raw, average)


def _check_water(raw, need):
    """Post-conditions for ``water_needed``: a finite float >= 0."""
    if not isinstance(need, float):
        _fail("water_needed", "water need is not a float", raw, need)
    if not math.isfinite(need):
        _fail("water_needed", "water need is not a finite number", raw, need)
    if need < 0:
        _fail("water_needed", "water need is negative", raw, need)


# =============================================================================
# 1. The three "no crash" properties asked for by the handout
# =============================================================================
@given(FUZZ)
def test_parse_zone_no_crash(s):
    """parse_zone must either parse the zone or reject it politely."""
    outcome, value = _call(parse_zone, s)
    if outcome == "ok":
        _check_zone(s, value)


@given(FUZZ)
def test_moisture_average_no_crash(s):
    """moisture_average must either average the readings or reject them."""
    outcome, value = _call(moisture_average, s)
    if outcome == "ok":
        _check_moisture(s, value)


@given(FUZZ)
def test_water_needed_no_crash(s):
    """water_needed must either compute a water volume or reject the input."""
    outcome, value = _call(water_needed, s)
    if outcome == "ok":
        _check_water(s, value)


# =============================================================================
# 2. Hardening must not change the behaviour of valid input
# =============================================================================
@given(VALID_NAME, VALID_AREA_STR)
def test_parse_zone_accepts_well_formed_input(name, area_str):
    zone, area = parse_zone(f"{name}:{area_str}")
    assert zone == name.strip().title()
    assert area == pytest.approx(float(area_str))


@given(VALID_NAME, VALID_AREA_STR, PADDING)
def test_parse_zone_tolerates_surrounding_whitespace(name, area_str, pad):
    expected = parse_zone(f"{name}:{area_str}")
    padded = f"{pad}{name}{pad}:{pad}{area_str}{pad}"
    assert parse_zone(padded) == expected


@given(st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=20))
def test_moisture_average_matches_reference(values):
    readings_csv = ",".join(str(v) for v in values)
    assert moisture_average(readings_csv) == sum(values) // len(values)


@given(st.integers(min_value=0, max_value=100), st.integers(min_value=1, max_value=12))
def test_moisture_average_of_repeated_reading_is_that_reading(value, count):
    assert moisture_average(",".join([str(value)] * count)) == value


@given(VALID_AREA_STR, VALID_RAIN_STR)
def test_water_needed_matches_reference(area_str, rain_str):
    expected = max(float(area_str) * 5 - float(rain_str), 0.0)
    assert water_needed(f"{area_str}|{rain_str}") == pytest.approx(expected)


@given(VALID_AREA_STR, VALID_RAIN_STR)
def test_water_needed_is_never_negative(area_str, rain_str):
    _check_water(f"{area_str}|{rain_str}", water_needed(f"{area_str}|{rain_str}"))


# =============================================================================
# 3. Regression tests - the concrete inputs the fuzzer shrank down to.
#    Every one of these must be a clean rejection, not a crash and not a
#    silently wrong answer.
# =============================================================================
PARSE_ZONE_BAD = [
    None,                       # TypeError: 'NoneType' has no attribute 'split'
    "",                         # ValueError: not enough values to unpack
    120,                        # wrong type entirely
    ["north", 120],             # wrong type entirely
    "north",                    # separator missing
    "north:",                   # area missing
    ":120",                     # name missing
    "  :  ",                    # both blank
    "north:abc",                # ValueError from float()
    "north:120:50",             # too many separators
    "north:nan",                # float() accepts 'nan' -> silent NaN area
    "north:inf",                # float() accepts 'inf' -> silent infinite area
    "north:1e400",              # overflows to +inf
    "north:-120",               # negative area accepted silently
    "north:0",                  # a zone with no area at all
    "north:\u0664\u0663",       # non-ASCII digits accepted silently
    "4\u0663:120",              # name that is not a name
]

MOISTURE_BAD = [
    None,
    "",                         # ValueError: invalid literal for int()
    40,
    [40, 35],
    "1,,3",                     # empty element
    "one,two",                  # ValueError from int()
    "40, ,50",                  # whitespace-only element
    ",",                        # two empty elements
    "40,35,",                   # trailing comma
    "40;35",                    # wrong separator
    "12.5",                     # float where an int is required
    "-5",                       # negative moisture accepted silently
    "101",                      # above 100% accepted silently
    "\u0664\u0663",             # non-ASCII digits accepted silently
    "99999999999999999999",     # absurd magnitude accepted silently
]

WATER_BAD = [
    None,
    "",
    120,
    ("120", "8"),
    "120",                      # separator missing
    "120|8|2",                  # too many separators
    "|",                        # both parts blank
    "120|",                     # rainfall missing
    "|8",                       # area missing
    "abc|8",                    # ValueError from float()
    "120|abc",
    "-120|8",                   # negative area accepted silently
    "120|-8",                   # negative rainfall accepted silently
    "0|8",                      # zero area
    "1e400|8",                  # +inf area -> inf litres of water
    "nan|8",                    # NaN propagates through max()
]


@pytest.mark.parametrize("bad", PARSE_ZONE_BAD, ids=repr)
def test_parse_zone_rejects_invalid_input(bad):
    with pytest.raises(InvalidInputError):
        parse_zone(bad)


@pytest.mark.parametrize("bad", MOISTURE_BAD, ids=repr)
def test_moisture_average_rejects_invalid_input(bad):
    with pytest.raises(InvalidInputError):
        moisture_average(bad)


@pytest.mark.parametrize("bad", WATER_BAD, ids=repr)
def test_water_needed_rejects_invalid_input(bad):
    with pytest.raises(InvalidInputError):
        water_needed(bad)


# =============================================================================
# 4. Robustness against oversized input (a cheap denial-of-service)
# =============================================================================
def test_oversized_reading_list_is_rejected():
    with pytest.raises(InvalidInputError):
        moisture_average(",".join(["50"] * 100_000))


def test_oversized_zone_string_is_rejected():
    with pytest.raises(InvalidInputError):
        parse_zone("n" * 100_000 + ":120")
