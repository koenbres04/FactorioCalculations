from facalc.factories import SubFactory, OutputPoint, Buffer, FullAnalysisResults, new_factory
from facalc.factorio_machines import Crafter, CRAFTER_RECIPES, Module


class CircuitFactory(SubFactory):
    def __init__(
            self,
            parent: SubFactory, iron_plate_line: Buffer, copper_plate_line: Buffer, chemical_line: Buffer,
            crafter_level,
            crafter_modules: tuple[Module, ...] = (),
            output_caps: dict[str, float] | None = None
    ):
        super().__init__(parent)
        self.output_line = self.add_buffer("circuit factory output", output_caps)
        circuit_line = self.add_buffer("circuit factory line")

        # add circuit crafters
        self.circuit_wire_crafters = self.add_machine_group(
            Crafter(CRAFTER_RECIPES["copper_wire"], crafter_level, crafter_modules))
        self.connect(copper_plate_line, self.circuit_wire_crafters, "copper_plate")
        self.circuit_crafters = self.add_machine_group(
            Crafter(CRAFTER_RECIPES["circuit"], crafter_level, crafter_modules))
        self.connect(self.circuit_wire_crafters, self.circuit_crafters, "copper_wire")
        self.connect(iron_plate_line, self.circuit_crafters, "iron_plate")
        self.connect(self.circuit_crafters, circuit_line, "circuit")

        # add red circuit crafters
        self.red_circuit_crafters = self.add_machine_group(
            Crafter(CRAFTER_RECIPES["red_circuit"], crafter_level, crafter_modules)
        )
        self.red_circuit_wire_crafters = self.add_machine_group(
            Crafter(CRAFTER_RECIPES["copper_wire"], crafter_level, crafter_modules))
        self.connect(copper_plate_line, self.red_circuit_wire_crafters, "copper_plate")
        self.connect(self.red_circuit_wire_crafters, self.red_circuit_crafters, "copper_wire")
        self.connect(circuit_line, self.red_circuit_crafters, "circuit")
        self.connect(chemical_line, self.red_circuit_crafters, "plastic")
        self.connect(self.red_circuit_crafters, circuit_line, "red_circuit")

        # add blue circuit crafters
        self.blue_circuit_crafters = self.add_machine_group(
            Crafter(CRAFTER_RECIPES["blue_circuit"], crafter_level, crafter_modules)
        )
        self.connect(chemical_line, self.blue_circuit_crafters, "sulfuric_acid")
        self.connect(circuit_line, self.blue_circuit_crafters, "circuit")
        self.connect(circuit_line, self.blue_circuit_crafters, "red_circuit")
        self.connect(self.blue_circuit_crafters, self.output_line, "blue_circuit")

        # output other circuits
        self.connect(circuit_line, self.output_line, "circuit")
        self.connect(circuit_line, self.output_line, "red_circuit")

    def print_info(self, results: FullAnalysisResults):
        rates = results.max_rates
        print(f"wire rate for circuit crafters: {self.circuit_wire_crafters.output_rate(rates, 'copper_wire'):.2f}")
        print(f"iron_plate rate for circuit crafters: {self.circuit_crafters.input_rate(rates, 'iron_plate'):.2f}")
        print(f"circuit rate for red circuit crafters: {self.red_circuit_crafters.input_rate(rates, 'circuit'):.2f}")
        print(f"plastic rate for red circuit crafters: {self.red_circuit_crafters.input_rate(rates, 'plastic'):.2f}")
        print(f"wire rate for red circuit crafters: {self.red_circuit_wire_crafters.output_rate(rates, 'copper_wire'):.2f}")
        print(f"circuit rate for blue circuit crafters: {self.blue_circuit_crafters.input_rate(rates, 'circuit'):.2f}")
        self.print_machines(rates)
        self.print_buffer_throughput(rates)


def main():
    # test case parameters
    crafter_modules = (Module.PRODUCTION_MODULE_1,) * 3
    crafter_level = 2
    output_cap = {
        "circuit": 15,
    }
    iron_plate_rate = 30
    copper_plate_rate = 30
    plastic_rate = 15

    # crate test factory
    factory = new_factory()
    iron_plate_source = factory.add_source("iron_plate", iron_plate_rate)
    iron_line = factory.add_buffer("test iron plate line")
    factory.connect(iron_plate_source, iron_line, "iron_plate")

    copper_plate_source = factory.add_source("copper_plate", copper_plate_rate)
    copper_line = factory.add_buffer("test copper plate line")
    factory.connect(copper_plate_source, copper_line, "copper_plate")

    plastic_source = factory.add_source("plastic", plastic_rate)
    sulfuric_acid_source = factory.add_source("sulfuric_acid")
    chemical_line = factory.add_buffer("test chemical line")
    factory.connect(plastic_source, chemical_line, "plastic")
    factory.connect(sulfuric_acid_source, chemical_line, "sulfuric_acid")

    circuit_factory = CircuitFactory(
        factory, iron_line, copper_line, chemical_line,
        crafter_modules= crafter_modules,
        crafter_level = crafter_level,
        output_caps= output_cap,
    )

    factory.add_output_point(OutputPoint(circuit_factory.output_line, "circuit"))
    factory.add_output_point(OutputPoint(circuit_factory.output_line, "red_circuit"))
    factory.add_output_point(OutputPoint(circuit_factory.output_line, "blue_circuit"))

    output = factory.analyse()
    print(output.display_full())
    print("")
    circuit_factory.print_info(output)

if __name__ == '__main__':
    main()