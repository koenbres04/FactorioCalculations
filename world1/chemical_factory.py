from facalc.factories import Factory, OutputPoint, Buffer, FullAnalysisResults, SingleAnalysisResults
from facalc.factorio_machines import (Module, ChemicalPlant, CHEMICAL_PLANT_RECIPES, OilRefinery, OIL_REFINERY_RECIPES,
                               get_crude_oil_rate)
from typing import Iterable


class ChemicalFactory:
    def __init__(
            self,
            factory: Factory, iron_plate_input: Buffer, copper_plate_input: Buffer,
            pumpjack_bonus: float,
            coal_rate: float | None = None,
            water_rate: float | None = None,
            crude_oil_rates: Iterable[float] | None = None,
            pumpjack_modules: tuple[Module, ...] = (),
            oil_refinery_modules: tuple[Module, ...] = (),
            chemical_plant_modules: tuple[Module, ...] = (),
            input_caps: dict[str, float] | None = None,
            output_caps: dict[str, float] | None = None
        ):
        # add sources
        coal_source = factory.add_source("coal", coal_rate)
        water_source = factory.add_source("water", water_rate)
        self.oil_rate = get_crude_oil_rate(crude_oil_rates, pumpjack_bonus, pumpjack_modules)
        oil_source = factory.add_source("crude_oil", self.oil_rate)

        # create the main, oils line and output line
        main_line = factory.add_buffer("chemical factory line", input_caps)
        factory.connect(coal_source, main_line)
        factory.connect(water_source, main_line)
        factory.connect(iron_plate_input, main_line, "iron_plate")
        factory.connect(copper_plate_input, main_line, "copper_plate")
        self.output_line = factory.add_buffer("chemical factory output", output_caps)
        factory.connect(main_line, self.output_line, "coal")
        oils_line = factory.add_buffer("oils line")

        # add refineries
        refineries = factory.add_machine_group(OilRefinery(
            OIL_REFINERY_RECIPES["advanced_oil_processing"], oil_refinery_modules
        ))
        factory.connect(water_source, refineries)
        factory.connect(oil_source, refineries)
        factory.connect(refineries, oils_line, "heavy_oil", "light_oil", "petroleum_gas")
        factory.connect(oils_line, main_line, "petroleum_gas")
        factory.connect(oils_line, self.output_line, "light_oil")
        # note: we output first to the oils_line because to prevent the solid fuel crafters from using petroleum made from
        # light oil, since it is better to use light oil directly

        # add lubricant chemical plants
        lubricant_plants = factory.add_machine_group(ChemicalPlant(
            CHEMICAL_PLANT_RECIPES["lubricant"], chemical_plant_modules
        ))
        factory.connect(oils_line, lubricant_plants, "heavy_oil")
        factory.connect(lubricant_plants, self.output_line, "lubricant")

        # add oil cracking chemical plants
        heavy_oil_crackers = factory.add_machine_group(ChemicalPlant(
            CHEMICAL_PLANT_RECIPES["heavy_oil_cracking"], chemical_plant_modules
        ))
        factory.connect(water_source, heavy_oil_crackers)
        factory.connect(oils_line, heavy_oil_crackers, "heavy_oil")
        factory.connect(heavy_oil_crackers, oils_line, "light_oil")
        light_oil_crakers = factory.add_machine_group(ChemicalPlant(
            CHEMICAL_PLANT_RECIPES["light_oil_cracking"], chemical_plant_modules
        ))
        factory.connect(water_source, light_oil_crakers)
        factory.connect(oils_line, light_oil_crakers, "light_oil")
        factory.connect(light_oil_crakers, main_line, "petroleum_gas")

        # add trash point for petroleum gas
        factory.add_trash_point(main_line, "petroleum_gas")

        # add solid fuel chemical plants
        light_oil_solid_fuel_plants = factory.add_machine_group(ChemicalPlant(
            CHEMICAL_PLANT_RECIPES["solid_fuel_from_light_oil"], chemical_plant_modules
        ))
        factory.connect(oils_line, light_oil_solid_fuel_plants, "light_oil")
        factory.connect(light_oil_solid_fuel_plants, self.output_line)
        petroleum_solid_fuel_plants = factory.add_machine_group(ChemicalPlant(
            CHEMICAL_PLANT_RECIPES["solid_fuel_from_petroleum_gas"], chemical_plant_modules
        ))
        factory.connect(oils_line, petroleum_solid_fuel_plants, "petroleum_gas")
        factory.connect(petroleum_solid_fuel_plants, self.output_line)

        # add the chemical crafters for the remaining products
        basic_products = [
            "plastic",
            "sulfur",
            "explosives",
            "sulfuric_acid",
            "battery",
        ]
        for material in basic_products:
            chemical_plants = factory.add_machine_group(ChemicalPlant(
                CHEMICAL_PLANT_RECIPES[material], chemical_plant_modules
            ))
            factory.connect(main_line, chemical_plants, *CHEMICAL_PLANT_RECIPES[material].inp.keys())
            factory.connect(chemical_plants, main_line)
            factory.connect(main_line, self.output_line, material)

    def print_info(self, results: FullAnalysisResults | SingleAnalysisResults):
        print("-------- chemical factory info")
        print(f"theoretical crude oil rate: {self.oil_rate:.2f} /s")
        print("...")


