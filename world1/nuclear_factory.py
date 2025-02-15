from facalc.factories import SubFactory, OutputPoint, Buffer, FullAnalysisResults, new_factory
from facalc.factorio_machines import (Crafter, CRAFTER_RECIPES, Centrifuge, CENTRIFUGE_RECIPES, UraniumDrill, Module,
                                      NuclearReactor)
from math import floor


class NuclearFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory,
            iron_plate_line: Buffer,
            sulfuric_acid_line: Buffer,
            rocket_fuel_line: Buffer,
            num_nuclear_reactors: int,
            resource_bonus,
            num_drills: float | None = None,
            drill_modules: tuple[Module, ...] = (),
            centrifuge_modules: tuple[Module, ...] = (),
            crafter_level=1,
            crafter_modules: tuple[Module, ...] = (),
            input_caps: dict[str, float] | None = None,
            output_caps: dict[str, float] | None = None,
    ):
        super().__init__(parent)
        # add input line
        self.input_line = self.add_buffer("uranium factory input line", input_caps)
        self.connect(iron_plate_line, self.input_line, "iron_plate")
        self.connect(sulfuric_acid_line, self.input_line, "sulfuric_acid")
        self.connect(rocket_fuel_line, self.input_line, "rocket_fuel")
        # add drill and ore processing
        self.pre_uranium_ore_source = self.add_source("pre_uranium_ore")
        self.drills = self.add_machine_group(UraniumDrill(resource_bonus, drill_modules), num_drills)
        self.connect(self.input_line, self.drills, "sulfuric_acid")
        self.connect(self.pre_uranium_ore_source, self.drills)
        self.ore_centrifuges = self.add_machine_group(Centrifuge(
            CENTRIFUGE_RECIPES["uranium_processing"], centrifuge_modules
        ))
        self.connect(self.drills, self.ore_centrifuges)

        # connect ore processing centrifuges to various lines
        self.raw_uranium_line = self.add_buffer("uranium factory raw uranium line")
        self.uranium_line = self.add_buffer("uranium factory uranium line")
        self.uranium_loop = self.add_buffer("uranium factory uranium loop")
        self.output_line = self.add_buffer("uranium factory output line", output_caps)
        self.connect(self.uranium_line, self.output_line, "uranium-235", "uranium-238")
        self.connect(self.ore_centrifuges, self.raw_uranium_line, "uranium-235", "uranium-238")
        self.connect(self.raw_uranium_line, self.uranium_line, "uranium-235", "uranium-238")

        # add trash point for U-235
        self.add_trash_point(self.raw_uranium_line, "uranium-235")

        # add kovarex enrichment loop
        self.enrichment_centrifuges = self.add_machine_group(Centrifuge(
            CENTRIFUGE_RECIPES["kovarex_enrichment_process"], centrifuge_modules
        ))
        self.connect(self.uranium_line, self.uranium_loop, "uranium-238")
        self.connect(self.enrichment_centrifuges, self.uranium_loop, "uranium-238", "uranium-235")
        self.connect(self.uranium_loop, self.enrichment_centrifuges, "uranium-238", "uranium-235")
        self.connect(self.uranium_loop, self.uranium_line, "uranium-235")

        # add nuclear fuel centrifuges
        self.nuclear_fuel_centrifuges = self.add_machine_group(Centrifuge(
            CENTRIFUGE_RECIPES["nuclear_fuel"], centrifuge_modules
        ))
        self.connect(self.input_line, self.nuclear_fuel_centrifuges, "rocket_fuel")
        self.connect(self.uranium_line, self.nuclear_fuel_centrifuges, "uranium-235")
        self.connect(self.nuclear_fuel_centrifuges, self.output_line, "nuclear_fuel")

        # add fuel cell crafting
        self.fuel_cell_crafters = self.add_machine_group(Crafter(
            CRAFTER_RECIPES["uranium_fuel_cell"], crafter_level, crafter_modules
        ))
        self.connect(self.input_line, self.fuel_cell_crafters, "iron_plate")
        self.connect(self.uranium_line, self.fuel_cell_crafters, "uranium-238", "uranium-235")
        self.connect(self.fuel_cell_crafters, self.output_line, "uranium_fuel_cell")

        # add nuclear fuel usage
        self.nuclear_reactors = self.add_machine_group(NuclearReactor(), num_nuclear_reactors)
        self.connect(self.output_line, self.nuclear_reactors, "uranium_fuel_cell")
        self.power_output_point = OutputPoint(self.nuclear_reactors, "uranium_fuel_cell_power")
        self.add_output_point(self.power_output_point)
        self.depleted_fuel_cell_centrifuges = self.add_machine_group(Centrifuge(
            CENTRIFUGE_RECIPES["nuclear_fuel_reprocessing"], centrifuge_modules
        ))
        self.connect(self.nuclear_reactors, self.depleted_fuel_cell_centrifuges, "depleted_uranium_fuel_cell")
        self.connect(self.depleted_fuel_cell_centrifuges, self.uranium_line, "uranium-238")


    def print_info(self, results: FullAnalysisResults):
        rates = results.max_rates
        print("-------- uranium factory info")
        print(f"sulfuric acid rate: {self.drills.input_rate(rates, "sulfuric_acid"):.2f}/s")
        print(f"number of used drills: {rates[self.drills]:.2f}")
        ore_rate_per_drill = self.drills.machine_type.output_rates["uranium_ore"]
        print(f"num drills per yellow belt side: {floor(7.5/ore_rate_per_drill)}")
        print(f"num drills per red belt side: {floor(15/ore_rate_per_drill)}")
        print(f"num drills per blue belt side: {floor(22.5/ore_rate_per_drill)}")
        print(f"ore rate: {self.drills.output_rate(rates, "uranium_ore"):.2f}/s")
        print(self.ore_centrifuges.machine_type.display_info(rates[self.ore_centrifuges]))
        print(self.enrichment_centrifuges.machine_type.display_info(rates[self.enrichment_centrifuges]))
        print(f"kovarex loop U-235 rate: {rates[(self.uranium_loop, 'uranium-235')]:.2f}/s")
        print(f"kovarex loop U-238 rate: {rates[(self.uranium_loop, 'uranium-238')]:.2f}/s")
        print(self.nuclear_fuel_centrifuges.machine_type.display_info(rates[self.nuclear_fuel_centrifuges]))
        print(self.depleted_fuel_cell_centrifuges.machine_type.display_info(rates[self.depleted_fuel_cell_centrifuges]))
        print(self.fuel_cell_crafters.machine_type.display_info(rates[self.fuel_cell_crafters]))



