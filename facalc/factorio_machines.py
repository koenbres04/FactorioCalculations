import json
from facalc.factories import *
import enum
from math import ceil
import os.path


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
class OilRefineryRecipe:
    time: float
    name: str
    inp: dict[str, float]
    outp: dict[str, float]
    supports_prod_modules: bool


@dataclass(frozen=True)
class OilRefinery(MachineType):
    recipe: OilRefineryRecipe
    modules: tuple[Module, ...] = tuple()

    @property
    def input_rates(self) -> dict[str, float]:
        return {name: amount / self.recipe.time * (1.+modules_to_speed_bonus(self.modules))
                for name, amount in self.recipe.inp.items()}

    @property
    def output_rates(self) -> dict[str, float]:
        return {name: amount / self.recipe.time * (1.+modules_to_speed_bonus(self.modules))*
                      (1.+modules_to_production_bonus(self.modules))
                for name, amount in self.recipe.outp.items()}

    def display_info(self, rate: float) -> str:
        if rate == float("inf"):
            return f"infinitely many {self.recipe.name} refineries"
        num_refineries = ceil(rate)
        return f"{num_refineries} {self.recipe.name} refineries"

    def get_cap_description(self) -> str:
        return f"{self.recipe.name} refinery cap"


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
OIL_REFINERY_RECIPES: dict[str, OilRefineryRecipe] = {}
for data in FACTORIO_DATA["oil_refinery_recipes"]:
    OIL_REFINERY_RECIPES[data["name"]] = OilRefineryRecipe(
        time=data["time"],
        name=data["name"],
        outp=data["outputs"],
        inp=data["inputs"],
        supports_prod_modules=data["supports_production_modules"]
    )
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


del FACTORIO_DATA

