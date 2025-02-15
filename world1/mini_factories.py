from facalc.factories import SubFactory, Buffer
from facalc.factorio_machines import Crafter, CRAFTER_RECIPES, Module


class LDSFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory,
            copper_plate_line: Buffer, plastic_line: Buffer, steel_line: Buffer,
            crafter_level,
            crafter_modules: tuple[Module, ...] = (),
            input_cap: dict[str, float] | None = None,
            output_cap: dict[str, float] | None = None
    ):
        super().__init__(parent)
        self.input_belt = self.add_buffer("lds factory input belt", input_cap)
        self.connect(copper_plate_line, self.input_belt, "copper_plate")
        self.connect(plastic_line, self.input_belt, "plastic")
        self.connect(steel_line, self.input_belt, "steel")

        self.output_belt = self.add_buffer("lds factory output", output_cap)
        self.crafters = self.add_machine_group(
        Crafter(CRAFTER_RECIPES["low_density_structure"], crafter_level, crafter_modules)
        )
        self.connect(self.input_belt, self.crafters, "copper_plate", "plastic", "steel")
        self.connect(self.crafters, self.output_belt)


class RailFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory,
            iron_plate_line: Buffer, steel_line: Buffer, stone_line: Buffer,
            crafter_level,
            rail_crafter_modules: tuple[Module, ...] = (),
            stick_crafter_modules: tuple[Module, ...] = (),
            input_cap: dict[str, float] | None = None,
            output_cap: dict[str, float] | None = None
    ):
        super().__init__(parent)
        self.input_belt = self.add_buffer("rail factory input belt", input_cap)
        self.connect(iron_plate_line, self.input_belt, "iron_plate")
        self.connect(stone_line, self.input_belt, "stone")
        self.connect(steel_line, self.input_belt, "steel")

        self.iron_stick_crafters = self.add_machine_group(
        Crafter(CRAFTER_RECIPES["iron_stick"], crafter_level, stick_crafter_modules)
        )
        self.connect(self.input_belt, self.iron_stick_crafters, "iron_plate")
        self.connect(self.iron_stick_crafters, self.input_belt)

        self.output_belt = self.add_buffer("rail factory output", output_cap)
        self.crafters = self.add_machine_group(
        Crafter(CRAFTER_RECIPES["rail"], crafter_level, rail_crafter_modules)
        )
        self.connect(self.input_belt, self.crafters, "iron_stick", "steel", "stone")
        self.connect(self.crafters, self.output_belt)
