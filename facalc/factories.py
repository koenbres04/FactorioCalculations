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

    @property
    def input_materials(self):
        return self.input_rates.keys()

    @property
    def output_materials(self):
        return self.output_rates.keys()

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

    def input_rate(self, rates: FactoryRates, material: str):
        return rates[self]*self.machine_type.input_rates[material]

    def output_rate(self, rates: FactoryRates, material: str):
        return rates[self]*self.machine_type.output_rates[material]

    @property
    def has_unconnected_inputs(self) -> bool:
        return any(
            material not in self.input_materials for material in self.machine_type.input_rates.keys()
        )

    @property
    def has_unconnected_outputs(self) -> bool:
        return any(
            material not in self.output_materials for material in self.machine_type.output_rates.keys()
        )


class Source(FactoryNode):
    def __init__(self, material: str, max_rate: float | None = None):
        self.material = material
        self.max_rate = max_rate
        super().__init__()

    def __str__(self):
        return f"a {self.material} source"


class TrashPoint(FactoryNode):
    def __init__(self, location: FactoryNode, material: str, max_rate: float | None = None, weight: float = 1.):
        self.location = location
        self.material = material
        self.max_rate = max_rate
        self.weight = weight
        super().__init__()

    def __str__(self):
        return f"a {self.material} trash point"


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

    def __str__(self):
        return f"a {self.material} output point at {self.location}"


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
class OutputPointRateCap(Bottleneck):
    output_point: OutputPoint

    def display(self) -> str:
        return f"output point rate cap of {str(self.output_point)}"


@dataclass(frozen=True)
class TrashPointRateCap(Bottleneck):
    trash_point: TrashPoint

    def display(self) -> str:
        return f"trash point rate cap of {str(self.trash_point)}"


def update_sup_dict(a: dict[Any, float], b: dict[Any, float]):
    for key, value in b.items():
        if key not in a:
            a[key] = 0.
        a[key] = max(a[key], value)


@dataclass(frozen=True)
class FactoryRates:
    source_rates: dict[Source, float]
    buffer_throughput: dict[tuple[Buffer, str], float]
    machine_rates: dict[MachineGroup, float]
    trash_rates: dict[TrashPoint, float]

    def __getitem__(self, item: Source | tuple[Buffer, str] | MachineGroup | TrashPoint) -> float:
        if isinstance(item, Source) and item in self.source_rates:
            return self.source_rates[item]
        if isinstance(item, tuple) and item in self.buffer_throughput:
            return self.buffer_throughput[item]
        if isinstance(item, MachineGroup) and item in self.machine_rates:
            return self.machine_rates[item]
        if isinstance(item, TrashPoint) and item in self.trash_rates:
            return self.trash_rates[item]
        return 0.

    def get_throughputs(self, buffer: Buffer) -> tuple[str, float]:
        for (other_buffer, material), throughput in self.buffer_throughput.items():
            if buffer is other_buffer:
                yield material, throughput

    def update_sup(self, other: FactoryRates):
        update_sup_dict(self.source_rates, other.source_rates)
        update_sup_dict(self.buffer_throughput, other.buffer_throughput)
        update_sup_dict(self.machine_rates, other.machine_rates)
        update_sup_dict(self.trash_rates, other.trash_rates)



