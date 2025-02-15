from facalc.factories import new_factory, OutputPoint
from facalc.factorio_machines import (Module, get_crude_oil_rate, ChemicalPlant,
                                      CHEMICAL_PLANT_RECIPES, OilRefinery, OIL_REFINERY_RECIPES)
from math import ceil

def main():
    # parameters
    crude_oil_rates = [
        13.6, 36.0, 42.4, 29.7, 32.3, 18.5, 10.4, 41.3, 20.4, 40.8, 12.9, 35.5, 10.0
        # 7, 19, 23, 16, 17, 10, 5, 22, 11, 22, 7, 19, 5
    ]
    pumpjack_bonus = .3
    chemical_plant_modules = (Module.PRODUCTION_MODULE_1,)*3
    pumpjack_modules = (Module.SPEED_MODULE_1,)*2
    oil_refinery_modules = (Module.PRODUCTION_MODULE_1,)*3

    output_cap = 2*22.5

    factory = new_factory()

    # create sources
    oil_rate = get_crude_oil_rate(crude_oil_rates, pumpjack_bonus, pumpjack_modules)
    oil_source = factory.add_source("crude_oil", oil_rate)
    water_source = factory.add_source("water")

    # create lines
    output_line = factory.add_buffer("fuel output", {"solid_fuel": output_cap})
    oils_line = factory.add_buffer("oils line")

    refineries = factory.add_machine_group(OilRefinery(
        OIL_REFINERY_RECIPES["advanced_oil_processing"], oil_refinery_modules
    ))
    factory.connect(water_source, refineries)
    factory.connect(oil_source, refineries)
    factory.connect(refineries, oils_line, "light_oil", "petroleum_gas")

    heavy_oil_crackers = factory.add_machine_group(ChemicalPlant(
        CHEMICAL_PLANT_RECIPES["heavy_oil_cracking"], chemical_plant_modules
    ))
    factory.connect(water_source, heavy_oil_crackers)
    factory.connect(refineries, heavy_oil_crackers, "heavy_oil")
    factory.connect(heavy_oil_crackers, oils_line, "light_oil")

    # add solid fuel chemical plants
    light_oil_solid_fuel_plants = factory.add_machine_group(ChemicalPlant(
        CHEMICAL_PLANT_RECIPES["solid_fuel_from_light_oil"], chemical_plant_modules
    ))
    factory.connect(oils_line, light_oil_solid_fuel_plants, "light_oil")
    factory.connect(light_oil_solid_fuel_plants, output_line)
    petroleum_solid_fuel_plants = factory.add_machine_group(ChemicalPlant(
        CHEMICAL_PLANT_RECIPES["solid_fuel_from_petroleum_gas"], chemical_plant_modules
    ))
    factory.connect(oils_line, petroleum_solid_fuel_plants, "petroleum_gas")
    factory.connect(petroleum_solid_fuel_plants, output_line)

    factory.add_output_point(OutputPoint(output_line, "solid_fuel"))

    result = factory.analyse().single_results[OutputPoint(output_line, "solid_fuel")]
    print(result.display(True, True, True, True))

    final_rate = result.result_rate
    print("")
    print(f"{ceil(final_rate/0.15)} boilers")
    print(f"{ceil(final_rate/0.15*2)} steam engines")
    print(f"water rate: {final_rate/0.15*1200/200:.2f} /s")
    print(f"final power: {final_rate/0.15*1.8:.2f} MW")


if __name__ == '__main__':
    main()