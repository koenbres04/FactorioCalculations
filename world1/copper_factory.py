from facalc.factories import SubFactory, OutputPoint, FullAnalysisResults, new_factory
from facalc.factorio_machines import ElectronicFurnace, get_ore_rate, FURNACE_RECIPES, Module
from math import floor

class CopperFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory,
            drill_bonus,
            num_drills: int | None = None,
            drill_modules: tuple[Module, ...] = (),
            furnace_modules: tuple[Module, ...] = (),
            output_caps: dict[str, float] | None = None
    ):
        super().__init__(parent)
        self.ore_rate_per_drill = get_ore_rate(1, drill_bonus, drill_modules)
        self.copper_source = self.add_source("copper_ore", get_ore_rate(num_drills, drill_bonus, drill_modules))
        ore_smelters = self.add_machine_group(ElectronicFurnace(
            recipe=FURNACE_RECIPES["copper_plate"], modules=furnace_modules
        ))
        self.connect(self.copper_source, ore_smelters)
        self.output_belt = self.add_buffer("copper factory output belt", output_caps)
        self.connect(ore_smelters, self.output_belt, "copper_plate")

    def print_info(self, results: FullAnalysisResults):
        rates = results.max_rates
        print("-------- copper factory info")
        print(f"number of used drills: {rates[self.copper_source]/self.ore_rate_per_drill:.2f}")
        print(f"internal iron rate: {rates[self.copper_source]:.2f}/s")
        print(f"num_drills per yellow belt side: {floor(7.5/self.ore_rate_per_drill)}")
        print(f"num_drills per red belt side: {floor(15/self.ore_rate_per_drill)}")
        print(f"num_drills per blue belt side: {floor(22.5/self.ore_rate_per_drill)}")


def main():
    factory = new_factory()
    copper_factory = CopperFactory(
        factory,
        num_drills=141,
        drill_bonus=.3,
        output_caps={"copper_plate": 180},
        furnace_modules=(Module.PRODUCTION_MODULE_1,)*2,
        drill_modules=(Module.SPEED_MODULE_1,)*3
    )
    factory.add_output_point(OutputPoint(copper_factory.output_belt, "copper_plate"))

    results = factory.analyse()
    print(results.display_full())
    print("")
    copper_factory.print_info(results)



if __name__ == '__main__':
    main()