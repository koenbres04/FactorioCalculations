from facalc.factories import _Factory, SubFactory, Buffer, FullAnalysisResults, MachineGroup
from facalc.factorio_machines import Crafter, CRAFTER_RECIPES, Module
from typing import Iterable


class ModuleFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory | _Factory, circuit_line: Buffer,
            module_types: Iterable[str],
            crafter_level,
            crafter_modules: tuple[Module, ...] = (),
            input_caps: dict[str, float] | None = None,
            output_caps: dict[str, float] | None = None,
    ):
        super().__init__(parent)
        self.input_line = self.add_buffer("module factory input", input_caps)
        self.connect(circuit_line, self.input_line, "circuit", "red_circuit", "blue_circuit")
        self.module_line = self.add_buffer("module factory line")
        self.output_line = self.add_buffer("module factory output", output_caps)
        self.crafters: dict[str, list[MachineGroup]] = {}
        for module_type in module_types:
            crafters = []
            module_1_crafters = self.add_machine_group(
                Crafter(CRAFTER_RECIPES[module_type + "_module_1"], crafter_level, crafter_modules))
            crafters.append(module_1_crafters)
            self.connect(self.input_line, module_1_crafters, "circuit", "red_circuit")
            self.connect(module_1_crafters, self.module_line)
            module_2_crafters = self.add_machine_group(
                Crafter(CRAFTER_RECIPES[module_type + "_module_2"], crafter_level, crafter_modules))
            crafters.append(module_2_crafters)
            self.connect(self.input_line, module_2_crafters, "red_circuit", "blue_circuit")
            self.connect(self.module_line, module_2_crafters, module_type + "_module_1")
            self.connect(module_2_crafters, self.module_line)
            module_3_crafters = self.add_machine_group(
                Crafter(CRAFTER_RECIPES[module_type + "_module_3"], crafter_level, crafter_modules))
            crafters.append(module_3_crafters)
            self.connect(self.input_line, module_3_crafters, "red_circuit", "blue_circuit")
            self.connect(self.module_line, module_3_crafters, module_type + "_module_2")
            self.connect(module_3_crafters, self.module_line)

            self.connect(self.module_line, self.output_line, *(f"{module_type}_module_{i}" for i in range(1, 4)))
            self.crafters[module_type] = crafters

    def print_info(self, results: FullAnalysisResults):
        rates = results.max_rates
        print("-------- module factory info")
        if not self.crafters:
            print("no module types specified")
            return
        for module_type in self.crafters.keys():
            crafters_1, crafters_2, crafters_3 = self.crafters[module_type]
            print(f" - {module_type} modules")
            print(f"circuit rate for module 1: {crafters_1.input_rate(rates, 'circuit'):.2f}")
            print(f"red circuit rate for module 1: {crafters_1.input_rate(rates, 'red_circuit'):.2f}")
            print(f"module 1 rate for module 2: {crafters_2.input_rate(rates, module_type + '_module_1'):.2f}")
            print(f"red circuit rate for module 2: {crafters_2.input_rate(rates, 'red_circuit'):.2f}")
            print(f"blue circuit rate for module 2: {crafters_2.input_rate(rates, 'blue_circuit'):.2f}")
            print(f"module 2 rate for module 3: {crafters_3.input_rate(rates, module_type + '_module_2'):.2f}")
            print(f"red circuit rate for module 3: {crafters_3.input_rate(rates, 'red_circuit'):.2f}")
            print(f"blue circuit rate for module 3: {crafters_3.input_rate(rates, 'blue_circuit'):.2f}")

