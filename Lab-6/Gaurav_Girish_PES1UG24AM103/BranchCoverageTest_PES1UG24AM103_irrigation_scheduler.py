"""
Lab 6 - Branch (Decision) Coverage Test Suite
Name : Gaurav Girish
SRN  : PES1UG24AM103
Repo : L6_L7_37_irrigation_scheduler

Goal of this file: force every decision in irrigation_scheduler.py to evaluate
BOTH True and False, including the loop-exit path that line coverage never
requires. Boundary values (60, 10, 45, 55, 5, 40, 35, 10 degC, area 0) are
tested explicitly because every decision in the module is a threshold test.

Commands used:
    coverage run --branch --source=irrigation_scheduler -m pytest BranchCoverageTest_PES1UG24AM103_irrigation_scheduler.py
    coverage report -m
"""

import pytest

from irrigation_scheduler import should_irrigate, water_volume, schedule


# ===========================================================================
# should_irrigate() - 6 decisions, both outcomes of each
# ===========================================================================

# --- Decision 1: if moisture >= 60 ---------------------------------------

def test_moisture_above_threshold_is_false():
    """moisture >= 60 -> True outcome of decision 1."""
    assert should_irrigate(70, 0, "seedling") is False


def test_moisture_exactly_60_is_false():
    """Boundary: 60 >= 60 is still the True outcome."""
    assert should_irrigate(60, 0, "flowering") is False


def test_moisture_just_below_60_continues():
    """moisture < 60 -> False outcome of decision 1, execution continues."""
    assert should_irrigate(59, 0, "flowering") is False  # falls through to 59 < 55


# --- Decision 2: if rain_mm >= 10 ----------------------------------------

def test_heavy_rain_is_false():
    """rain_mm >= 10 -> True outcome of decision 2."""
    assert should_irrigate(50, 12, "seedling") is False


def test_rain_exactly_10_is_false():
    """Boundary: 10 >= 10 is still the True outcome."""
    assert should_irrigate(30, 10, "seedling") is False


def test_rain_just_below_10_continues():
    """rain_mm < 10 -> False outcome of decision 2, execution continues."""
    assert should_irrigate(30, 9, "seedling") is True


# --- Decision 3: if stage == "seedling"  and  Decision 4: if moisture < 45 -

def test_seedling_dry_is_true():
    """Decision 3 True, decision 4 True."""
    assert should_irrigate(40, 0, "seedling") is True


def test_seedling_moist_is_false():
    """Decision 3 True, decision 4 False."""
    assert should_irrigate(50, 0, "seedling") is False


def test_seedling_moisture_exactly_45_is_false():
    """Boundary: 45 < 45 is False, so no irrigation."""
    assert should_irrigate(45, 0, "seedling") is False


def test_non_seedling_stage_falls_through():
    """Decision 3 False -> execution reaches the flowering check."""
    assert should_irrigate(50, 0, "flowering") is True


# --- Decision 5: if stage == "flowering" ---------------------------------

def test_flowering_dry_is_true():
    """Decision 5 True, inner comparison True."""
    assert should_irrigate(50, 0, "flowering") is True


def test_flowering_moist_is_false():
    """Decision 5 True, inner comparison False."""
    assert should_irrigate(58, 0, "flowering") is False


def test_flowering_moisture_exactly_55_is_false():
    """Boundary: 55 < 55 is False."""
    assert should_irrigate(55, 0, "flowering") is False


def test_other_stage_falls_through_to_rain_check():
    """Decision 5 False -> execution reaches the rain_mm >= 5 check."""
    assert should_irrigate(30, 0, "vegetative") is True


# --- Decision 6: if rain_mm >= 5  and final 'return moisture < 40' -------

def test_light_rain_blocks_irrigation():
    """Decision 6 True outcome."""
    assert should_irrigate(30, 6, "vegetative") is False


def test_rain_exactly_5_blocks_irrigation():
    """Boundary: 5 >= 5 is still the True outcome."""
    assert should_irrigate(30, 5, "vegetative") is False


def test_default_stage_dry_soil_is_true():
    """Decision 6 False outcome, final comparison True."""
    assert should_irrigate(39, 4, "vegetative") is True


def test_default_stage_moist_soil_is_false():
    """Decision 6 False outcome, final comparison False."""
    assert should_irrigate(50, 0, "vegetative") is False


def test_default_stage_moisture_exactly_40_is_false():
    """Boundary: 40 < 40 is False."""
    assert should_irrigate(40, 0, "vegetative") is False


# ===========================================================================
# water_volume() - 4 decisions, both outcomes of each
# ===========================================================================