@dataclass(frozen=True)
class SingleAnalysisResults:
    result_rate: float
    rates: FactoryRates
    bottlenecks: tuple[tuple[float, Bottleneck], ...]

    @property
    def source_costs(self) -> dict[Source, float]:
        return {source: source_rate/self.result_rate for source, source_rate in self.rates.source_rates.items()
                if self.result_rate != 0. and source_rate != float("inf")}

    def display(self, bottlenecks: bool = True, trash_rates: bool = False, source_costs: bool = False,
                source_rates: bool = False) -> str:
        lines = [f"final rate: {self.display_one_line()}"]
        if bottlenecks and len(self.bottlenecks) >= 2:
            lines.append(" -- bottlenecks -- ")
            for i in range(len(self.bottlenecks)):
                if i != len(self.bottlenecks)-1:
                    lines.append(f"{self.bottlenecks[i+1][0]:.2f} by removing {self.bottlenecks[i][1].display()}")
                else:
                    lines.append(f"infinite by removing {self.bottlenecks[i][1].display()}")
        if trash_rates and self.rates.trash_rates:
            lines.append(" -- trash rates -- ")
            for trash_point, rate in self.rates.trash_rates.items():
                lines.append(f"{trash_point.material}: {rate:.2f}/s")
        if source_costs and self.source_costs:
            lines.append(" -- cost per unit material -- ")
            for source, cost in self.source_costs.items():
                lines.append(f"{source.material}: {cost:.2f}")
        if source_rates and self.rates.source_rates:
            lines.append(" -- sources -- ")
            for source, rate in self.rates.source_rates.items():
                lines.append(f"{source.material}: {rate:.2f}/s")
        return "\n".join(lines)

    def display_one_line(self) -> str:
        if self.result_rate < 1e-9:
            return "0.00/s"
        elif len(self.bottlenecks) == 0:
            return f"infinite"
        elif len(self.bottlenecks) == 1:
            return f"{self.result_rate:.2f}/s bottlenecked by {self.bottlenecks[0][1].display()} for ever"
        else:
            bottleneck_factor = self.bottlenecks[1][0]/self.bottlenecks[0][0]
            return (f"{self.result_rate:.2f}/s bottlenecked by {self.bottlenecks[0][1].display()} "
                    f"for another {bottleneck_factor:.1f}x")


@dataclass(frozen=True)
class FullAnalysisResults:
    max_rates: FactoryRates
    single_results: dict[OutputPoint, SingleAnalysisResults]

    @classmethod
    def from_single_analyses(cls, results: Iterable[tuple[OutputPoint, SingleAnalysisResults]]) -> FullAnalysisResults:
        max_rates = FactoryRates({}, {}, {}, {})
        single_results = {}
        for output_point, result in results:
            max_rates.update_sup(result.rates)
            single_results[output_point] = result
        return FullAnalysisResults(max_rates, single_results)

    def display(self) -> str:
        lines = [" -- single output rates -- "]
        for output_point, result in self.single_results.items():
            lines.append(f"{output_point.material}: {result.display_one_line()}")
        return "\n".join(lines)


class FactoryAnalysisException(Exception):
    pass


