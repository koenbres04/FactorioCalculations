from itertools import chain
from facalc.factories import SubFactory, OutputPoint, FullAnalysisResults
from facalc.factorio_machines import Crafter, CRAFTER_RECIPES, Module

class MiscFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory,
            immediate_outputs: list[str],
            stations: list[str],
            productivity_crafter_level: int,
            non_productivity_crafter_level: int,
            productivity_crafter_modules: tuple[Module, ...] = (),
            non_productivity_crafter_modules: tuple[Module, ...] = (),
            crafter_caps: dict[str, float] | None = None,
            belt_caps: dict[str, float] | None = None,
            default_belt_cap: float | None = None
    ):
        super().__init__(parent)
        if crafter_caps is None:
            crafter_caps = dict()
        if default_belt_cap is not None:
            if belt_caps is None:
                belt_caps = dict()
            for key in chain(immediate_outputs, stations):
                if key not in belt_caps:
                    belt_caps[key] = default_belt_cap

        self.main_belt = self.add_buffer("main belt", rate_caps=belt_caps)
        # add immediate outputs
        for material in immediate_outputs:
            self.add_output_point(OutputPoint(self.main_belt, material))

        # add crafters
        for material in stations:
            recipe = CRAFTER_RECIPES[material]
            if recipe.supports_prod_modules:
                crafter_type = Crafter(recipe, productivity_crafter_level, productivity_crafter_modules)
            else:
                crafter_type = Crafter(recipe, non_productivity_crafter_level, non_productivity_crafter_modules)
            if material in crafter_caps:
                crafters = self.add_machine_group(crafter_type, crafter_caps[material])
            else:
                crafters = self.add_machine_group(crafter_type)
            self.connect(crafters, self.main_belt, material)
            for inp in recipe.inp.keys():
                self.connect(self.main_belt, crafters, inp)
            self.add_output_point(OutputPoint(self.main_belt, material))

    def print_info(self, results: FullAnalysisResults):
        print("-------- misc factory info")
        self.print_machines(results.max_rates)
        self.print_buffer_throughput(results.max_rates)
