from facalc.factories import Factory, OutputPoint, Buffer, FullAnalysisResults, SingleAnalysisResults
from facalc.factorio_machines import Crafter, ElectronicFurnace, CRAFTER_RECIPES, FURNACE_RECIPES, get_ore_rate, Module
from math import floor


class StoneFactory:
    def __init__(
            self,
            factory: Factory,
            iron_ore_line: Buffer,
            drill_bonus,
            crafter_level,
            num_drills: float | None = None,
            drill_modules: tuple[Module, ...] = (),
            furnace_modules: tuple[Module, ...] = (),
            crafter_modules: tuple[Module, ...] = (),
            output_caps: dict[str, float] | None = None,
    ):
        # add stone source and line
        self.stone_rate_per_drill = get_ore_rate(1, drill_bonus, drill_modules)
        self.stone_source = factory.add_source("stone", get_ore_rate(num_drills, drill_bonus, drill_modules))
        self.stone_buffer = factory.add_buffer("stone factory line")
        factory.connect(self.stone_source, self.stone_buffer, "stone")

        # add brick furnaces
        self.brick_furnaces = factory.add_machine_group(ElectronicFurnace(
            recipe=FURNACE_RECIPES["stone_brick"], modules=furnace_modules
        ))
        factory.connect(self.stone_buffer, self.brick_furnaces, "stone")
        factory.connect(self.brick_furnaces, self.stone_buffer, "stone_brick")

        # add concrete crafters
        water_source = factory.add_source("water")
        concrete_crafters = factory.add_machine_group(Crafter(
            recipe=CRAFTER_RECIPES["concrete"], crafter_level=crafter_level, modules=crafter_modules
        ))
        factory.connect(water_source, concrete_crafters, "water")
        factory.connect(iron_ore_line, concrete_crafters, "iron_ore")
        factory.connect(self.stone_buffer, concrete_crafters, "stone_brick")

        self.output_line = factory.add_buffer("stone factory output", output_caps)
        factory.connect(self.stone_buffer, self.output_line, "stone", "stone_brick")
        factory.connect(concrete_crafters, self.output_line, "concrete")

    def print_info(self, results: FullAnalysisResults | SingleAnalysisResults):
        if isinstance(results, FullAnalysisResults):
            buffer_throughput = results.max_buffer_throughput
            source_rates = results.max_source_rates
        else:
            buffer_throughput = results.buffer_throughput
            source_rates = results.source_rates
        print("-------- stone factory info")
        print(f"number of used drills: {source_rates[self.stone_source]/self.stone_rate_per_drill:.2f}")
        print(f"internal stone rate: {buffer_throughput[(self.stone_buffer, 'stone')]:.2f}/s")
        print(f"num_drills per yellow belt side: {floor(7.5/self.stone_rate_per_drill)}")
        print(f"num_drills per red belt side: {floor(15/self.stone_rate_per_drill)}")
        print(f"num_drills per blue belt side: {floor(22.5/self.stone_rate_per_drill)}")


def main():
    factory = Factory()
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

    results = factory.full_analyse()
    print(results.display_full())
    print("")
    stone_factory.print_info(results)


if __name__ == '__main__':
    main()