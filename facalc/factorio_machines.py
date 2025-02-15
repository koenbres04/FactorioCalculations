import json
from facalc.factories import *
import enum
from math import ceil
import os.path
from functools import lru_cache


class Module(enum.Enum):
    SPEED_MODULE_1 = 0
    SPEED_MODULE_2 = 1
    SPEED_MODULE_3 = 2
    PRODUCTION_MODULE_1 = 3
    PRODUCTION_MODULE_2 = 4
    PRODUCTION_MODULE_3 = 5
    EFFICIENCY_MODULE_1 = 6
    EFFICIENCY_MODULE_2 = 7
    EFFICIENCY_MODULE_3 = 8

MODULE_SPEED_BONUS = {
    Module.SPEED_MODULE_1: .2,
    Module.SPEED_MODULE_2: .3,
    Module.SPEED_MODULE_3: .5,
    Module.PRODUCTION_MODULE_1: -.05,
    Module.PRODUCTION_MODULE_2: -.10,
    Module.PRODUCTION_MODULE_3: -.15,
    Module.EFFICIENCY_MODULE_1: 0.,
    Module.EFFICIENCY_MODULE_2: 0.,
    Module.EFFICIENCY_MODULE_3: 0.,
}

MODULE_PRODUCTION_BONUS = {
    Module.SPEED_MODULE_1: 0.,
    Module.SPEED_MODULE_2: 0.,
    Module.SPEED_MODULE_3: 0.,
    Module.PRODUCTION_MODULE_1: .04,
    Module.PRODUCTION_MODULE_2: .06,
    Module.PRODUCTION_MODULE_3: .10,
    Module.EFFICIENCY_MODULE_1: 0.,
    Module.EFFICIENCY_MODULE_2: 0.,
    Module.EFFICIENCY_MODULE_3: 0.,
}


def modules_to_speed_bonus(modules: tuple[Module, ...]) -> float:
    return sum((MODULE_SPEED_BONUS[x] for x in modules), start=0.)


def modules_to_production_bonus(modules: tuple[Module, ...]) -> float:
    return sum((MODULE_PRODUCTION_BONUS[x] for x in modules), start=0.)


CRAFTER_LEVEL_TO_SPEED = {
    1: 0.5,
    2: 0.75,
    3: 1.0
}

@dataclass(frozen=True)
class CrafterRecipe:
    time: float
    outp: str
    outp_count: float
    inp: dict[str, float]
    supports_prod_modules: bool


@dataclass(frozen=True)
class Crafter(MachineType):
    recipe: CrafterRecipe
    crafter_level: int
    modules: tuple[Module, ...] = tuple()

    @property
    def crafting_speed(self) -> float:
        return CRAFTER_LEVEL_TO_SPEED[self.crafter_level]

    @property
    def input_rates(self) -> dict[str, float]:
        return {name: amount / self.recipe.time * self.crafting_speed * (1.+modules_to_speed_bonus(self.modules))
                for name, amount in self.recipe.inp.items()}

    @property
    def output_rates(self) -> dict[str, float]:
        return {
            self.recipe.outp: self.recipe.outp_count * self.crafting_speed / self.recipe.time * (1.+modules_to_speed_bonus(self.modules))
                              * (1.+modules_to_production_bonus(self.modules) if self.recipe.supports_prod_modules else 1.)
        }

    def display_info(self, rate: float) -> str:
        if rate == float("inf"):
            return f"infinitely many {self.recipe.outp} crafters"
        num_crafters = ceil(rate)
        return f"{num_crafters} {self.recipe.outp} crafters"

    def get_cap_description(self) -> str:
        return f"{self.recipe.outp} crafter cap"


@dataclass(frozen=True)
class FurnaceRecipe:
    time: float
    outp: str
    outp_count: float
    inp: dict[str, float]
    supports_prod_modules: bool


@dataclass(frozen=True)
class ElectronicFurnace(MachineType):
    recipe: FurnaceRecipe
    modules: tuple[Module, ...] = tuple()

    @property
    def input_rates(self) -> dict[str, float]:
        return {name: 2 * amount / self.recipe.time * (1.+modules_to_speed_bonus(self.modules))
                for name, amount in self.recipe.inp.items()}

    @property
    def output_rates(self) -> dict[str, float]:
        return {
            self.recipe.outp: 2 * self.recipe.outp_count / self.recipe.time * (1.+modules_to_speed_bonus(self.modules))
                              * (1.+modules_to_production_bonus(self.modules))
        }

    def display_info(self, rate: float) -> str:
        if rate == float("inf"):
            return f"infinitely many {self.recipe.outp} furnaces"
        num_crafters = ceil(rate)
        return f"{num_crafters} {self.recipe.outp} furnaces"

    def get_cap_description(self) -> str:
        return f"{self.recipe.outp} furnace cap"


