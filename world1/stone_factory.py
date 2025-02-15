from facalc.factories import SubFactory, OutputPoint, Buffer, FullAnalysisResults, new_factory
from facalc.factorio_machines import Crafter, ElectronicFurnace, CRAFTER_RECIPES, FURNACE_RECIPES, get_ore_rate, Module
from math import floor


class StoneFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory,
            iron_ore_line: Buffer,
            drill_bonus,
            crafter_level,
            num_drills: float | None = None,
            drill_modules: tuple[Module, ...] = (),
            furnace_modules: tuple[Module, ...] = (),
            crafter_modules: tuple[Module, ...] = (),
            output_caps: dict[str, float] | None = None,
    ):
        super().__init__(parent)
        # add stone source and line
        self.stone_rate_per_drill = get_ore_rate(1, drill_bonus, drill_modules)
        self.stone_source = self.add_source("stone", get_ore_rate(num_drills, drill_bonus, drill_modules))
        self.stone_buffer = self.add_buffer("stone factory line")
        self.connect(self.stone_source, self.stone_buffer, "stone")

        # add brick furnaces
        self.brick_furnaces = self.add_machine_group(ElectronicFurnace(
            recipe=FURNACE_RECIPES["stone_brick"], modules=furnace_modules
        ))
        self.connect(self.stone_buffer, self.brick_furnaces, "stone")
        self.connect(self.brick_furnaces, self.stone_buffer, "stone_brick")

        # add concrete crafters
        water_source = self.add_source("water")
        concrete_crafters = self.add_machine_group(Crafter(
            recipe=CRAFTER_RECIPES["concrete"], crafter_level=crafter_level, modules=crafter_modules
        ))
        self.connect(water_source, concrete_crafters, "water")
        self.connect(iron_ore_line, concrete_crafters, "iron_ore")
        self.connect(self.stone_buffer, concrete_crafters, "stone_brick")

        self.output_line = self.add_buffer("stone factory output", output_caps)
        self.connect(self.stone_buffer, self.output_line, "stone", "stone_brick")
        self.connect(concrete_crafters, self.output_line, "concrete")

    def print_info(self, results: FullAnalysisResults):
        rates = results.max_rates
        print("-------- stone factory info")
        print(f"number of used drills: {rates[self.stone_source]/self.stone_rate_per_drill:.2f}")
        print(f"internal stone rate: {rates[(self.stone_buffer, 'stone')]:.2f}/s")
        print(f"num_drills per yellow belt side: {floor(7.5/self.stone_rate_per_drill)}")
        print(f"num_drills per red belt side: {floor(15/self.stone_rate_per_drill)}")
        print(f"num_drills per blue belt side: {floor(22.5/self.stone_rate_per_drill)}")


def main():
    factory = new_factory()
    iron_ore_source = factory.add_source("iron_ore")
    iron_ore_line = factory.add_buffer("test iron ore line")
    factory.connect(iron_ore_source, iron_ore_line, "iron_ore")
    stone_factory = StoneFactory(
        factory, iron_ore_line,
        num_drills=65,
        drill_bonus=.3,
        crafter_level=3,
        output_caps={
            "stone": 30,
            "stone_brick": 15,
            "concrete": 15
        },
        furnace_modules=(Module.PRODUCTION_MODULE_1,)*2,
        crafter_modules=(Module.PRODUCTION_MODULE_1,)*4,
        drill_modules=(Module.PRODUCTION_MODULE_1,)*3
    )
    factory.add_output_point(OutputPoint(stone_factory.output_line, "stone"))
    factory.add_output_point(OutputPoint(stone_factory.output_line, "stone_brick"))
    factory.add_output_point(OutputPoint(stone_factory.output_line, "concrete"))

    results = factory.analyse()
    print(results.display_full())
    print("")
    stone_factory.print_info(results)


if __name__ == '__main__':
    main()