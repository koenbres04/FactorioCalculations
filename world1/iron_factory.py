from facalc.factories import OutputPoint, SingleAnalysisResults, FullAnalysisResults, SubFactory, new_factory
from facalc.factorio_machines import Crafter, ElectronicFurnace, get_ore_rate, FURNACE_RECIPES, CRAFTER_RECIPES, Module
from math import floor

class IronFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory,
            drill_bonus,
            crafter_level,
            num_drills: int | None = None,
            output_caps: None | dict[str, float] = None,
            iron_ore_line_cap: None | float = None,
            drill_modules: tuple[Module, ...] = (),
            furnace_modules: tuple[Module, ...] = (),
            crafter_modules: tuple[Module, ...] = (),
    ):
        super().__init__(parent)
        self.ore_rate_per_drill = get_ore_rate(1, drill_bonus, drill_modules)
        self.iron_source = self.add_source("iron_ore", get_ore_rate(num_drills, drill_bonus, drill_modules))
        self.iron_ore_line = self.add_buffer("iron ore line", {} if iron_ore_line_cap is None else
        {"iron_ore": iron_ore_line_cap})
        self.connect(self.iron_source, self.iron_ore_line, "iron_ore")
        ore_smelters = self.add_machine_group(ElectronicFurnace(
            recipe=FURNACE_RECIPES["iron_plate"], modules=furnace_modules
        ))
        self.connect(self.iron_source, ore_smelters, "iron_ore")
        self.iron_belt = self.add_buffer("iron factory iron belt")
        self.connect(ore_smelters, self.iron_belt, "iron_plate")
        self.output_belt = self.add_buffer("iron factory output belt", output_caps)
        self.connect(self.iron_belt, self.output_belt, "iron_plate")
        self.gear_crafters = self.add_machine_group(Crafter(CRAFTER_RECIPES["gear"], crafter_level, crafter_modules))
        self.connect(self.iron_belt, self.gear_crafters, "iron_plate")
        self.connect(self.gear_crafters, self.output_belt, "gear")
        self.steel_smelters = self.add_machine_group(ElectronicFurnace(
            recipe=FURNACE_RECIPES["steel"], modules=furnace_modules
        ))
        self.connect(self.iron_belt, self.steel_smelters, "iron_plate")
        self.connect(self.steel_smelters, self.output_belt, "steel")

    def print_info(self, results: FullAnalysisResults | SingleAnalysisResults):
        rates = results.rates if isinstance(results, SingleAnalysisResults) else results.max_rates
        print("-------- iron factory info")
        print(f"number of used drills: {rates[self.iron_source]/self.ore_rate_per_drill:.2f}")
        print(f"num_drills per yellow belt side: {floor(7.5/self.ore_rate_per_drill)}")
        print(f"num_drills per red belt side: {floor(15/self.ore_rate_per_drill)}")
        print(f"num_drills per blue belt side: {floor(22.5/self.ore_rate_per_drill)}")
        print(f"internal iron rate: {rates[(self.iron_belt, 'iron_plate')]:.2f}/s")
        print(f"iron plate rate for gears: {self.gear_crafters.input_rate(rates, 'iron_plate'):.2f}")
        print(f"iron plate rate for steel: {self.steel_smelters.input_rate(rates, 'iron_plate'):.2f}")
        self.print_machines(rates)

def main():
    factory = new_factory()
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

    results = factory.analyse()
    print(results.display_full())
    print("")
    iron_factory.print_info(results)

if __name__ == '__main__':
    main()