def get_ore_rate(num_electric_drills: int | None, resource_bonus: float = 0., modules: tuple[Module, ...] = ()):
    if num_electric_drills is None:
        return None
    return (0.5*num_electric_drills*(1+resource_bonus+modules_to_production_bonus(modules))
            *(1.+modules_to_speed_bonus(modules)))

def get_crude_oil_rate(crude_oil_rates: Iterable[float] | None, resource_bonus: float = 0.,
                       modules: tuple[Module, ...] = ()):
    if crude_oil_rates is None:
        return None
    base_oil_rate = sum(crude_oil_rates, start=0.)
    return base_oil_rate*(1.+resource_bonus+modules_to_production_bonus(modules))*(1.+modules_to_speed_bonus(modules))



SCIENCE_PACKS = {
    "a": "automation_science_pack",
    "l": "logistic_science_pack",
    "m": "military_science_pack",
    "c": "chemical_science_pack",
    "u": "utility_science_pack",
    "p": "production_science_pack",
    "s": "space_science_pack"
}

class Lab(MachineType):
    def __init__(self, science_types: str, time: float, speed_bonus: float = 0., modules: tuple[Module, ...] = tuple()):
        self.science_types = science_types
        self.time = time
        self.speed_bonus = speed_bonus
        self.modules = modules

    @property
    def input_rates(self) -> dict[str, float]:
        return {
            SCIENCE_PACKS[c]: (1.+self.speed_bonus+modules_to_speed_bonus(self.modules)) for c in self.science_types
        }

    @property
    def output_rates(self) -> dict[str, float]:
        return {
            f"{self.science_types} science": (1.+self.speed_bonus+modules_to_speed_bonus(self.modules))
                                             * (1.+modules_to_production_bonus(self.modules))
        }

    def display_info(self, rate: float) -> str:
        return f"{ceil(rate*self.time/(1.+self.speed_bonus))} {self.science_types} labs"


@dataclass(frozen=True)
class ChemicalPlantRecipe:
    time: float
    name: str
    outp: str
    outp_count: float
    inp: dict[str, float]
    supports_prod_modules: bool


@dataclass(frozen=True)
class ChemicalPlant(MachineType):
    recipe: ChemicalPlantRecipe
    modules: tuple[Module, ...] = tuple()

    @property
    def input_rates(self) -> dict[str, float]:
        return {name: amount / self.recipe.time * (1.+modules_to_speed_bonus(self.modules))
                for name, amount in self.recipe.inp.items()}

    @property
    def output_rates(self) -> dict[str, float]:
        return {
            self.recipe.outp: self.recipe.outp_count / self.recipe.time * (1.+modules_to_speed_bonus(self.modules))
                              * (1.+modules_to_production_bonus(self.modules))
        }

    def display_info(self, rate: float) -> str:
        if rate == float("inf"):
            return f"infinitely many {self.recipe.name} chemical plants"
        num_crafters = ceil(rate)
        return f"{num_crafters} {self.recipe.name} chemical plants"

    def get_cap_description(self) -> str:
        return f"{self.recipe.outp} chemical plant cap"


@dataclass(frozen=True)
class CompleteRecipe:
    time: float
    name: str
    inp: dict[str, float]
    outp: dict[str, float]
    supports_prod_modules: bool

    @staticmethod
    def from_json(data: dict):
        return CompleteRecipe(
            time=data["time"],
            name=data["name"],
            outp=data["outputs"],
            inp=data["inputs"],
            supports_prod_modules=data["supports_production_modules"]
        )

    def get_input_rates(self, modules: tuple[Module, ...]) -> dict[str, float]:
        return {name: amount / self.time * (1.+modules_to_speed_bonus(modules))
                for name, amount in self.inp.items()}

    def get_output_rates(self, modules: tuple[Module, ...]) -> dict[str, float]:
        result = {}
        for name, amount in self.outp.items():
            input_amount = self.inp[name] if name in self.inp else 0.
            new_amount = (amount if input_amount >= amount else
                          (amount-input_amount)*(1.+modules_to_production_bonus(modules))+input_amount)
            result[name] = new_amount / self.time * (1.+modules_to_speed_bonus(modules))
        return result


