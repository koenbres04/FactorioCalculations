from __future__ import annotations
import numpy as np
import scipy
from dataclasses import dataclass
import abc
import weakref
from typing import Iterable, Any


class MachineType(abc.ABC):
    @property
    @abc.abstractmethod
    def input_rates(self) -> dict[str, float]:
        pass

    @property
    @abc.abstractmethod
    def output_rates(self) -> dict[str, float]:
        pass

    @abc.abstractmethod
    def display_info(self, rate: float) -> str:
        pass

    def get_cap_description(self) -> str:
        return "[no description]"


class FactoryNode(abc.ABC):
    def __init__(self):
        self._inputs: dict[str, list[weakref.ReferenceType[FactoryNode]]] = dict()
        self._outputs: dict[str, list[weakref.ReferenceType[FactoryNode]]] = dict()

    def add_input(self, node: FactoryNode, material: str):
        if material not in self._inputs:
            self._inputs[material] = []
        self._inputs[material].append(weakref.ref(node))

    def add_output(self, node: FactoryNode, material: str):
        if material not in self._outputs:
            self._outputs[material] = []
        self._outputs[material].append(weakref.ref(node))

    @property
    def input_materials(self):
        return self._inputs.keys()

    @property
    def output_materials(self):
        return self._outputs.keys()

    def inputs(self, material: str) -> Iterable[FactoryNode]:
        if material not in self._inputs:
            return tuple()
        return (x() for x in self._inputs[material])

    def outputs(self, material: str) -> Iterable[FactoryNode]:
        if material not in self._outputs:
            return tuple()
        return (x() for x in self._outputs[material])


class MachineGroup(FactoryNode):
    def __init__(self, machine_type: MachineType, machine_cap: float | None = None):
        self.machine_type = machine_type
        self.machine_cap = machine_cap
        super().__init__()

    def input_rate(self, result: SingleAnalysisResults | FullAnalysisResults, material: str):
        rate_dict = result.machine_rates if isinstance(result, SingleAnalysisResults) else result.max_machine_rates
        if self not in rate_dict:
            return 0.
        return rate_dict[self]*self.machine_type.input_rates[material]

    def output_rate(self, result: SingleAnalysisResults | FullAnalysisResults, material: str):
        rate_dict = result.machine_rates if isinstance(result, SingleAnalysisResults) else result.max_machine_rates
        if self not in rate_dict:
            return 0.
        return rate_dict[self]*self.machine_type.output_rates[material]


class Source(FactoryNode):
    def __init__(self, material: str, max_rate: float | None = None):
        self.material = material
        self.max_rate = max_rate
        super().__init__()

    def __str__(self):
        return f"a {self.material} source"


class Buffer(FactoryNode):
    def __init__(self, name: str, rate_caps: dict[str, float] | None):
        if rate_caps is None:
            rate_caps = dict()
        self.name = name
        self.rate_caps: dict[str, float] = rate_caps
        super().__init__()

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class OutputPoint:
    location: FactoryNode
    material: str
    max_rate: float | None = None


class Bottleneck(abc.ABC):
    @abc.abstractmethod
    def display(self) -> str:
        pass


@dataclass(frozen=True)
class SourceRateCap(Bottleneck):
    source: Source

    def display(self) -> str:
        return f"maximum rate of a {self.source.material} source"


@dataclass(frozen=True)
class MachineRateCap(Bottleneck):
    machine_group: MachineGroup

    def display(self) -> str:
        return self.machine_group.machine_type.get_cap_description()


@dataclass(frozen=True)
class BufferRateCap(Bottleneck):
    buffer: Buffer
    material: str

    def display(self) -> str:
        return f"{self.material} rate cap of buffer '{self.buffer.name}'"