class _Factory:
    def __init__(self):
        self.nodes: list[FactoryNode] = []

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

    def add_trash_point(self, location: FactoryNode, material: str, weight: float = 1., max_rate: float | None = None) -> TrashPoint:
        if isinstance(location, Source):
            raise ValueError("Cannot attach a trash point directly to a source.")
        trash_point = TrashPoint(location, material, max_rate, weight)
        self.connect(location, trash_point, material)
        self.nodes.append(trash_point)
        return trash_point

    @staticmethod
    def connect(frm: FactoryNode, to: FactoryNode, *materials: str):
        """
        Connects the output of node 'frm' to the input of node 'to' for the specified materials.
        If no materials are specified, one will be auto-detected when there is only one choice

        :param frm: the source of the connection
        :param to: the target of the connection
        :param materials: materials to connect. If none specified, one will be auto-detected when there is only one choice
        """
        if isinstance(frm, TrashPoint) or (isinstance(to, TrashPoint) and to.input_materials):
            raise ValueError("Cannot make any additional connections to trash points.")
        if isinstance(to, Source):
            raise ValueError("Cannot connect anything towards a source.")
        for material in materials:
            if isinstance(frm, Source) and material != frm.material:
                raise ValueError("Cannot connect from a source with a different material than the source material.")
            if isinstance(frm, MachineGroup):
                if material in frm.output_materials:
                    raise ValueError("Per material a machine group can have only one output")
                if material not in frm.machine_type.output_materials:
                    raise ValueError(f"A machine of this type cannot have '{material}' as an output.")
            if isinstance(to, MachineGroup):
                if material in to.input_materials:
                    raise ValueError("Per material a machine group can have only one input")
                if material not in to.machine_type.input_materials:
                    raise ValueError(f"A machine of this type cannot have '{material}' as an input.")

        if not materials and isinstance(frm, Source):
            materials = (frm.material,)
        if not materials and isinstance(frm, MachineGroup) and len(frm.machine_type.output_rates.keys()) == 1:
            materials = (list(frm.machine_type.output_rates.keys())[0],)
        if not materials and isinstance(to, MachineGroup) and len(to.machine_type.input_rates.keys()) == 1:
            materials = (list(to.machine_type.input_rates.keys())[0],)
        if not materials:
            raise ValueError("Unable to auto-detect material.")
        for material in materials:
            to.add_input(frm, material)
            frm.add_output(to, material)

    @staticmethod
    def search_nodes(location: FactoryNode, material: str, hit_search: tuple[set, ...] | None = None):
        sources: list[Source] = []
        machine_groups: list[MachineGroup] = []
        buffer_lines: list[tuple[Buffer, str]] = []
        buffer_transfers: list[tuple[Buffer | Source, Buffer, str]] = []
        to_search: list[tuple[FactoryNode, str | None]] = [
            (location, material) if isinstance(location, Buffer)
            else (location, None)
        ]
        if hit_search is not None:
            (hit_sources, hit_machine_groups, hit_buffer_lines) = hit_search
        else:
            (hit_sources, hit_machine_groups, hit_buffer_lines) = (set() for _ in range(3))
        searched = to_search.copy()
        did_hit = False
        while to_search:
            new_to_search: list[tuple[FactoryNode, str | None]] = []
            for node, material in to_search:
                if isinstance(node, MachineGroup):
                    if node in hit_machine_groups:
                        did_hit = True
                        continue
                    machine_groups.append(node)
                    for new_material in node.input_materials:
                        for new_node in node.inputs(new_material):
                            new_tuple = (new_node, new_material) if isinstance(new_node, Buffer) else (new_node, None)
                            if new_tuple not in searched:
                                new_to_search.append(new_tuple)
                                searched.append(new_tuple)
                elif isinstance(node, Source):
                    if node in hit_sources:
                        did_hit = True
                        continue
                    sources.append(node)
                elif isinstance(node, Buffer):
                    if (node, material) in hit_buffer_lines:
                        did_hit = True
                        continue
                    buffer_lines.append((node, material))
                    for new_node in node.inputs(material):
                        new_tuple = (new_node, material) if isinstance(new_node, Buffer) else (new_node, None)
                        if new_tuple not in searched:
                            new_to_search.append(new_tuple)
                            searched.append(new_tuple)
                        if isinstance(new_node, Buffer | Source):
                            buffer_transfers.append((new_node, node, material))
            to_search = new_to_search
        if hit_search is None:
            return sources, machine_groups, buffer_lines, buffer_transfers
        else:
            return sources, machine_groups, buffer_lines, buffer_transfers, did_hit

    def analyse(self, output_point: OutputPoint) -> SingleAnalysisResults:
        if isinstance(output_point.location, Source):
            raise FactoryAnalysisException("Taking output directly from a source is not supported.")
        if (isinstance(output_point.location, MachineGroup) and
                output_point.material in output_point.location.output_materials):
            raise FactoryAnalysisException("Taking output from a machine group which already has "
                                           "output is not supported")
        if any(isinstance(node, TrashPoint) for node in output_point.location.outputs(output_point.material)):
            raise FactoryAnalysisException("Taking output from a node and material which already has a trash point is "
                                           "not supported")
        # find relevant nodes and trash points
        sources: list[Source]
        machine_groups: list[MachineGroup]
        buffer_lines: list[tuple[Buffer, str]]
        buffer_transfers: list[tuple[Buffer | Source, Buffer, str]]
        (
            sources, machine_groups, buffer_lines, buffer_transfers
        ) = self.search_nodes(output_point.location, output_point.material)
        sources_set = set(sources)
        machine_groups_set = set(machine_groups)
        buffer_lines_set = set(buffer_lines)
        buffer_transfers_set = set(buffer_transfers)

        trash_points: list[TrashPoint] = []
        did_something = True
        while did_something:
            did_something = False
            for trash_point in self.nodes:
                if not isinstance(trash_point, TrashPoint) or trash_point in trash_points:
                    continue
                (
                    new_sources, new_machine_groups, new_buffer_lines, new_buffer_transfers, did_hit
                ) = self.search_nodes(trash_point.location, trash_point.material,
                                      (sources_set, machine_groups_set, buffer_lines_set))
                if not did_hit:
                    continue
                did_something = True
                trash_points.append(trash_point)
                sources.extend(new_sources)
                sources_set.update(new_sources)
                machine_groups.extend(new_machine_groups)
                machine_groups_set.update(new_machine_groups)
                buffer_lines.extend(new_buffer_lines)
                buffer_lines_set.update(new_buffer_lines)
                buffer_transfers.extend(new_buffer_transfers)
                buffer_transfers_set.update(new_buffer_transfers)

        # set up the linear programming problem
        num_variables = 1+len(machine_groups)+len(buffer_transfers)+len(trash_points)
        buffer_transfers_start = 1+len(machine_groups)
        trash_points_start = 1+len(machine_groups)+len(buffer_transfers)
        equalities: list[tuple[np.ndarray, float]] = []
        inequalities: list[tuple[np.ndarray, float, Bottleneck]] = []
        # stop all machine groups for which one of the inputs or outputs is not relevant or disconnected
        for i, machine_group in enumerate(machine_groups):
            found_disconnect = False
            for material in machine_group.machine_type.output_materials:
                if material not in machine_group.output_materials:
                    if output_point.location != machine_group or material != output_point.material:
                        found_disconnect = True
                        break
                    continue
                node = tuple(machine_group.outputs(material))[0]
                if (
                    (isinstance(node, MachineGroup) and node not in machine_groups)
                    or (isinstance(node, TrashPoint) and node not in trash_points)
                    or (isinstance(node, Buffer) and (node, material) not in buffer_lines)
                ) and (output_point.location != machine_group or material != output_point.material):
                    found_disconnect = True
                    break
            if machine_group.has_unconnected_inputs:
                found_disconnect = True
            if found_disconnect:
                coefficients = np.zeros(num_variables, float)
                coefficients[1+i] = 1
                equalities.append((coefficients, 0.))
        # add inequalities for rate cap on machine groups
        for i, machine_group in enumerate(machine_groups):
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
        for i, machine_group in enumerate(machine_groups):
            for material in machine_group.input_materials:
                for node in machine_group.inputs(material):
                    if not isinstance(node, MachineGroup):
                        continue
                    equation = np.zeros(num_variables, float)
                    equation[1+i] = machine_group.machine_type.input_rates[material]
                    input_index = machine_groups.index(node)
                    equation[1+input_index] = -node.machine_type.output_rates[material]
                    equalities.append((equation, 0.))
        # add inequalities on source output
        source_rate_vectors = {}
        for source in sources:
            source_rate_vector = np.zeros(num_variables, float)
            for node in source.outputs(source.material):
                if isinstance(node, MachineGroup):
                    if not node in machine_groups:
                        continue
                    index = machine_groups.index(node)
                    source_rate_vector[1+index] = node.machine_type.input_rates[source.material]
                elif isinstance(node, Buffer):
                    if not (source, node, source.material) in buffer_transfers:
                        continue
                    index = buffer_transfers.index((source, node, source.material))
                    source_rate_vector[buffer_transfers_start+index] = 1.
            source_rate_vectors[source] = source_rate_vector
            if source.max_rate is not None:
                inequalities.append((
                    source_rate_vector,
                    source.max_rate,
                    SourceRateCap(source)
                ))
        # add equalities for buffer in and out and inequalities for source input caps
        buffer_throughput_vectors = {}
        for buffer, material in buffer_lines:
            # determine vectors for input and output and require they are equal
            input_vector = np.zeros(num_variables, float)
            for node in buffer.inputs(material):
                if isinstance(node, Buffer | Source):
                    index = buffer_transfers_start+buffer_transfers.index((node, buffer, material))
                    input_vector[index] = 1.
                elif isinstance(node, MachineGroup):
                    index = 1+machine_groups.index(node)
                    input_vector[index] = node.machine_type.output_rates[material]
            output_vector = np.zeros(num_variables, float)
            for node in buffer.outputs(material):
                if isinstance(node, Buffer):
                    if (node, material) not in buffer_lines:
                        continue
                    index = buffer_transfers_start+buffer_transfers.index((buffer, node, material))
                    output_vector[index] = 1.
                elif isinstance(node, MachineGroup):
                    if node not in machine_groups:
                        continue
                    index = 1+machine_groups.index(node)
                    output_vector[index] = node.machine_type.input_rates[material]
                elif isinstance(node, TrashPoint):
                    if node not in trash_points:
                        continue
                    index = trash_points_start+trash_points.index(node)
                    output_vector[index] = 1.
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
        # add relation between output and machine group if the output or a trash point is directly from a machine
        if isinstance(output_point.location, MachineGroup):
            equation = np.zeros(num_variables, float)
            equation[0] = -1
            machine_index = machine_groups.index(output_point.location)
            equation[1+machine_index] = output_point.location.machine_type.output_rates[output_point.material]
            equalities.append((equation, 0))
        for i, trash_point in enumerate(trash_points):
            if not isinstance(trash_point.location, MachineGroup):
                continue
            equation = np.zeros(num_variables, float)
            equation[trash_points_start+i] = -1
            machine_index = machine_groups.index(trash_point.location)
            equation[1+machine_index] = trash_point.location.machine_type.output_rates[trash_point.material]
            equalities.append((equation, 0))
        # add maximum output and trash rate cap
        if output_point.max_rate is not None:
            equation = np.zeros(num_variables, float)
            equation[0] = 1.
            inequalities.append((equation, output_point.max_rate, OutputPointRateCap(output_point)))
        for i, trash_point in enumerate(trash_points):
            if trash_point.max_rate is None:
                continue
            equation = np.zeros(num_variables, float)
            equation[trash_points_start+i] = 1.
            inequalities.append((equation, trash_point.max_rate, TrashPointRateCap(trash_point)))

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
                FactoryRates(
                    {source: float("inf") for source in sources},
                    {x: float("inf") for x in buffer_lines},
                    {machine_group: float("inf") for machine_group in machine_groups},
                    {},
                ),
                ()
            )
        elif result.status != 0:
            raise FactoryAnalysisException("Failed to solve the linear programming problem somehow.")
        optimal_rate = result.x[0]
        bottlenecks_indices = [i for i, x in enumerate(result.slack) if x < 1e-9]

        # if there are relevant trash points, minimize for the weighted sum of their rates
        if any(result.x[trash_points_start+i] > 1e-9 for i in range(len(trash_points))):
            rate_vector = np.zeros(num_variables, dtype=float)
            rate_vector[0] = 1.
            new_equalities_matrix = np.concatenate((equalities_matrix, np.array([rate_vector])))
            new_equalities_values = np.concatenate((equalities_values, np.array([optimal_rate])))
            new_to_minimize_vector = np.zeros(num_variables, dtype=float)
            for i, trash_point in enumerate(trash_points):
                new_to_minimize_vector[trash_points_start+i] = trash_point.weight
            # noinspection PyDeprecation
            result = scipy.optimize.linprog(
                new_to_minimize_vector, inequalities_matrix, inequalities_bounds,
                new_equalities_matrix, new_equalities_values
            )
            if result.status != 0:
                raise FactoryAnalysisException("Failed to solve the linear programming problem to minimize trash rates"
                                               " somehow.")


        # store some information from the results (which are possibly changed to minimize trashing)
        source_rates = {source: v.dot(result.x) for source, v in source_rate_vectors.items()}
        buffer_throughput = {key: v.dot(result.x) for key, v in buffer_throughput_vectors.items()}
        machine_rates = {machine_group: result.x[1+i] for i, machine_group in enumerate(machine_groups)}
        trash_rates = {trash_point: result.x[trash_points_start+i]
                       for i, trash_point in enumerate(trash_points) if result.x[trash_points_start+i] > 1e-9}

        # calculate bottleneck results
        current_rate = optimal_rate
        ordered_bottlenecks: list[tuple[float, Bottleneck]] = []
        while bottlenecks_indices:
            bottleneck_index = bottlenecks_indices[0]
            ordered_bottlenecks.append((current_rate, inequalities[bottleneck_index][2]))

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
            elif result.status == 3:  # if the problem is unbounded, there are no bottlenecks left
                break
            current_rate = result.x[0]
            # if there are relevant trash points, minimize for the weighted sum of their rates
            if any(result.x[trash_points_start + i] > 1e-9 for i in range(len(trash_points))):
                rate_vector = np.zeros(num_variables, dtype=float)
                rate_vector[0] = 1.
                new_equalities_matrix = np.concatenate((equalities_matrix, np.array([rate_vector])))
                new_equalities_values = np.concatenate((equalities_values, np.array([current_rate])))
                new_to_minimize_vector = np.zeros(num_variables, dtype=float)
                for i, trash_point in enumerate(trash_points):
                    new_to_minimize_vector[trash_points_start + i] = trash_point.weight
                # noinspection PyDeprecation
                result = scipy.optimize.linprog(
                    new_to_minimize_vector, inequalities_matrix, inequalities_bounds,
                    new_equalities_matrix, new_equalities_values
                )
                if result.status != 0:
                    raise FactoryAnalysisException(
                        "Failed to solve the linear programming problem to minimize trash rates"
                        " somehow.")
            # obtain the new bottlenecks from the results
            bottlenecks_indices = [i for i, x in enumerate(result.slack) if x < 1e-9]
        return SingleAnalysisResults(
            optimal_rate,
            FactoryRates(source_rates, buffer_throughput, machine_rates, trash_rates),
            tuple(ordered_bottlenecks)
        )