@dataclass(frozen=True)
class OilRefinery(MachineType):
    recipe: CompleteRecipe
    modules: tuple[Module, ...] = tuple()

    @property
    def input_rates(self) -> dict[str, float]:
        return self.recipe.get_input_rates(self.modules)

    @property
    def output_rates(self) -> dict[str, float]:
        return self.recipe.get_output_rates(self.modules)

    def display_info(self, rate: float) -> str:
        if rate == float("inf"):
            return f"infinitely many {self.recipe.name} refineries"
        num_refineries = ceil(rate)
        return f"{num_refineries} {self.recipe.name} refineries"

    def get_cap_description(self) -> str:
        return f"{self.recipe.name} refinery cap"


@dataclass(frozen=True)
class Centrifuge(MachineType):
    recipe: CompleteRecipe
    modules: tuple[Module, ...] = tuple()

    @property
    def input_rates(self) -> dict[str, float]:
        return self.recipe.get_input_rates(self.modules)

    @property
    def output_rates(self) -> dict[str, float]:
        return self.recipe.get_output_rates(self.modules)

    def display_info(self, rate: float) -> str:
        if rate == float("inf"):
            return f"infinitely many {self.recipe.name} centrifuges"
        num_refineries = ceil(rate)
        return f"{num_refineries} {self.recipe.name} centrifuges"

    def get_cap_description(self) -> str:
        return f"{self.recipe.name} centrifuge cap"


@dataclass
class UraniumDrill(MachineType):
    resource_bonus: float = 0.
    modules: tuple[Module, ...] = tuple()

    @property
    def input_rates(self) -> dict[str, float]:
        return {"sulfuric_acid": 0.25*(1.+modules_to_speed_bonus(self.modules)),
                "pre_uranium_ore": 0.25*(1.+modules_to_speed_bonus(self.modules))}

    @property
    def output_rates(self) -> dict[str, float]:
        return {"uranium_ore": 0.25 * (1. + self.resource_bonus + modules_to_production_bonus(self.modules)) *
                               (1.+modules_to_speed_bonus(self.modules))}

    def display_info(self, rate: float) -> str:
        if rate == float("inf"):
            return f"infinitely many uranium drills"
        num_drills = ceil(rate)
        return f"{num_drills} uranium centrifuges"

    def get_cap_description(self) -> str:
        return f"number of uranium drills cap"


class NuclearReactor(MachineType):
    @property
    def input_rates(self) -> dict[str, float]:
        return {"uranium_fuel_cell": 1/200}

    @property
    def output_rates(self) -> dict[str, float]:
        return {"depleted_uranium_fuel_cell": 1/200, "uranium_fuel_cell_power": 1/200}

    def display_info(self, rate: float) -> str:
        return f"{ceil(rate)} nuclear reactors"

    def get_cap_description(self) -> str:
        return f"nuclear reactor number cap"


with open(os.path.join(os.path.dirname(__file__), "factorio_data.json")) as file:
    FACTORIO_DATA = json.load(file)

CRAFTER_RECIPES: dict[str, CrafterRecipe] = {}
for data in FACTORIO_DATA["crafter_recipes"]:
    CRAFTER_RECIPES[data["output"]] = CrafterRecipe(
        time=data["time"],
        outp=data["output"],
        outp_count=data["count"],
        inp=data["inputs"],
        supports_prod_modules=data["supports_production_modules"]
    )
FURNACE_RECIPES: dict[str, FurnaceRecipe] = {}
for data in FACTORIO_DATA["furnace_recipes"]:
    FURNACE_RECIPES[data["output"]] = FurnaceRecipe(
        time=data["time"],
        outp=data["output"],
        outp_count=data["count"],
        inp=data["inputs"],
        supports_prod_modules=data["supports_production_modules"]
    )
OIL_REFINERY_RECIPES: dict[str, CompleteRecipe] = {}
for data in FACTORIO_DATA["oil_refinery_recipes"]:
    OIL_REFINERY_RECIPES[data["name"]] = CompleteRecipe.from_json(data)
CHEMICAL_PLANT_RECIPES: dict[str, ChemicalPlantRecipe] = {}
for data in FACTORIO_DATA["chemical_plant_recipes"]:
    CHEMICAL_PLANT_RECIPES[data["name"]] = ChemicalPlantRecipe(
        time=data["time"],
        name=data["name"],
        outp=data["output"],
        outp_count=data["count"],
        inp=data["inputs"],
        supports_prod_modules=data["supports_production_modules"]
    )
CENTRIFUGE_RECIPES: dict[str, CompleteRecipe] = {}
for data in FACTORIO_DATA["centrifuge_recipes"]:
    CENTRIFUGE_RECIPES[data["name"]] = CompleteRecipe.from_json(data)

del FACTORIO_DATA

