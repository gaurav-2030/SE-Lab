def parse_zone(text):
    name, area = text.split(':')
    return name.strip().title(), float(area)

def moisture_average(readings_csv):
    values = [int(r) for r in readings_csv.split(',')]
    return sum(values) // len(values)

def water_needed(text):
    plot, rain = text.split('|')
    need = float(plot) * 5 - float(rain)
    return max(need, 0)

def main():
    print("==== Running parse_zone ====")
    user_input = input("Enter zone:area in m2 (e.g. north:120): ")
    result = parse_zone(user_input)
    print("Zone and Area:", result)

    print("\n==== Running moisture_average ====")
    user_input = input("Enter moisture readings as CSV (e.g. 40,35,50): ")
    result = moisture_average(user_input)
    print("Average Moisture:", result)

    print("\n==== Running water_needed ====")
    user_input = input("Enter area|rainfall (e.g. 120|8): ")
    result = water_needed(user_input)
    print("Water Needed:", result)

if __name__ == "__main__":
    main()
