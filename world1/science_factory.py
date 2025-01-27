from facalc.factories import Factory, Buffer, OutputPoint, FullAnalysisResults
from facalc.factorio_machines import Lab, SCIENCE_PACKS, Module
from typing import Iterable


class ScienceFactory:
    def __init__(
            self,
            factory: Factory,
            input_belt: Buffer,
            science_types: Iterable[str],
            max_time: float = 60,
            speed_bonus: float = .0,
            lab_modules: tuple[Module, ...] = ()
    ):
        self.lab_groups = []
        self.output_points: dict[str, OutputPoint] = {}
        self.input_belt = input_belt
        for science_type in science_types:
            labs = factory.add_machine_group(Lab(science_type, max_time, speed_bonus, lab_modules))
            for c in science_type:
                factory.connect(input_belt, labs, SCIENCE_PACKS[c])
            output_point = OutputPoint(labs, f"{science_type} science")
            factory.add_output_point(output_point)
            self.output_points[science_type] = output_point
            self.lab_groups.append(labs)

    def print_info(self, analysis_results: FullAnalysisResults, science_type: str):
        if not science_type in self.output_points:
            raise ValueError("Science type 'science type' was not added to this factory.")
        print(f" --------- {science_type} science info")
        for output_point, sub_result in analysis_results.single_results.items():
            if output_point.location in self.lab_groups and output_point.material == f"{science_type} science":
                print(sub_result.display())
