"""Growprint: Python implementation of the assignment workbook.

Cell references below refer to the supplied workbook's Calculator tab.
All emissions, annual quantities, intensities and percentages are computed here.
"""

from decimal import Decimal, InvalidOperation

SOURCE_URL = "https://docs.google.com/spreadsheets/d/1tkGwkPDtqRkXlu5lfNHK5l_IliIhMGI2/edit"

# key, readable name, unit, spreadsheet value, source cell, maximum
INPUTS = [
    ("area", "Growing area", "sq ft", 10, "B5", 1000000000),
    ("cycles", "Crop cycles per year", "cycles/year", 10, "B6", 1000000000),
    ("yield_per_cycle", "Yield per cycle", "lb/cycle", 8, "B7", 1000000000),
    ("days", "Operating days per year", "days/year", 365, "B8", 366),
    ("lights_watts", "Grow lights power", "watts", 200, "B11", 1000000000),
    ("lights_hours", "Grow lights runtime", "hours/day", 14, "B12", 24),
    ("pump_watts", "Water pump power", "watts", 25, "B13", 1000000000),
    ("pump_hours", "Water pump runtime", "hours/day", 24, "B14", 24),
    ("air_watts", "Air pump / aeration power", "watts", 10, "B15", 1000000000),
    ("air_hours", "Air pump runtime", "hours/day", 24, "B16", 24),
    ("fans_watts", "Fans / circulation power", "watts", 20, "B17", 1000000000),
    ("fans_hours", "Fans runtime", "hours/day", 12, "B18", 24),
    ("other_watts", "Other electric load", "watts", 0, "B19", 1000000000),
    ("other_hours", "Other load runtime", "hours/day", 0, "B20", 24),
    ("hvac_kwh", "Allocated HVAC electricity", "kWh/year", 0, "B21", 1000000000),
    ("water", "Water used per cycle", "gallons/cycle", 20, "B24", 1000000000),
    ("nutrients", "Nutrients used per cycle", "kg/cycle", 0.35, "B25", 1000000000),
    ("media", "Growing media used per cycle", "kg/cycle", 0.25, "B26", 1000000000),
    ("packaging", "Packaging used per cycle", "kg/cycle", 0, "B27", 1000000000),
    ("miles", "Vehicle travel / delivery", "miles/year", 0, "B28", 1000000000),
    ("equipment_carbon", "Equipment embodied carbon", "kg CO₂e total", 0, "B29", 1000000000),
    ("equipment_life", "Equipment useful life", "years", 5, "B30", 1000000000),
]

# Defaults copied exactly from Emission Factors!B5:B10, not current local rates.
FACTORS = [
    ("factor_electricity", "Grid electricity", "kg CO₂e/kWh", 0.3497, "B5"),
    ("factor_water", "Tap water", "kg CO₂e/gallon", 0.0015, "B6"),
    ("factor_nutrients", "Hydroponic nutrients", "kg CO₂e/kg nutrient", 2.5, "B7"),
    ("factor_media", "Growing media", "kg CO₂e/kg media", 1, "B8"),
    ("factor_packaging", "Packaging", "kg CO₂e/kg packaging", 2, "B9"),
    ("factor_transport", "Vehicle travel", "kg CO₂e/mile", 0.4, "B10"),
]

SECTIONS = [
    {"id": "farm", "title": "Farm Information & Production", "short": "Your farm", "note": "Plan for one year. The reference is designed for farms of 2–20 sq ft.", "fields": INPUTS[:4]},
    {"id": "electricity", "title": "Electricity Consumption", "short": "Electricity", "note": "Use the total wattage for each group of devices. Runtime is the average per operating day.", "fields": INPUTS[4:15]},
    {"id": "water-use", "title": "Water Consumption", "short": "Water", "note": "Include fresh water added for the initial fill, top-ups and cleaning each cycle.", "fields": INPUTS[15:16]},
    {"id": "materials", "title": "Nutrients & Growing Media", "short": "Nutrients & media", "note": "Enter the mass used in one crop cycle, such as fertilizer and replacement coco or plugs.", "fields": INPUTS[16:18]},
    {"id": "transport", "title": "Packaging & Transportation", "short": "Packaging & travel", "note": "Packaging is per cycle. Travel is the annual distance attributable to this farm.", "fields": INPUTS[18:20]},
    {"id": "equipment", "title": "Equipment", "short": "Equipment", "note": "Embodied carbon is the emissions from making your equipment. Use supplier data when available.", "fields": INPUTS[20:22]},
]

EXAMPLE = {row[0]: row[3] for row in INPUTS + FACTORS}
EXAMPLE.update(farm_name="Spreadsheet example", crop="Leafy greens")