# --- Decision 1: if area_m2 <= 0 -----------------------------------------

def test_zero_area_raises():
    """Boundary: 0 <= 0 -> True outcome, ValueError raised."""
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(0, "seedling", 20)


def test_negative_area_raises():
    """area_m2 < 0 -> True outcome."""
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(-5, "flowering", 20)


def test_positive_area_does_not_raise():
    """area_m2 > 0 -> False outcome, execution continues."""
    assert water_volume(1, "seedling", 20) == 2


# --- Decisions 2 and 3: the stage if / elif / else chain -----------------

def test_seedling_rate():
    """stage == 'seedling' -> litres = 2."""
    assert water_volume(10, "seedling", 20) == 20


def test_flowering_rate():
    """stage != 'seedling' but == 'flowering' -> litres = 5."""
    assert water_volume(10, "flowering", 20) == 50


def test_default_rate():
    """Neither stage matches -> else branch, litres = 4."""
    assert water_volume(10, "vegetative", 20) == 40


# --- Decisions 4 and 5: the temperature if / elif / else chain -----------

def test_hot_weather_scales_up():
    """temp_c > 35 -> litres * 1.5."""
    assert water_volume(10, "vegetative", 40) == pytest.approx(60.0)


def test_temp_exactly_35_is_not_hot():
    """Boundary: 35 > 35 is False, so no scaling up."""
    assert water_volume(10, "vegetative", 35) == 40


def test_cold_weather_scales_down():
    """temp_c < 10 -> litres * 0.5."""
    assert water_volume(10, "vegetative", 5) == pytest.approx(20.0)


def test_temp_exactly_10_is_not_cold():
    """Boundary: 10 < 10 is False, so no scaling down."""
    assert water_volume(10, "vegetative", 10) == 40


def test_mild_weather_is_unscaled():
    """Both temperature decisions False -> litres unchanged."""
    assert water_volume(10, "flowering", 25) == 50


def test_hot_weather_with_seedling_rate():
    """Scaling applied on top of the seedling rate."""
    assert water_volume(10, "seedling", 36) == pytest.approx(30.0)


def test_cold_weather_with_flowering_rate():
    """Scaling applied on top of the flowering rate."""
    assert water_volume(10, "flowering", 9) == pytest.approx(25.0)


# ===========================================================================
# schedule() - the loop plus 2 decisions, both outcomes of each,
#              INCLUDING the loop-exit path that line coverage misses
# ===========================================================================

def test_schedule_empty_zone_list():
    """Loop body never entered -> the for-statement's exit branch."""
    assert schedule([], 100) == []


def test_schedule_runs_to_completion():
    """Loop runs out of zones instead of breaking -> for -> 'return plan' arc.

    This is the branch that a line-coverage-only suite never exercises,
    because every statement in schedule() can be reached without it.
    """
    zones = [("north", 5, 30, 0, "seedling", 20)]  # needs 10 L of 1000 L
    assert schedule(zones, 1000) == ["north"]


def test_schedule_skips_zone_that_needs_no_water():
    """'if not should_irrigate(...)' True outcome -> continue."""
    zones = [
        ("wet", 10, 80, 0, "vegetative", 20),   # moisture 80 -> skipped
        ("dry", 10, 30, 0, "seedling", 20),     # needs 20 L -> watered
    ]
    assert schedule(zones, 100) == ["dry"]


def test_schedule_waters_zone_that_needs_water():
    """'if not should_irrigate(...)' False outcome -> zone is processed."""
    zones = [("east", 10, 30, 0, "flowering", 20)]  # needs 50 L
    assert schedule(zones, 50) == ["east"]


def test_schedule_breaks_when_zone_exceeds_budget():
    """'if need > budget' True outcome -> break."""
    zones = [("huge", 100, 30, 0, "flowering", 20)]  # needs 500 L of 50 L
    assert schedule(zones, 50) == []


def test_schedule_need_exactly_equals_budget():
    """Boundary: need > budget is False when they are equal -> zone watered."""
    zones = [("exact", 10, 30, 0, "seedling", 20)]  # needs exactly 20 L
    assert schedule(zones, 20) == ["exact"]


def test_schedule_stops_at_first_unaffordable_zone():
    """'if need > budget' False then True -> budget is consumed, then break."""
    zones = [
        ("a", 10, 30, 0, "seedling", 20),    # needs 20 L, budget 45 -> 25 left
        ("b", 10, 30, 0, "flowering", 20),   # needs 50 L > 25 -> break
        ("c", 10, 30, 0, "seedling", 20),    # never reached
    ]
    assert schedule(zones, 45) == ["a"]
