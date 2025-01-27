from facalc.factories import Factory, Buffer
from facalc.factorio_machines import Crafter, CRAFTER_RECIPES, Module


class LDSFactory:
    def __init__(
            self,
            factory: Factory,
            copper_plate_line: Buffer, plastic_line: Buffer, steel_line: Buffer,
            crafter_level,
            crafter_modules: tuple[Module, ...] = (),
            input_cap: dict[str, float] | None = None,
            output_cap: dict[str, float] | None = None
    ):
        self.input_belt = factory.add_buffer("lds factory input belt", input_cap)
        factory.connect(copper_plate_line, self.input_belt, "copper_plate")
        factory.connect(plastic_line, self.input_belt, "plastic")
        factory.connect(steel_line, self.input_belt, "steel")

        self.output_belt = factory.add_buffer("lds factory output", output_cap)
        self.crafters = factory.add_machine_group(
        Crafter(CRAFTER_RECIPES["low_density_structure"], crafter_level, crafter_modules)
        )
        factory.connect(self.input_belt, self.crafters, "copper_plate", "plastic", "steel")
        factory.connect(self.crafters, self.output_belt)


class RailFactory:
    def __init__(
            self,
            factory: Factory,
            iron_plate_line: Buffer, steel_line: Buffer, stone_line: Buffer,
            crafter_level,
            rail_crafter_modules: tuple[Module, ...] = (),
            stick_crafter_modules: tuple[Module, ...] = (),
            input_cap: dict[str, float] | None = None,
            output_cap: dict[str, float] | None = None
    ):
        self.input_belt = factory.add_buffer("rail factory input belt", input_cap)
        factory.connect(iron_plate_line, self.input_belt, "iron_plate")
        factory.connect(stone_line, self.input_belt, "stone")
        factory.connect(steel_line, self.input_belt, "steel")

        self.iron_stick_crafters = factory.add_machine_group(
        Crafter(CRAFTER_RECIPES["iron_stick"], crafter_level, stick_crafter_modules)
        )
        factory.connect(self.input_belt, self.iron_stick_crafters, "iron_plate")
        factory.connect(self.iron_stick_crafters, self.input_belt)

        self.output_belt = factory.add_buffer("rail factory output", output_cap)
        self.crafters = factory.add_machine_group(
        Crafter(CRAFTER_RECIPES["rail"], crafter_level, rail_crafter_modules)
        )
        factory.connect(self.input_belt, self.crafters, "iron_stick", "steel", "stone")
        factory.connect(self.crafters, self.output_belt)
