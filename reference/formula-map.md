# Spreadsheet implementation map

Source: `hydroponic_carbon_footprint_calculator.xlsx`, downloaded from the assignment's [reference link](https://docs.google.com/spreadsheets/d/1tkGwkPDtqRkXlu5lfNHK5l_IliIhMGI2/edit). Tabs: `Calculator`, `Emission Factors`, `How to Use`. The source workbook is unchanged.

## Activity fields (Calculator tab)

| Source | Form/API field | Unit |
|---|---|---|
| B5 | area | sq ft |
| B6 | cycles | cycles/year |
| B7 | yield_per_cycle | lb/cycle |
| B8 | days | days/year |
| B11, B12 | lights_watts, lights_hours | watts; hours/day |
| B13, B14 | pump_watts, pump_hours | watts; hours/day |
| B15, B16 | air_watts, air_hours | watts; hours/day |
| B17, B18 | fans_watts, fans_hours | watts; hours/day |
| B19, B20 | other_watts, other_hours | watts; hours/day |
| B21 | hvac_kwh | kWh/year |
| B24 | water | gallons/cycle |
| B25 | nutrients | kg/cycle |
| B26 | media | kg/cycle |
| B27 | packaging | kg/cycle |
| B28 | miles | miles/year |
| B29 | equipment_carbon | kg CO₂e total |
| B30 | equipment_life | years |

Farm name and crop are optional descriptive fields; they do not alter the arithmetic.

## Formulas (Calculator tab)

| Cell | Spreadsheet formula | Implementation |
|---|---|---|
| F5 | `B11*B12*B8/1000` | Lights kWh/year |
| F6 | `B13*B14*B8/1000` | Water pump kWh/year |
| F7 | `B15*B16*B8/1000` | Air pump kWh/year |
| F8 | `B17*B18*B8/1000` | Fans kWh/year |
| F9 | `B19*B20*B8/1000` | Other load kWh/year |
| F10 | `B21` | Already annual HVAC kWh; not multiplied by cycles or days |
| F11 | `SUM(F5:F10)` | Total annual electricity |
| F12 | `F11*'Emission Factors'!B5` | Electricity emissions |
| F13 | `B24*B6*'Emission Factors'!B6` | Water emissions |
| F14 | `B25*B6*'Emission Factors'!B7` | Nutrient emissions |
| F15 | `B26*B6*'Emission Factors'!B8` | Growing media emissions |
| F16 | `B27*B6*'Emission Factors'!B9` | Packaging emissions |
| F17 | `B28*'Emission Factors'!B10` | Annual transport emissions; not multiplied by cycles |
| F18 | `IF(B30>0,B29/B30,0)` | Annualized equipment emissions |
| F19 | `SUM(F12:F18)` | Total annual footprint |
| F20 | `B7*B6` | Annual production in pounds |
| F21 | `IF(B6>0,F19/B6,0)` | Footprint per crop cycle |
| F22 | `IF(B5>0,F19/B5,0)` | Footprint per square foot per year |
| F23 | `IF(F20>0,F19/F20,0)` | Footprint per pound |

The seven chart values correspond to Calculator!I4:I10. Each percentage is calculated in Python as category emissions ÷ total emissions × 100, with zero returned when the total is zero.

## Emission Factors tab

| Cell | Factor | Default |
|---|---|---|
| B5 | Grid electricity, kg CO₂e/kWh | 0.3497 |
| B6 | Tap water, kg CO₂e/gallon | 0.0015 |
| B7 | Nutrients, kg CO₂e/kg nutrient | 2.5 |
| B8 | Growing media, kg CO₂e/kg media | 1 |
| B9 | Packaging, kg CO₂e/kg packaging | 2 |
| B10 | Vehicle travel, kg CO₂e/mile | 0.4 |

The workbook calls the water, nutrient, media, packaging and travel factors illustrative. Its electricity note identifies EPA eGRID 2023 U.S. total output rate, 770.884 lb CO₂e/MWh converted to kg/kWh. This implementation uses the stored factor **0.3497**, exactly as the workbook formula does.