class SubFactory:
    def __init__(self, parent: _Factory | SubFactory):
        self.parent = parent
        self._nodes: list[FactoryNode] = []
        self._output_points: list[OutputPoint] = []

    @property
    def factory(self) -> _Factory:
        if isinstance(self.parent, _Factory):
            return self.parent
        return self.parent.factory

    def add_buffer(self, name: str, rate_caps: dict[str, float] | None = None) -> Buffer:
        buffer = self.parent.add_buffer(name, rate_caps)
        self._nodes.append(buffer)
        return buffer

    def add_source(self, material: str, max_rate: float | None = None) -> Source:
        source = self.parent.add_source(material, max_rate)
        self._nodes.append(source)
        return source

    def add_machine_group(self, machine_type: MachineType, machine_cap: float | None = None) -> MachineGroup:
        machine_group = self.parent.add_machine_group(machine_type, machine_cap)
        self._nodes.append(machine_group)
        return machine_group

    def add_output_point(self, output_point: OutputPoint):
        if isinstance(self.parent, SubFactory):
            self.parent.add_output_point(output_point)
        self._output_points.append(output_point)

    def add_trash_point(self, location: FactoryNode, material: str, weight: float = 1., max_rate: float | None = None) -> TrashPoint:
        trash_point = self.parent.add_trash_point(location, material, weight, max_rate)
        self._nodes.append(trash_point)
        return trash_point

    def connect(self, frm: FactoryNode, to: FactoryNode, *materials: str):
        self.parent.connect(frm, to, *materials)

    def analyse(self, print_progress: bool = False) -> FullAnalysisResults:
        sub_results = []
        for i, output_point in enumerate(self._output_points):
            if print_progress:
                print(f"analysing output point {i+1}/{len(self._output_points)}", end="\r")
            sub_results.append((output_point, self.factory.analyse(output_point)))
        if print_progress:
            print("done!")
        return FullAnalysisResults.from_single_analyses(sub_results)

    def default_print_info(self, results: FullAnalysisResults):
        print(results.display())
        self.print_buffer_throughput(results.max_rates)
        self.print_machines(results.max_rates)
        for output_point in self._output_points:
            if output_point in results.single_results:
                print("")
                print(f" --- {output_point.material}")
                print(results.single_results[output_point].display(True, True, True, True))

    def print_machines(self, rates: FactoryRates):
        print(" -- machines -- ")
        for machine in self._nodes:
            if not isinstance(machine, MachineGroup):
                continue
            print(machine.machine_type.display_info(rates[machine]))

    def print_buffer_throughput(self, rates: FactoryRates):
        print(" -- buffer throughput -- ")
        for buffer in self._nodes:
            if not isinstance(buffer, Buffer):
                continue
            print(buffer.name + ":")
            for material, rate in rates.get_throughputs(buffer):
                print(f"- {material}: {rate:.2f}/s")


def new_factory() -> SubFactory:
    return SubFactory(_Factory())
