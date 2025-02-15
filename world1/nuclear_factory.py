from facalc.factories import Factory, OutputPoint, Buffer, FullAnalysisResults, SingleAnalysisResults, MachineType
from facalc.factorio_machines import (Crafter, CRAFTER_RECIPES, Centrifuge, CENTRIFUGE_RECIPES, UraniumDrill, Module,
                                      NuclearReactor)
from math import floor


class NuclearFactory:
    def __init__(
            self,
            factory: Factory,
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
        # add input line
        self.input_line = factory.add_buffer("uranium factory input line", input_caps)
        factory.connect(iron_plate_line, self.input_line, "iron_plate")
        factory.connect(sulfuric_acid_line, self.input_line, "sulfuric_acid")
        factory.connect(rocket_fuel_line, self.input_line, "rocket_fuel")
        # add drill and ore processing
        self.pre_uranium_ore_source = factory.add_source("pre_uranium_ore")
        self.drills = factory.add_machine_group(UraniumDrill(resource_bonus, drill_modules), num_drills)
        factory.connect(self.input_line, self.drills, "sulfuric_acid")
        factory.connect(self.pre_uranium_ore_source, self.drills)
        self.ore_centrifuges = factory.add_machine_group(Centrifuge(
            CENTRIFUGE_RECIPES["uranium_processing"], centrifuge_modules
        ))
        factory.connect(self.drills, self.ore_centrifuges)

        # connect ore processing centrifuges to various lines
        self.uranium_line = factory.add_buffer("uranium factory uranium line")
        self.uranium_loop = factory.add_buffer("uranium factory uranium loop")
        self.output_line = factory.add_buffer("uranium factory output line", output_caps)
        factory.connect(self.uranium_line, self.output_line, "uranium-235", "uranium-238")
        factory.connect(self.ore_centrifuges, self.uranium_line, "uranium-235", "uranium-238")

        # add trash point for U-235
        factory.add_trash_point(self.uranium_line, "uranium-235")

        # add kovarex enrichment loop
        self.enrichment_centrifuges = factory.add_machine_group(Centrifuge(
            CENTRIFUGE_RECIPES["kovarex_enrichment_process"], centrifuge_modules
        ))
        factory.connect(self.uranium_line, self.uranium_loop, "uranium-238")
        factory.connect(self.enrichment_centrifuges, self.uranium_loop, "uranium-238", "uranium-235")
        factory.connect(self.uranium_loop, self.enrichment_centrifuges, "uranium-238", "uranium-235")
        factory.connect(self.uranium_loop, self.uranium_line, "uranium-235")

        # add nuclear fuel centrifuges
        self.nuclear_fuel_centrifuges = factory.add_machine_group(Centrifuge(
            CENTRIFUGE_RECIPES["nuclear_fuel"], centrifuge_modules
        ))
        factory.connect(self.input_line, self.nuclear_fuel_centrifuges, "rocket_fuel")
        factory.connect(self.uranium_line, self.nuclear_fuel_centrifuges, "uranium-235")
        factory.connect(self.nuclear_fuel_centrifuges, self.output_line, "nuclear_fuel")

        # add fuel cell crafting
        self.fuel_cell_crafters = factory.add_machine_group(Crafter(
            CRAFTER_RECIPES["uranium_fuel_cell"], crafter_level, crafter_modules
        ))
        factory.connect(self.input_line, self.fuel_cell_crafters, "iron_plate")
        factory.connect(self.uranium_line, self.fuel_cell_crafters, "uranium-238", "uranium-235")
        factory.connect(self.fuel_cell_crafters, self.output_line, "uranium_fuel_cell")

        # add nuclear fuel usage
        self.nuclear_reactors = factory.add_machine_group(NuclearReactor(), num_nuclear_reactors)
        factory.connect(self.output_line, self.nuclear_reactors, "uranium_fuel_cell")
        self.power_output_point = OutputPoint(self.nuclear_reactors, "uranium_fuel_cell_power")
        factory.add_output_point(self.power_output_point)
        self.depleted_fuel_cell_centrifuges = factory.add_machine_group(Centrifuge(
            CENTRIFUGE_RECIPES["nuclear_fuel_reprocessing"], centrifuge_modules
        ))
        factory.connect(self.nuclear_reactors, self.depleted_fuel_cell_centrifuges, "depleted_uranium_fuel_cell")
        factory.connect(self.depleted_fuel_cell_centrifuges, self.uranium_line, "uranium-238")


    def print_info(self, results: FullAnalysisResults | SingleAnalysisResults):
        if isinstance(results, FullAnalysisResults):
            buffer_throughput = results.max_buffer_throughput
            machine_rates = results.max_machine_rates
        else:
            buffer_throughput = results.buffer_throughput
            machine_rates = results.machine_rates
        print("-------- uranium factory info")
        print(f"sulfuric acid rate: {self.drills.input_rate(results, "sulfuric_acid"):.2f}/s")
        print(f"number of used drills: {machine_rates[self.drills]:.2f}")
        ore_rate_per_drill = self.drills.machine_type.output_rates["uranium_ore"]
        print(f"num drills per yellow belt side: {floor(7.5/ore_rate_per_drill)}")
        print(f"num drills per red belt side: {floor(15/ore_rate_per_drill)}")
        print(f"num drills per blue belt side: {floor(22.5/ore_rate_per_drill)}")
        print(f"ore rate: {self.drills.output_rate(results, "uranium_ore"):.2f}/s")
        print(self.ore_centrifuges.machine_type.display_info(machine_rates[self.ore_centrifuges]))
        print(self.enrichment_centrifuges.machine_type.display_info(machine_rates[self.enrichment_centrifuges]))
        print(f"kovarex loop U-235 rate: {buffer_throughput[(self.uranium_loop, 'uranium-235')]:.2f}/s")
        print(f"kovarex loop U-238 rate: {buffer_throughput[(self.uranium_loop, 'uranium-238')]:.2f}/s")
        print(self.nuclear_fuel_centrifuges.machine_type.display_info(machine_rates[self.nuclear_fuel_centrifuges]))
        print(self.depleted_fuel_cell_centrifuges.machine_type.display_info(machine_rates[self.depleted_fuel_cell_centrifuges]))
        print(self.fuel_cell_crafters.machine_type.display_info(machine_rates[self.fuel_cell_crafters]))



def main():
    factory = Factory()
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

    results = factory.full_analyse()
    print(results.display_full())
    print("")
    nuclear_factory.print_info(results)


if __name__ == '__main__':
    main()