def main():
    factory = new_factory()
    iron_plate_source = factory.add_source("iron_plate")
    iron_plate_line = factory.add_buffer("test iron plate line")
    factory.connect(iron_plate_source, iron_plate_line)
    sulfuric_acid_source = factory.add_source("sulfuric_acid")
    sulfuric_acid_line = factory.add_buffer("test sulfuric acid line")
    factory.connect(sulfuric_acid_source, sulfuric_acid_line)
    rocket_fuel_source = factory.add_source("rocket_fuel")
    rocket_fuel_line = factory.add_buffer("test rocket fuel line")
    factory.connect(rocket_fuel_source, rocket_fuel_line)

    nuclear_factory = NuclearFactory(
        factory, iron_plate_line, sulfuric_acid_line, rocket_fuel_line,
        num_nuclear_reactors=100,
        num_drills=40,
        resource_bonus=.3,
        input_caps={
        },
        output_caps={
        },
        centrifuge_modules=(Module.PRODUCTION_MODULE_1,)*2,
        crafter_modules=(Module.PRODUCTION_MODULE_3,)*4,
        crafter_level=3,
        drill_modules=(Module.PRODUCTION_MODULE_2,)*3
    )
    factory.add_output_point(OutputPoint(nuclear_factory.output_line, "uranium-235", 7.5))
    factory.add_output_point(OutputPoint(nuclear_factory.output_line, "uranium-238", 7.5))
    factory.add_output_point(OutputPoint(nuclear_factory.output_line, "nuclear_fuel", 1.))
    factory.add_output_point(OutputPoint(nuclear_factory.output_line, "uranium_fuel_cell", 7.5))

    results = factory.analyse()
    print(results.display_full())
    print("")
    nuclear_factory.print_info(results)


if __name__ == '__main__':
    main()