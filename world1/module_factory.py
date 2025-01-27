from facalc.factories import Factory, OutputPoint, Buffer, SingleAnalysisResults, FullAnalysisResults, MachineGroup
from facalc.factorio_machines import Crafter, CRAFTER_RECIPES, Module
from typing import Iterable


class ModuleFactory:
    def __init__(
            self,
            factory: Factory, circuit_line: Buffer,
            module_types: Iterable[str],
            crafter_level,
            crafter_modules: tuple[Module, ...] = (),
            input_caps: dict[str, float] | None = None,
            output_caps: dict[str, float] | None = None,
    ):
        self.input_line = factory.add_buffer("module factory input", input_caps)
        factory.connect(circuit_line, self.input_line, "circuit", "red_circuit", "blue_circuit")
        self.module_line = factory.add_buffer("module factory line")
        self.output_line = factory.add_buffer("module factory output", output_caps)
        self.crafters: dict[str, list[MachineGroup]] = {}
        for module_type in module_types:
            crafters = []
            module_1_crafters = factory.add_machine_group(
                Crafter(CRAFTER_RECIPES[module_type + "_module_1"], crafter_level, crafter_modules))
            crafters.append(module_1_crafters)
            factory.connect(self.input_line, module_1_crafters, "circuit", "red_circuit")
            factory.connect(module_1_crafters, self.module_line)
            module_2_crafters = factory.add_machine_group(
                Crafter(CRAFTER_RECIPES[module_type + "_module_2"], crafter_level, crafter_modules))
            crafters.append(module_2_crafters)
            factory.connect(self.input_line, module_2_crafters, "red_circuit", "blue_circuit")
            factory.connect(self.module_line, module_2_crafters, module_type + "_module_1")
            factory.connect(module_2_crafters, self.module_line)
            module_3_crafters = factory.add_machine_group(
                Crafter(CRAFTER_RECIPES[module_type + "_module_3"], crafter_level, crafter_modules))
            crafters.append(module_3_crafters)
            factory.connect(self.input_line, module_3_crafters, "red_circuit", "blue_circuit")
            factory.connect(self.module_line, module_3_crafters, module_type + "_module_2")
            factory.connect(module_3_crafters, self.module_line)

            factory.connect(self.module_line, self.output_line, *(f"{module_type}_module_{i}" for i in range(1, 4)))
            self.crafters[module_type] = crafters

    def print_info(self, results: FullAnalysisResults | SingleAnalysisResults):
        print("-------- module factory info")
        if not self.crafters:
            print("no module types specified")
            return
        for module_type in self.crafters.keys():
            crafters_1, crafters_2, crafters_3 = self.crafters[module_type]
            print(f" - {module_type} modules")
            print(f"circuit rate for module 1: {crafters_1.input_rate(results, 'circuit'):.2f}")
            print(f"red circuit rate for module 1: {crafters_1.input_rate(results, 'red_circuit'):.2f}")
            print(f"module 1 rate for module 2: {crafters_2.input_rate(results, module_type + '_module_1'):.2f}")
            print(f"red circuit rate for module 2: {crafters_2.input_rate(results, 'red_circuit'):.2f}")
            print(f"blue circuit rate for module 2: {crafters_2.input_rate(results, 'blue_circuit'):.2f}")
            print(f"module 2 rate for module 3: {crafters_3.input_rate(results, module_type + '_module_2'):.2f}")
            print(f"red circuit rate for module 3: {crafters_3.input_rate(results, 'red_circuit'):.2f}")
            print(f"blue circuit rate for module 3: {crafters_3.input_rate(results, 'blue_circuit'):.2f}")

