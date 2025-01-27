from facalc.factories import Factory, OutputPoint, SingleAnalysisResults, FullAnalysisResults
from facalc.factorio_machines import Crafter, ElectronicFurnace, get_ore_rate, FURNACE_RECIPES, CRAFTER_RECIPES, Module
from math import floor

class IronFactory:
    def __init__(
            self,
            factory: Factory,
            drill_bonus,
            crafter_level,
            num_drills: int | None = None,
            output_caps: None | dict[str, float] = None,
            iron_ore_line_cap: None | float = None,
            drill_modules: tuple[Module, ...] = (),
            furnace_modules: tuple[Module, ...] = (),
            crafter_modules: tuple[Module, ...] = (),
    ):
        self.ore_rate_per_drill = get_ore_rate(1, drill_bonus, drill_modules)
        self.iron_source = factory.add_source("iron_ore", get_ore_rate(num_drills, drill_bonus, drill_modules))
        self.iron_ore_line = factory.add_buffer("iron ore line", {} if iron_ore_line_cap is None else
        {"iron_ore": iron_ore_line_cap})
        factory.connect(self.iron_source, self.iron_ore_line, "iron_ore")
        ore_smelters = factory.add_machine_group(ElectronicFurnace(
            recipe=FURNACE_RECIPES["iron_plate"], modules=furnace_modules
        ))
        factory.connect(self.iron_source, ore_smelters, "iron_ore")
        self.iron_belt = factory.add_buffer("iron factory iron belt")
        factory.connect(ore_smelters, self.iron_belt, "iron_plate")
        self.output_belt = factory.add_buffer("iron factory output belt", output_caps)
        factory.connect(self.iron_belt, self.output_belt, "iron_plate")
        self.gear_crafters = factory.add_machine_group(Crafter(CRAFTER_RECIPES["gear"], crafter_level, crafter_modules))
        factory.connect(self.iron_belt, self.gear_crafters, "iron_plate")
        factory.connect(self.gear_crafters, self.output_belt, "gear")
        self.steel_smelters = factory.add_machine_group(ElectronicFurnace(
            recipe=FURNACE_RECIPES["steel"], modules=furnace_modules
        ))
        factory.connect(self.iron_belt, self.steel_smelters, "iron_plate")
        factory.connect(self.steel_smelters, self.output_belt, "steel")

    def print_info(self, results: FullAnalysisResults | SingleAnalysisResults):
        if isinstance(results, FullAnalysisResults):
            machine_rates = results.max_machine_rates
            buffer_throughput = results.max_buffer_throughput
            source_rates = results.max_source_rates
        else:
            machine_rates = results.machine_rates
            buffer_throughput = results.buffer_throughput
            source_rates = results.source_rates
        print("-------- iron factory info")
        print(f"number of used drills: {source_rates[self.iron_source]/self.ore_rate_per_drill:.2f}")
        print(f"num_drills per yellow belt side: {floor(7.5/self.ore_rate_per_drill)}")
        print(f"num_drills per red belt side: {floor(15/self.ore_rate_per_drill)}")
        print(f"num_drills per blue belt side: {floor(22.5/self.ore_rate_per_drill)}")
        print(f"internal iron rate: {buffer_throughput[(self.iron_belt, 'iron_plate')]:.2f}/s")
        print(f"iron plate rate for gears: {self.gear_crafters.input_rate(results, 'iron_plate'):.2f}")
        print(f"iron plate rate for steel: {self.steel_smelters.input_rate(results, 'iron_plate'):.2f}")

def main():
    factory = Factory()
    iron_factory = IronFactory(
        factory,
        num_drills=160,
        drill_bonus=.3,
        crafter_level=3,
        # output_caps={
        #     "iron_plate": 210,
        #     "gear": 30,
        #     "steel": 15
        # },
        # iron_ore_line_cap=,
        furnace_modules=(Module.PRODUCTION_MODULE_1,)*2,
        crafter_modules=(Module.PRODUCTION_MODULE_1,)*3,
        drill_modules=(Module.SPEED_MODULE_1,)*3
    )
    factory.add_output_point(OutputPoint(iron_factory.output_belt, "iron_plate"))
    factory.add_output_point(OutputPoint(iron_factory.output_belt, "gear"))
    factory.add_output_point(OutputPoint(iron_factory.output_belt, "steel"))

    results = factory.full_analyse()
    print(results.display_full())
    print("")
    iron_factory.print_info(results)

if __name__ == '__main__':
    main()