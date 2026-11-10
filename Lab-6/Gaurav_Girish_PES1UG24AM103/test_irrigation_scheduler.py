"""
Lab 6 - Irrigation Scheduler test file
Name : Gaurav Girish
SRN  : PES1UG24AM103

Stage 1: test cases added to reach 100% CODE (line) coverage.
Stage 2: further test cases added to reach 100% BRANCH coverage.
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


# --- Added for branch (decision) coverage ----------------------------------

def test_moisture_exactly_60_is_false():
    assert should_irrigate(60, 0, "flowering") is False


def test_moisture_just_below_60_continues():
    assert should_irrigate(59, 0, "flowering") is False


def test_rain_exactly_10_is_false():
    assert should_irrigate(30, 10, "seedling") is False


def test_rain_just_below_10_continues():
    assert should_irrigate(30, 9, "seedling") is True


def test_seedling_moisture_exactly_45_is_false():
    assert should_irrigate(45, 0, "seedling") is False


def test_flowering_moist_is_false():
    assert should_irrigate(58, 0, "flowering") is False


def test_flowering_moisture_exactly_55_is_false():
    assert should_irrigate(55, 0, "flowering") is False


def test_rain_exactly_5_blocks_irrigation():
    assert should_irrigate(30, 5, "vegetative") is False


def test_default_stage_moist_soil_is_false():
    assert should_irrigate(50, 0, "vegetative") is False


def test_default_stage_moisture_exactly_40_is_false():
    assert should_irrigate(40, 0, "vegetative") is False


def test_negative_area_raises():
    with pytest.raises(ValueError, match="invalid area"):
        water_volume(-5, "flowering", 20)


def test_positive_area_does_not_raise():
    assert water_volume(1, "seedling", 20) == 2


def test_temp_exactly_35_is_not_hot():
    assert water_volume(10, "vegetative", 35) == 40


def test_temp_exactly_10_is_not_cold():
    assert water_volume(10, "vegetative", 10) == 40


def test_mild_weather_is_unscaled():
    assert water_volume(10, "flowering", 25) == 50


def test_hot_weather_with_seedling_rate():
    assert water_volume(10, "seedling", 36) == pytest.approx(30.0)


def test_cold_weather_with_flowering_rate():
    assert water_volume(10, "flowering", 9) == pytest.approx(25.0)


def test_schedule_empty_zone_list():
    """Loop body never entered -> the for-statement's exit branch."""
    assert schedule([], 100) == []


def test_schedule_runs_to_completion():
    """Loop runs out of zones instead of breaking -> the 35->43 arc."""
    zones = [("north", 5, 30, 0, "seedling", 20)]
    assert schedule(zones, 1000) == ["north"]


def test_schedule_waters_zone_that_needs_water():
    zones = [("east", 10, 30, 0, "flowering", 20)]
    assert schedule(zones, 50) == ["east"]


def test_schedule_need_exactly_equals_budget():
    zones = [("exact", 10, 30, 0, "seedling", 20)]
    assert schedule(zones, 20) == ["exact"]


def test_schedule_stops_at_first_unaffordable_zone():
    zones = [
        ("a", 10, 30, 0, "seedling", 20),
        ("b", 10, 30, 0, "flowering", 20),
        ("c", 10, 30, 0, "seedling", 20),
    ]
    assert schedule(zones, 45) == ["a"]