def main():
    factory = Factory()

    iron_plate_source = factory.add_source("iron_plate", 15)
    iron_line = factory.add_buffer("test iron plate line")
    factory.connect(iron_plate_source, iron_line, "iron_plate")

    copper_plate_source = factory.add_source("copper_plate", 15)
    copper_line = factory.add_buffer("test copper plate line")
    factory.connect(copper_plate_source, copper_line, "copper_plate")

    chemical_factory = ChemicalFactory(
        factory, iron_plate_source, copper_plate_source,
        coal_rate=15,
        pumpjack_bonus=.3,
        crude_oil_rates=[
            # 4.67, 4.2, 27.0, 14.8, 14.3, 8.16, 6.17,
            # 35.7, 16.9, 28.1, 18.5, 25.4, 18.8, 30.8, 14.4, 26.6, 19.7
            2.6, 2.6, 8.23, 6.88, 4.54, 3.42, 2.94,
            7.05, 33.0, 23.6, 10.1, 20.7, 11.4, 6.31, 22.4, 12.4, 27.6
            # 2, 2, 6, 5, 3, 2, 2,
            # 5, 25, 18, 7, 15, 8, 9, 17, 21, 4,
        ],
        output_caps={
            "coal": 15,
            "plastic": 15,
            "sulfur": 15,
            "explosives": 15,
            "battery": 15,
            "solid_fuel": 15
        },
        chemical_plant_modules=(Module.PRODUCTION_MODULE_1,)*3,
        pumpjack_modules=(Module.SPEED_MODULE_1,)*2,
        oil_refinery_modules=(Module.PRODUCTION_MODULE_1,)*3
    )
    factory.add_output_point(OutputPoint(chemical_factory.output_line, "coal"))
    factory.add_output_point(OutputPoint(chemical_factory.output_line, "plastic"))
    factory.add_output_point(OutputPoint(chemical_factory.output_line, "sulfuric_acid"))
    factory.add_output_point(OutputPoint(chemical_factory.output_line, "sulfur"))
    factory.add_output_point(OutputPoint(chemical_factory.output_line, "explosives"))
    factory.add_output_point(OutputPoint(chemical_factory.output_line, "battery"))
    factory.add_output_point(OutputPoint(chemical_factory.output_line, "solid_fuel"))

    results = factory.full_analyse()
    print(results.display_full())
    print("")
    chemical_factory.print_info(results)

if __name__ == '__main__':
    main()