from facalc.factories import new_factory, OutputPoint
from facalc.factorio_machines import Crafter, ElectronicFurnace, FURNACE_RECIPES, CRAFTER_RECIPES

def main():
    factory = new_factory()

    # temporary hardcoded recipes
    iron_smelt_recipe = FURNACE_RECIPES["iron_plate"]
    gear_recipe = CRAFTER_RECIPES["gear"]
    belt_recipe = CRAFTER_RECIPES["belt"]

    # add basic sources
    iron_source = factory.add_source("iron_ore", 60)
    temp_buffer = factory.add_buffer("temp_buffer")
    factory.connect(iron_source, temp_buffer, "iron_ore")
    iron_smelters = factory.add_machine_group(ElectronicFurnace(iron_smelt_recipe))
    factory.connect(temp_buffer, iron_smelters, "iron_ore")
    iron_factory_buffer = factory.add_buffer("iron_buffer")
    factory.connect(iron_smelters, iron_factory_buffer, "iron_plate")
    factory.add_output_point(OutputPoint(iron_factory_buffer, "iron_plate"))
    gear_crafters = factory.add_machine_group(Crafter(gear_recipe, 3))
    factory.connect(iron_factory_buffer, gear_crafters, "iron_plate")
    factory.connect(gear_crafters, iron_factory_buffer, "gear")
    factory.add_output_point(OutputPoint(iron_factory_buffer, "gear"))
    belt_crafters = factory.add_machine_group(Crafter(belt_recipe, 3))
    factory.connect(iron_factory_buffer, belt_crafters, "iron_plate")
    factory.connect(iron_factory_buffer, belt_crafters, "gear")
    factory.add_output_point(OutputPoint(belt_crafters, "belt"))

    factory.default_print_info(factory.analyse())


if __name__ == '__main__':
    main()