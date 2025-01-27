from facalc.factories import Factory, OutputPoint, FullAnalysisResults, SingleAnalysisResults
from facalc.factorio_machines import ElectronicFurnace, get_ore_rate, FURNACE_RECIPES, Module
from math import floor

class CopperFactory:
    def __init__(
            self,
            factory: Factory,
            drill_bonus,
            num_drills: int | None = None,
            drill_modules: tuple[Module, ...] = (),
            furnace_modules: tuple[Module, ...] = (),
            output_caps: dict[str, float] | None = None
    ):
        self.ore_rate_per_drill = get_ore_rate(1, drill_bonus, drill_modules)
        self.copper_source = factory.add_source("copper_ore", get_ore_rate(num_drills, drill_bonus, drill_modules))
        ore_smelters = factory.add_machine_group(ElectronicFurnace(
            recipe=FURNACE_RECIPES["copper_plate"], modules=furnace_modules
        ))
        factory.connect(self.copper_source, ore_smelters)
        self.output_belt = factory.add_buffer("copper factory output belt", output_caps)
        factory.connect(ore_smelters, self.output_belt, "copper_plate")

    def print_info(self, results: FullAnalysisResults | SingleAnalysisResults):
        if isinstance(results, FullAnalysisResults):
            source_rates = results.max_source_rates
        else:
            source_rates = results.source_rates
        print("-------- copper factory info")
        print(f"number of used drills: {source_rates[self.copper_source]/self.ore_rate_per_drill:.2f}")
        print(f"internal iron rate: {source_rates[self.copper_source]:.2f}/s")
        print(f"num_drills per yellow belt side: {floor(7.5/self.ore_rate_per_drill)}")
        print(f"num_drills per red belt side: {floor(15/self.ore_rate_per_drill)}")
        print(f"num_drills per blue belt side: {floor(22.5/self.ore_rate_per_drill)}")


def main():
    factory = Factory()
    copper_factory = CopperFactory(
        factory,
        num_drills=141,
        drill_bonus=.3,
        output_caps={"copper_plate": 180},
        furnace_modules=(Module.PRODUCTION_MODULE_1,)*2,
        drill_modules=(Module.SPEED_MODULE_1,)*3
    )
    factory.add_output_point(OutputPoint(copper_factory.output_belt, "copper_plate"))

    results = factory.full_analyse()
    print(results.display_full())
    print("")
    copper_factory.print_info(results)



if __name__ == '__main__':
    main()