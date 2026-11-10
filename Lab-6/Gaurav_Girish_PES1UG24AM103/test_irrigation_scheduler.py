"""
Lab 6 - Irrigation Scheduler test file
Name : Gaurav Girish
SRN  : PES1UG24AM103

Stage 1: test cases added to reach 100% CODE (line) coverage.
"""

import pytest
from irrigation_scheduler import should_irrigate, water_volume, schedule

#Example test cases:
def test_wet_soil_no_irrigation():
    assert should_irrigate(70, 0, "seedling") is False

def test_seedling_volume():
    assert water_volume(10, "seedling", 20) == 20


# --- Added for code (line) coverage ----------------------------------------

def test_heavy_rain_no_irrigation():
    assert should_irrigate(50, 12, "seedling") is False


def test_seedling_dry_needs_water():
    assert should_irrigate(40, 0, "seedling") is True


def test_seedling_moist_enough():
    assert should_irrigate(50, 0, "seedling") is False


def test_flowering_stage_returns_comparison():
    assert should_irrigate(50, 0, "flowering") is True


def test_light_rain_blocks_other_stage():
    assert should_irrigate(50, 6, "vegetative") is False


def test_default_stage_dry_soil():
    assert should_irrigate(30, 0, "vegetative") is True


def test_invalid_area_raises():
    with pytest.raises(ValueError):
        water_volume(0, "seedling", 20)


def test_flowering_volume():
    assert water_volume(10, "flowering", 20) == 50


def test_default_stage_volume():
    assert water_volume(10, "vegetative", 20) == 40


def test_hot_weather_scales_up():
    assert water_volume(10, "vegetative", 40) == 60


def test_cold_weather_scales_down():
    assert water_volume(10, "vegetative", 5) == 20


def test_schedule_adds_zone_then_stops_on_budget():
    zones = [
        ("north", 10, 30, 0, "seedling", 20),
        ("south", 100, 30, 0, "flowering", 20),
    ]
    assert schedule(zones, 100) == ["north"]


def test_schedule_skips_wet_zone():
    zones = [
        ("wet", 10, 80, 0, "vegetative", 20),
        ("huge", 50, 20, 0, "vegetative", 20),
    ]
    assert schedule(zones, 50) == []
