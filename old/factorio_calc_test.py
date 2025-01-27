from dataclasses import dataclass
from math import ceil
import json

@dataclass
class Recipe:
    outp: str
    output_count: int
    inp: tuple[tuple[str, int], ...]
    time: float

    def to_dict(self) -> dict:
        return {
            "output": self.outp,
            "count": self.output_count,
            "craft_time": self.time,
            "inputs": {x: y for x, y in self.inp}
        }


max_rates: dict[str, float] = {
    "iron_plate": 7.5,
    "gear": 7.5,
    "copper_plate": 15,
    "steel": 7.5,
    "iron_stick": 7.5,
    "stone_brick": 7.5,
    "coal": 7.5,
    "plastic": 5.16,
    "sulfur": 7.5,
    "explosives": 6.88,
}

rate_cap = 15
crafter_speed = 0.75
recipes = [
    Recipe("copper_wire", 2, (("copper_plate", 1),), 0.5),
    Recipe("circuit", 1, (("copper_wire", 3), ("iron_plate", 1)), 0.5),
    Recipe("inserter", 1, (("copper_wire", 3), ("gear", 1), ("iron_plate", 1)), 0.5),
    Recipe("belt", 2, (("gear", 1), ("iron_plate", 1)), 0.5),
    Recipe("ammo", 1, (("iron_plate", 1),), 0.5),
    Recipe("underground_belt", 2, (("belt", 5), ("iron_plate", 2)), 1),
    Recipe("splitter", 1, (("circuit", 5), ("belt", 4), ("iron_plate", 5)), 1),
    Recipe("long_inserter", 1, (("inserter", 1), ("gear", 1), ("iron_plate", 1)), 0.5),
    Recipe("medium_electric_pole", 1, (("copper_wire", 2), ("iron_stick", 4), ("steel", 2)), 0.5),
    Recipe("big_electric_pole", 1, (("copper_wire", 4), ("iron_stick", 8), ("steel", 5),), 0.5),
    Recipe("auto_crafter_1", 1, (("circuit", 3), ("gear", 5), ("iron_plate", 9)), 0.5),
    Recipe("electric_drill", 1, (("circuit", 3), ("gear", 5), ("iron_plate", 10),), 2),
    Recipe("wall", 1, (("stone_brick", 5),), 0.5),
    Recipe("steel_furnace", 1, (("steel", 6), ("stone_brick", 10)), 3),
    Recipe("auto_crafter_2", 1, (("auto_crafter_1", 1), ("circuit", 3), ("gear", 5), ("steel", 2)), 0.5),
    Recipe("gun_turret", 1, (("copper_plate", 10), ("gear", 10), ("iron_plate", 10)), 8),
    Recipe("fast_inserter", 1, (("iron_plate", 2), ("circuit", 2), ("inserter", 1)), 0.5),
    Recipe("red_belt", 1, (("belt", 1), ("gear", 5)), 0.5),
    Recipe("lab", 1, (("belt", 4), ("gear", 10), ("circuit", 10)), 1),
    Recipe("asp", 1, (("copper_plate", 1), ("iron_plate", 1)), 5),
    Recipe("lsp", 1, (("belt", 1), ("inserter", 1)), 6),
    Recipe("pipe", 1, (("iron_plate", 1),), 0.5),
    Recipe("engine_unit", 1, (("gear", 1), ("pipe", 2), ("steel", 1)), 10),
    Recipe("steam_engine", 1, (("gear", 8), ("pipe", 3), ("iron_plate", 10)), 0.5),
    Recipe("offshore_pump", 1, (("gear", 2), ("pipe", 3)), 0.5),
    Recipe("pipe_to_ground", 1, (("iron_plate", 5), ("pipe", 10)), 0.5),
    Recipe("pump_jack", 1, (("steel", 5), ("gear", 10), ("circuit", 5), ("pipe", 10)), 5),
    Recipe("chemical_plant", 1, (("steel", 5), ("gear", 5), ("circuit", 5), ("pipe", 5)), 5),
    Recipe("oil_refinery", 1, (("steel", 15), ("gear", 10), ("circuit", 10), ("pipe", 10), ("stone_brick", 10)), 8),
    Recipe("gate", 1, (("wall", 1), ("circuit", 2), ("steel", 2)), 0.5),
    Recipe("slowdown_capsule", 1, (("coal", 5), ("steel", 2), ("circuit", 2)), 8),
    Recipe("poison_capsule", 1, (("coal", 10), ("steel", 3), ("circuit", 3)), 8),
    Recipe("grenade", 1, (("coal", 10), ("iron_plate", 5)), 8),
    Recipe("piercing_ammo", 1, (("copper_plate", 5), ("ammo", 1), ("steel", 1)), 3),
    Recipe("msp", 2, (("piercing_ammo", 1), ("grenade", 1), ("wall", 2)), 10),
    Recipe("red_circuit", 1, (("plastic", 2), ("circuit", 2), ("copper_wire", 4)), 6),
    Recipe("csp", 2, (("engine_unit", 2), ("red_circuit", 3), ("sulfur", 1)), 24),
    Recipe("cannon_shell", 1, (("steel", 2), ("plastic", 2), ("explosives", 1)), 8),
    Recipe("explosive_cannon_shell", 1, (("steel", 2), ("plastic", 2), ("explosives", 2)), 8),
    Recipe("low_density_structure", 1, (("copper_plate", 20), ("steel", 2), ("plastic", 5)), 15),
    Recipe("electric_furnace", 1, (("steel", 10), ("red_circuit", 5), ("stone_brick", 10)), 5),
    # Recipe("solar_panel", 1, (("steel", 1), ("inserter", 1)), 10),
]

with open("temp_output.json", "w") as file:
    json.dump({"recipes": [recipe.to_dict() for recipe in recipes]}, file, indent=2)

for recipe in recipes:
    max_craft_rate = min(
         max_rates[inp]/count for inp, count in recipe.inp
    )
    max_craft_rate = min(max_craft_rate*recipe.output_count, rate_cap)/recipe.output_count
    num_crafters = ceil(max_craft_rate*recipe.time/crafter_speed)
    output_rate = max_craft_rate*recipe.output_count
    max_rates[recipe.outp] = output_rate
    print(f"{recipe.outp}: {num_crafters} crafters, {output_rate:.2f} /s")