CATEGORIES = [
    ("electricity", "Electricity", "#1c5545"),
    ("water", "Water", "#3b83aa"),
    ("nutrients", "Nutrients", "#bd6b42"),
    ("media", "Growing media", "#8873a8"),
    ("packaging", "Packaging", "#d1a433"),
    ("transport", "Transportation", "#78a173"),
    ("equipment", "Equipment", "#cf7c91"),
]


class InputError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Please check the highlighted fields.")


def parse_inputs(data):
    """Blank activity = 0; blank factor = workbook default. Reject invalid data."""
    if not isinstance(data, dict):
        raise InputError({"form": "Send the form as a JSON object."})
    values, errors = {}, {}
    for row in INPUTS + FACTORS:
        key, label = row[:2]
        default = row[3] if key.startswith("factor_") else 0
        limit = row[5] if len(row) > 5 else 1000000000
        raw = data.get(key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            raw = default
        try:
            if isinstance(raw, (bool, list, dict)):
                raise InvalidOperation
            number = Decimal(str(raw).strip())
            if not number.is_finite() or number < 0 or number > limit:
                raise InvalidOperation
            values[key] = number
        except (InvalidOperation, ValueError, TypeError):
            errors[key] = f"{label}: enter a number from 0 to {limit:,}."
    for key, label in [("farm_name", "Farm name"), ("crop", "Crop")]:
        raw = data.get(key, "")
        if not isinstance(raw, str) or len(raw) > 100:
            errors[key] = f"{label}: use 100 characters or fewer."
    if errors:
        raise InputError(errors)
    return values


def calculate(data):
    v = parse_inputs(data)
    zero = Decimal(0)
    # Calculator!F5:F10: watts × hours/day × operating days ÷ 1,000.
    energy = {
        key: v[f"{key}_watts"] * v[f"{key}_hours"] * v["days"] / 1000
        for key in ("lights", "pump", "air", "fans", "other")
    }
    energy["hvac"] = v["hvac_kwh"]
    total_kwh = sum(energy.values(), zero)  # F11
    emissions = {
        "electricity": total_kwh * v["factor_electricity"],  # F12
        "water": v["water"] * v["cycles"] * v["factor_water"],  # F13
        "nutrients": v["nutrients"] * v["cycles"] * v["factor_nutrients"],  # F14
        "media": v["media"] * v["cycles"] * v["factor_media"],  # F15
        "packaging": v["packaging"] * v["cycles"] * v["factor_packaging"],  # F16
        "transport": v["miles"] * v["factor_transport"],  # F17
        "equipment": v["equipment_carbon"] / v["equipment_life"] if v["equipment_life"] > 0 else zero,  # F18
    }
    total = sum(emissions.values(), zero)  # F19
    production = v["yield_per_cycle"] * v["cycles"]  # F20

    def divide(denominator):
        # Preserve workbook IF guards. UI uses defined flags to show N/A.
        return float(total / denominator) if denominator > 0 else 0.0

    warnings = []
    if v["area"] == 0:
        warnings.append("Add a growing area to calculate emissions per square foot.")
    elif not 2 <= v["area"] <= 20:
        warnings.append("The reference is intended for 2–20 sq ft farms; this area is outside that range.")
    if v["cycles"] == 0:
        warnings.append("Add crop cycles to calculate emissions per cycle.")
    if production == 0:
        warnings.append("Annual production is zero. Emissions per pound are not available.")
    if v["equipment_carbon"] > 0 and v["equipment_life"] == 0:
        warnings.append("Equipment emissions are excluded because useful life is zero or blank, matching the spreadsheet. Add its useful life to include them.")

    categories = [
        {"key": key, "label": label, "color": color,
         "emissions": float(emissions[key]),
         "percentage": float(emissions[key] / total * 100) if total > 0 else 0.0}
        for key, label, color in CATEGORIES
    ]
    largest = max(categories, key=lambda row: row["emissions"]) if total > 0 else None
    return {
        "farm_name": data.get("farm_name", "").strip() or "Your farm",
        "crop": data.get("crop", "").strip(),
        "metrics": {"total_annual": float(total), "annual_production": float(production),
                    "per_cycle": divide(v["cycles"]), "per_sqft": divide(v["area"]),
                    "per_pound": divide(production), "electricity_kwh": float(total_kwh)},
        "defined": {"per_cycle": v["cycles"] > 0, "per_sqft": v["area"] > 0, "per_pound": production > 0},
        "categories": categories, "largest_source": largest,
        "electricity_breakdown_kwh": {key: float(value) for key, value in energy.items()},
        "factors_used": {row[0]: float(v[row[0]]) for row in FACTORS},
        "warnings": warnings,
    }
