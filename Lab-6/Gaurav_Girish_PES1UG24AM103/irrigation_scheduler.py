def should_irrigate(moisture, rain_mm, stage):
    if moisture >= 60:
        return False
    if rain_mm >= 10:
        return False
    if stage == "seedling":
        if moisture < 45:
            return True
        return False
    if stage == "flowering":
        return moisture < 55
    if rain_mm >= 5:
        return False
    return moisture < 40


def water_volume(area_m2, stage, temp_c):
    if area_m2 <= 0:
        raise ValueError("invalid area")
    if stage == "seedling":
        litres = 2
    elif stage == "flowering":
        litres = 5
    else:
        litres = 4
    if temp_c > 35:
        litres = litres * 1.5
    elif temp_c < 10:
        litres = litres * 0.5
    return area_m2 * litres


def schedule(zones, budget):
    plan = []
    for name, area, moisture, rain, stage, temp in zones:
        if not should_irrigate(moisture, rain, stage):
            continue
        need = water_volume(area, stage, temp)
        if need > budget:
            break
        budget -= need
        plan.append(name)
    return plan