@dataclass(frozen=True)
class SingleAnalysisResults:
    result_rate: float
    source_rates: dict[Source, float]
    buffer_throughput: dict[tuple[Buffer, str], float]
    machine_rates: dict[MachineGroup, float]
    bottlenecks: tuple[tuple[float, Bottleneck], ...]

    @property
    def source_costs(self) -> dict[Source, float]:
        return {source: source_rate/self.result_rate for source, source_rate in self.source_rates.items()}

    def display(self) -> str:
        lines = [f"final rate: {self.display_one_line()}"]
        if len(self.bottlenecks) >= 2:
            lines.append(" -- bottlenecks -- ")
            for i in range(len(self.bottlenecks)):
                if i != len(self.bottlenecks)-1:
                    lines.append(f"{self.bottlenecks[i+1][0]:.2f} by removing {self.bottlenecks[i][1].display()}")
                else:
                    lines.append(f"infinite by removing {self.bottlenecks[i][1].display()}")
        if self.source_rates:
            lines.append(" -- cost per unit material -- ")
            for source, cost in self.source_costs.items():
                lines.append(f"{source.material}: {cost:.2f}")
            lines.append(" -- sources -- ")
            for source, rate in self.source_rates.items():
                lines.append(f"{source.material}: {rate:.2f}/s")
        if self.buffer_throughput:
            lines.append(" -- buffer throughput -- ")
            throughput_by_buffer: dict[Buffer, dict[str, float]] = dict()
            for (buffer, material), rate in self.buffer_throughput.items():
                if not buffer in throughput_by_buffer:
                    throughput_by_buffer[buffer] = dict()
                throughput_by_buffer[buffer][material] = rate
            for buffer, throughput_dict in throughput_by_buffer.items():
                lines.append(buffer.name + ":")
                for material, rate in throughput_dict.items():
                    lines.append(f"- {material}: {rate:.2f}/s")
        if self.machine_rates:
            lines.append(" -- machines -- ")
            for machine_group, rate in self.machine_rates.items():
                lines.append(machine_group.machine_type.display_info(rate))
        return "\n".join(lines)

    def display_one_line(self) -> str:
        if len(self.bottlenecks) == 0:
            return f"infinite"
        elif len(self.bottlenecks) == 1:
            return f"{self.result_rate:.2f}/s bottlenecked by {self.bottlenecks[0][1].display()} for ever"
        else:
            bottleneck_factor = self.bottlenecks[1][0]/self.bottlenecks[0][0]
            return (f"{self.result_rate:.2f}/s bottlenecked by {self.bottlenecks[0][1].display()} "
                    f"for another {bottleneck_factor:.1f}x")


def update_sup_dict(a: dict[Any, float], b: dict[Any, float]):
    for key, value in b.items():
        if key not in a:
            a[key] = 0.
        a[key] = max(a[key], value)


@dataclass(frozen=True)
class FullAnalysisResults:
    max_source_rates: dict[Source, float]
    max_buffer_throughput: dict[tuple[Buffer, str], float]
    max_machine_rates: dict[MachineGroup, float]
    single_results: dict[OutputPoint, SingleAnalysisResults]

    @classmethod
    def from_single_analyses(cls, results: Iterable[tuple[OutputPoint, SingleAnalysisResults]]) -> FullAnalysisResults:
        max_source_rates = dict()
        max_buffer_throughput = dict()
        max_machine_rates = dict()
        single_results = dict()
        for output_point, result in results:
            update_sup_dict(max_source_rates, result.source_rates)
            update_sup_dict(max_buffer_throughput, result.buffer_throughput)
            update_sup_dict(max_machine_rates, result.machine_rates)
            single_results[output_point] = result
        return FullAnalysisResults(max_source_rates, max_buffer_throughput, max_machine_rates, single_results)

    def display(self) -> str:
        lines = []
        if self.max_source_rates:
            lines.append(" -- sources -- ")
            for source, rate in self.max_source_rates.items():
                lines.append(f"{source.material}: {rate:.2f}/s")
        if self.max_buffer_throughput:
            lines.append(" -- buffer throughput -- ")
            throughput_by_buffer: dict[Buffer, dict[str, float]] = dict()
            for (buffer, material), rate in self.max_buffer_throughput.items():
                if not buffer in throughput_by_buffer:
                    throughput_by_buffer[buffer] = dict()
                throughput_by_buffer[buffer][material] = rate
            for buffer, throughput_dict in throughput_by_buffer.items():
                lines.append(buffer.name + ":")
                for material, rate in throughput_dict.items():
                    lines.append(f"- {material}: {rate:.2f}/s")
        if self.max_machine_rates:
            lines.append(" -- machines -- ")
            for machine_group, rate in self.max_machine_rates.items():
                lines.append(machine_group.machine_type.display_info(rate))
        lines.append(" -- single output rates -- ")
        for output_point, result in self.single_results.items():
            lines.append(f"{output_point.material}: {result.display_one_line()}")
        return "\n".join(lines)

    def display_full(self) -> str:
        lines = []
        for output_point, sub_result in self.single_results.items():
            lines.append(f"-------- {output_point.material}")
            lines.append(sub_result.display())
            lines.append("")
        lines.append("-------- full analysis")
        lines.append(self.display())
        return "\n".join(lines)


