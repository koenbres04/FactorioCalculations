import json
from dataclasses import dataclass
from math import ceil
import abc


@dataclass
class Recipe:
    outp: str
    output_count: int
    inp: tuple[tuple[str, int], ...]
    time: float

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data["output"],
            data["count"],
            tuple((key, value) for key, value in data["inputs"].items()),
            data["craft_time"]
        )

    def to_dict(self) -> dict:
        return {
            "output": self.outp,
            "count": self.output_count,
            "craft_time": self.time,
            "inp": {x: y for x, y in self.inp}
        }


class Bottleneck(abc.ABC):
    @abc.abstractmethod
    def display(self) -> str:
        pass

    @property
    def duration(self) -> float | None:
        return None

    @duration.setter
    def duration(self, value):
        pass


class External(Bottleneck):
    def display(self) -> str:
        return " from an external source"


@dataclass
class Cap(Bottleneck):
    description: str
    _duration: float

    @property
    def duration(self) -> float | None:
        return self._duration

    @duration.setter
    def duration(self, x):
        self._duration = x

    def display(self) -> str:
        return f", bottlenecked by {f'{self.duration:.2f}'.rjust(4)}x from {self.description}"



@dataclass
class Proportional(Bottleneck):
    to: str
    factor: float
    _duration: float | None

    @property
    def duration(self) -> float | None:
        return self._duration

    @duration.setter
    def duration(self, x):
        self._duration = x

    def display(self) -> str:
        return f" = {f'{self.factor:.2f}'} x {self.to}" + ("" if self.duration is None else
                                            f" for another {self.duration:.2f}x")


@dataclass
class ItemLine:
    rate: float
    bottleneck: Bottleneck
    num_crafters: int | None


def min_none_as_inf(*args):
    return min((arg for arg in args if arg is not None), default=None)

if __name__ == '__main__':
    input_file = "main_factory.json"

    with open(input_file) as file:
        factory_data = json.load(file)
    crafter_speed = factory_data["misc"]["crafter_speed"]
    rate_cap = factory_data["misc"]["belt_cap"]
    crafter_cap = factory_data["misc"]["crafter_cap"]
    item_lines: dict[str, ItemLine] = {
        name: ItemLine(rate, External(), None) for name, rate in factory_data["input_rates"].items()
    }
    recipes = [Recipe.from_dict(x) for x in factory_data["recipes"]]

    for recipe in recipes:
        if len(recipe.inp) == 1:
            input_name, input_count = recipe.inp[0]
            bottleneck = Proportional(input_name, recipe.output_count/input_count, None)
            max_craft_rate = item_lines[input_name].rate/input_count
        else:
            sorted_inputs = [
                (name, count, item_lines[name].rate/count) for name, count in recipe.inp
            ]
            sorted_inputs.sort(key=lambda x: x[2])
            bottleneck_name, bottleneck_count, max_craft_rate = sorted_inputs[0]
            bottleneck = Proportional(bottleneck_name, recipe.output_count/bottleneck_count,
                                      sorted_inputs[1][2]/max_craft_rate)
        while isinstance(item_lines[bottleneck.to].bottleneck, Proportional):
            new_bottleneck = item_lines[bottleneck.to].bottleneck
            # noinspection PyUnresolvedReferences
            bottleneck = Proportional(new_bottleneck.to, bottleneck.factor*new_bottleneck.factor,
                                      min_none_as_inf(new_bottleneck.duration, bottleneck.duration))

        # apply output rate cap
        if max_craft_rate*recipe.output_count > rate_cap:
            capped_max_craft_rate = min(max_craft_rate*recipe.output_count, rate_cap)/recipe.output_count
            bottleneck_factor = max_craft_rate/capped_max_craft_rate
            bottleneck = Cap("belt rate cap", bottleneck_factor)
            max_craft_rate = capped_max_craft_rate
        else:
            factor_until_cap = rate_cap/recipe.output_count/max_craft_rate
            bottleneck.duration = min_none_as_inf(bottleneck.duration, factor_until_cap)

        # apply crafter cap
        if max_craft_rate*recipe.time/crafter_speed > crafter_cap:
            capped_max_craft_rate = crafter_cap/recipe.time*crafter_speed
            bottleneck_factor = max_craft_rate / capped_max_craft_rate
            bottleneck = Cap("crafter cap", bottleneck_factor)
            max_craft_rate = capped_max_craft_rate
        else:
            factor_until_cap = crafter_cap/recipe.time*crafter_speed/max_craft_rate
            bottleneck.duration = min_none_as_inf(bottleneck.duration, factor_until_cap)


        # store results
        output_rate = max_craft_rate*recipe.output_count
        num_crafters = ceil(max_craft_rate*recipe.time/crafter_speed)
        item_lines[recipe.outp] = ItemLine(output_rate, bottleneck, num_crafters)

    # print results
    max_name_length = max(len(name) for name in item_lines.keys())
    for name, line in item_lines.items():
        print(
            f"{name}:".ljust(max_name_length+2) +
            (str(line.num_crafters).rjust(3) + " crafters, "  if line.num_crafters is not None else " "*14)+
            f"{line.rate:.2f}".rjust(5) + f" /s{line.bottleneck.display()}"
        )
