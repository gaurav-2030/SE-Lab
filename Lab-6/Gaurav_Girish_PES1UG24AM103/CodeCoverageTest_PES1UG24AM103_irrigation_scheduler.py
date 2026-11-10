"""
Lab 6 - Code (Line) Coverage Test Suite
Name : Gaurav Girish
SRN  : PES1UG24AM103
Repo : L6_L7_37_irrigation_scheduler

Goal of this file: drive every executable statement in irrigation_scheduler.py
at least once, i.e. maximise LINE coverage.

Command used:
    coverage run --source=irrigation_scheduler -m pytest CodeCoverageTest_PES1UG24AM103_irrigation_scheduler.py
    coverage report -m
"""

import pytest

from irrigation_scheduler import should_irrigate, water_volume, schedule


# ---------------------------------------------------------------------------
# should_irrigate() - one test per statement/return in the function
# ---------------------------------------------------------------------------

def test_wet_soil_no_irrigation():
    """moisture >= 60 -> early exit (line: 'if moisture >= 60: return False')."""
    assert should_irrigate(70, 0, "seedling") is False


def test_heavy_rain_no_irrigation():
    """rain_mm >= 10 -> early exit (line: 'if rain_mm >= 10: return False')."""
    assert should_irrigate(50, 12, "seedling") is False


def test_seedling_dry_needs_water():
    """seedling branch, moisture < 45 -> 'return True'."""
    assert should_irrigate(40, 0, "seedling") is True


def test_seedling_moist_enough():
    """seedling branch, moisture >= 45 -> 'return False'."""
    assert should_irrigate(50, 0, "seedling") is False


def test_flowering_stage_returns_comparison():
    """flowering branch -> 'return moisture < 55'."""
    assert should_irrigate(50, 0, "flowering") is True


def test_light_rain_blocks_other_stage():
    """default stage, rain_mm >= 5 -> 'return False'."""
    assert should_irrigate(50, 6, "vegetative") is False


def test_default_stage_dry_soil():
    """default stage, no rain -> final 'return moisture < 40'."""
    assert should_irrigate(30, 0, "vegetative") is True


# ---------------------------------------------------------------------------
# water_volume() - one test per litres assignment and per temperature scaling
# ---------------------------------------------------------------------------

def test_invalid_area_raises():
    """area_m2 <= 0 -> 'raise ValueError' line."""
    with pytest.raises(ValueError):
        water_volume(0, "seedling", 20)


def test_seedling_volume():
    """'litres = 2' line."""
    assert water_volume(10, "seedling", 20) == 20


def test_flowering_volume():
    """'litres = 5' line."""
    assert water_volume(10, "flowering", 20) == 50


def test_default_stage_volume():
    """'litres = 4' (else) line."""
    assert water_volume(10, "vegetative", 20) == 40


def test_hot_weather_scales_up():
    """'litres = litres * 1.5' line (temp_c > 35)."""
    assert water_volume(10, "vegetative", 40) == 60


def test_cold_weather_scales_down():
    """'litres = litres * 0.5' line (temp_c < 10)."""
    assert water_volume(10, "vegetative", 5) == 20


# ---------------------------------------------------------------------------
# schedule() - cover the loop body, the 'continue', the 'break' and 'append'
# ---------------------------------------------------------------------------

def test_schedule_adds_zone_then_stops_on_budget():
    """Covers 'need = ...', 'budget -= need', 'plan.append(name)' and 'break'."""
    zones = [
        ("north", 10, 30, 0, "seedling", 20),    # needs 20 L, affordable
        ("south", 100, 30, 0, "flowering", 20),  # needs 500 L, over budget
    ]
    assert schedule(zones, 100) == ["north"]


def test_schedule_skips_wet_zone():
    """Covers the 'continue' line when should_irrigate() is False."""
    zones = [
        ("wet", 10, 80, 0, "vegetative", 20),    # skipped: moisture 80
        ("huge", 50, 20, 0, "vegetative", 20),   # needs 200 L, over budget
    ]
    assert schedule(zones, 50) == []