class FactoryAnalysisException(Exception):
    pass


class Factory:
    def __init__(self):
        self.nodes: list[FactoryNode] = []
        self.output_points: list[OutputPoint] = []

    def add_buffer(self, name: str, rate_caps: dict[str, float] | None = None) -> Buffer:
        if rate_caps is None:
            rate_caps = dict()
        buffer = Buffer(name, rate_caps)
        self.nodes.append(buffer)
        return buffer

    def add_source(self, material: str, max_rate: float | None = None):
        source = Source(material, max_rate)
        self.nodes.append(source)
        return source

    def add_machine_group(self, machine_type: MachineType, machine_cap: float | None = None):
        machine_group = MachineGroup(machine_type, machine_cap)
        self.nodes.append(machine_group)
        return machine_group

    def add_output_point(self, output_point: OutputPoint):
        self.output_points.append(output_point)

    @staticmethod
    def connect(frm: FactoryNode, to: FactoryNode, *materials: str):
        """
        Connects the output of node 'frm' to the input of node 'to' for the specified materials.
        If no materials are specified, one will be auto-detected when there is only one choice

        :param frm: the source of the connection
        :param to: the target of the connection
        :param materials: materials to connect. If none specified, one will be auto-detected when there is only one choice
        """
        if isinstance(to, Source):
            raise ValueError("Cannot connect anything towards a source.")
        for material in materials:
            if isinstance(frm, Source) and material != frm.material:
                raise ValueError("Cannot connect from a source with a different material than the source material.")
            if isinstance(frm, MachineGroup) and material in frm.output_materials:
                raise ValueError("Per material a machine group can have only one output")

        if not materials and isinstance(frm, Source):
            materials = (frm.material,)
        if not materials and isinstance(frm, MachineGroup) and len(frm.machine_type.output_rates.keys()) == 1:
            materials = (list(frm.machine_type.output_rates.keys())[0],)
        if not materials and isinstance(to, MachineGroup) and len(frm.machine_type.input_rates.keys()) == 1:
            materials = (list(frm.machine_type.input_rates.keys())[0],)
        if not materials:
            raise ValueError("Unable to auto-detect material.")
        for material in materials:
            to.add_input(frm, material)
            frm.add_output(to, material)

    @staticmethod
    def search_nodes(output_point: OutputPoint):
        sources: list[Source] = []
        machine_groups: list[MachineGroup] = []
        buffer_lines: list[tuple[Buffer, str]] = []
        buffer_transfers: list[tuple[Buffer | Source, Buffer, str]] = []
        to_search: list[tuple[FactoryNode, str | None]] = [
            (output_point.location, output_point.material) if isinstance(output_point.location, Buffer)
            else (output_point.location, None)
        ]
        searched = to_search.copy()
        while to_search:
            new_to_search: list[tuple[FactoryNode, str | None]] = []
            for node, material in to_search:
                if isinstance(node, MachineGroup):
                    machine_groups.append(node)
                    for new_material in node.input_materials:
                        for new_node in node.inputs(new_material):
                            new_tuple = (new_node, new_material) if isinstance(new_node, Buffer) else (new_node, None)
                            if new_tuple not in searched:
                                new_to_search.append(new_tuple)
                                searched.append(new_tuple)
                elif isinstance(node, Source):
                    sources.append(node)
                elif isinstance(node, Buffer):
                    buffer_lines.append((node, material))
                    for new_node in node.inputs(material):
                        new_tuple = (new_node, material) if isinstance(new_node, Buffer) else (new_node, None)
                        if new_tuple not in searched:
                            new_to_search.append(new_tuple)
                            searched.append(new_tuple)
                        if isinstance(new_node, Buffer | Source):
                            buffer_transfers.append((new_node, node, material))
            to_search = new_to_search
        return sources, machine_groups, buffer_lines, buffer_transfers

    @staticmethod
    def _analyse(output_point: OutputPoint) -> SingleAnalysisResults:
        if isinstance(output_point.location, Source):
            raise FactoryAnalysisException("Taking output directly from a source is not supported.")
        if (isinstance(output_point.location, MachineGroup) and
                output_point.material in output_point.location.output_materials):
            raise FactoryAnalysisException("Taking output from a machine group which already has "
                                           "output is not supported")
        # find relevant nodes
        (relevant_sources, relevant_machine_groups,
         relevant_buffer_lines, relevant_buffer_transfers) = Factory.search_nodes(output_point)

        # set up the linear programming problem
        num_variables = 1+len(relevant_machine_groups)+len(relevant_buffer_transfers)
        equalities: list[tuple[np.ndarray, float]] = []
        inequalities: list[tuple[np.ndarray, float, Bottleneck]] = []
        # add inequalities for rate cap on machine groups
        for i, machine_group in enumerate(relevant_machine_groups):
            if machine_group.machine_cap is None:
                continue
            coefficients = np.zeros(num_variables, float)
            coefficients[1+i] = 1
            inequalities.append((
                coefficients,
                machine_group.machine_cap,
                MachineRateCap(machine_group)
            ))
        # add equalities for connections between machine groups
        for i, machine_group in enumerate(relevant_machine_groups):
            for material in machine_group.input_materials:
                for node in machine_group.inputs(material):
                    if not isinstance(node, MachineGroup):
                        continue
                    equation = np.zeros(num_variables, float)
                    equation[1+i] = machine_group.machine_type.input_rates[material]
                    input_index = relevant_machine_groups.index(node)
                    equation[1+input_index] = -node.machine_type.output_rates[material]
                    equalities.append((equation, 0.))
        # add inequalities on source output
        source_rate_vectors = {}
        for source in relevant_sources:
            source_rate_vector = np.zeros(num_variables, float)
            for node in source.outputs(source.material):
                if isinstance(node, MachineGroup):
                    if not node in relevant_machine_groups:
                        continue
                    index = relevant_machine_groups.index(node)
                    source_rate_vector[1+index] = node.machine_type.input_rates[source.material]
                elif isinstance(node, Buffer):
                    if not (source, node, source.material) in relevant_buffer_transfers:
                        continue
                    index = relevant_buffer_transfers.index((source, node, source.material))
                    source_rate_vector[1+len(relevant_machine_groups)+index] = 1.
            source_rate_vectors[source] = source_rate_vector
            if source.max_rate is not None:
                inequalities.append((
                    source_rate_vector,
                    source.max_rate,
                    SourceRateCap(source)
                ))
        # add equalities for buffer in and out and inequalities for source input caps
        buffer_throughput_vectors = {}
        for buffer, material in relevant_buffer_lines:
            # determine vectors for input and output and require they are equal
            input_vector = np.zeros(num_variables, float)
            for node in buffer.inputs(material):
                if isinstance(node, Buffer | Source):
                    index = 1+len(relevant_machine_groups)+relevant_buffer_transfers.index((node, buffer, material))
                    input_vector[index] = 1.
                elif isinstance(node, MachineGroup):
                    index = 1+relevant_machine_groups.index(node)
                    input_vector[index] = node.machine_type.output_rates[material]
            output_vector = np.zeros(num_variables, float)
            for node in buffer.outputs(material):
                if isinstance(node, Buffer):
                    if (node, material) not in relevant_buffer_lines:
                        continue
                    index = 1+len(relevant_machine_groups)+relevant_buffer_transfers.index((buffer, node, material))
                    output_vector[index] = 1.
                elif isinstance(node, MachineGroup):
                    if node not in relevant_machine_groups:
                        continue
                    index = 1+relevant_machine_groups.index(node)
                    output_vector[index] = node.machine_type.input_rates[material]
            if output_point.location is buffer and output_point.material == material:
                output_vector[0] = 1
            equalities.append((input_vector-output_vector, 0.))
            buffer_throughput_vectors[(buffer, material)] = input_vector
            # add input cap
            if material in buffer.rate_caps:
                inequalities.append((
                    input_vector,
                    buffer.rate_caps[material],
                    BufferRateCap(buffer, material)
                ))
        # add relation between output and machine group if the output is directly from a machine
        if isinstance(output_point.location, MachineGroup):
            equation = np.zeros(num_variables, float)
            equation[0] = -1
            machine_index = relevant_machine_groups.index(output_point.location)
            equation[1+machine_index] = output_point.location.machine_type.output_rates[output_point.material]
            equalities.append((equation, 0))

        # solve and store result
        to_minimize_vector = np.zeros(num_variables, float)
        to_minimize_vector[0] = -1
        if inequalities:
            inequalities_matrix = np.stack([coefficients for coefficients, bounds, description in inequalities])
            inequalities_bounds = np.array([bounds for coefficients, bounds, description in inequalities], dtype=float)
        else:
            inequalities_matrix = np.zeros((0, num_variables), float)
            inequalities_bounds = np.zeros(0, float)
        if equalities:
            equalities_matrix = np.stack([coefficients for coefficients, value in equalities])
            equalities_values = np.array([value for coefficients, value in equalities], dtype=float)
        else:
            equalities_matrix = np.zeros((0, num_variables), float)
            equalities_values = np.zeros(0, float)
        # noinspection PyDeprecation
        result = scipy.optimize.linprog(
            to_minimize_vector, inequalities_matrix, inequalities_bounds, equalities_matrix, equalities_values
        )
        # check for infinite or invalid results
        if result.status == 3:
            return SingleAnalysisResults(
                float("inf"),
                {source: float("inf") for source in relevant_sources},
                {x: float("inf") for x in relevant_buffer_lines},
                {machine_group: float("inf") for machine_group in relevant_machine_groups},
                ()
            )
        elif result.status != 0:
            raise FactoryAnalysisException("Failed to solve the linear programming problem somehow.")
        result_1_rate = result.x[0]
        source_rates = {source: v.dot(result.x) for source, v in source_rate_vectors.items()}
        bottlenecks_indices = [i for i, x in enumerate(result.slack) if x < 1e-9]
        buffer_throughput = {key: v.dot(result.x) for key, v in buffer_throughput_vectors.items()}
        machine_rates = {machine_group: result.x[1+i] for i, machine_group in enumerate(relevant_machine_groups)}

        # calculate bottleneck results
        current_rate = result_1_rate
        bottlenecks = []
        while bottlenecks_indices:
            bottleneck_index = bottlenecks_indices[0]
            bottlenecks.append((current_rate, inequalities[bottleneck_index][2]))

            # solve the system again but with one less inequalties
            inequalities.pop(bottleneck_index)
            if inequalities:
                inequalities_matrix = np.stack([coefficients for coefficients, bounds, description in inequalities])
                inequalities_bounds = np.array([bounds for coefficients, bounds, description in inequalities], dtype=float)
            else:
                inequalities_matrix = np.zeros((0, num_variables), float)
                inequalities_bounds = np.zeros(0, float)
            # noinspection PyDeprecation
            result = scipy.optimize.linprog(
                to_minimize_vector, inequalities_matrix, inequalities_bounds, equalities_matrix, equalities_values
            )
            if result.status not in (0, 3):
                raise FactoryAnalysisException("Failed to solve the linear programming problem somehow.")
            elif result.status == 3:
                break
            current_rate = result.x[0]
            bottlenecks_indices = [i for i, x in enumerate(result.slack) if x < 1e-9]
        return SingleAnalysisResults(result_1_rate, source_rates, buffer_throughput, machine_rates, tuple(bottlenecks))

    def analyse(self, output_point) -> SingleAnalysisResults:
        result = self._analyse(output_point)
        source_rates_items = list(result.source_rates.items())
        source_rates_items.sort(key=lambda x: self.nodes.index(x[0]))
        buffer_throughput_items = list(result.buffer_throughput.items())
        buffer_throughput_items.sort(key=lambda x: self.nodes.index(x[0][0]))
        machine_rates_items = list(result.machine_rates.items())
        machine_rates_items.sort(key=lambda x: self.nodes.index(x[0]))
        return SingleAnalysisResults(
            result.result_rate,
            {x: y for x, y in source_rates_items},
            {x: y for x, y in buffer_throughput_items},
            {x: y for x, y in machine_rates_items},
            result.bottlenecks
        )


    def full_analyse(self, print_progress: bool = False) -> FullAnalysisResults:
        sub_results = []
        for i, output_point in enumerate(self.output_points):
            if print_progress:
                print(f"analysing output point {i+1}/{len(self.output_points)}", end="\r")
            sub_results.append((output_point, self.analyse(output_point)))
        if print_progress:
            print("done!")

        result = FullAnalysisResults.from_single_analyses(sub_results)
        source_rates_items = list(result.max_source_rates.items())
        source_rates_items.sort(key=lambda x: self.nodes.index(x[0]))
        buffer_throughput_items = list(result.max_buffer_throughput.items())
        buffer_throughput_items.sort(key=lambda x: self.nodes.index(x[0][0]))
        machine_rates_items = list(result.max_machine_rates.items())
        machine_rates_items.sort(key=lambda x: self.nodes.index(x[0]))
        return FullAnalysisResults(
            {x: y for x, y in source_rates_items},
            {x: y for x, y in buffer_throughput_items},
            {x: y for x, y in machine_rates_items},
            result.single_results
        )

