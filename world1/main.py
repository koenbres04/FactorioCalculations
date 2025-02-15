from facalc.factories import Factory, OutputPoint
from facalc.factorio_machines import Module
from iron_factory import IronFactory
from copper_factory import CopperFactory
from misc_factory import add_misc_factory
from stone_factory import StoneFactory
from circuit_factory import CircuitFactory
from chemical_factory import ChemicalFactory
from science_factory import ScienceFactory
from module_factory import ModuleFactory
from mini_factories import LDSFactory, RailFactory
from nuclear_factory import NuclearFactory

def main():
    factory = Factory()
    # global parameters
    resource_bonus = .3

    # add various factories
    iron_factory = IronFactory(
        factory,
        num_drills=160,
        drill_bonus=resource_bonus,
        crafter_level=3,
        output_caps={
            "iron_plate": 180,
            "gear": 30,
            "steel": 30
        },
        iron_ore_line_cap=7.5,
        furnace_modules=(Module.PRODUCTION_MODULE_1,)*2,
        crafter_modules=(Module.PRODUCTION_MODULE_1,)*4,
        drill_modules=(Module.SPEED_MODULE_1,)*3
    )

    copper_factory = CopperFactory(
        factory,
        num_drills=141,
        drill_bonus=resource_bonus,
        output_caps={"copper_plate": 30*6},
        furnace_modules=(Module.PRODUCTION_MODULE_1,)*2,
        drill_modules=(Module.SPEED_MODULE_1,)*3
    )

    stone_factory = StoneFactory(
        factory, iron_factory.iron_ore_line,
        num_drills=65,
        drill_bonus=resource_bonus,
        crafter_level=3,
        output_caps={
            "stone": 30,
            "stone_brick": 15,
            "concrete": 15
        },
        furnace_modules=(Module.PRODUCTION_MODULE_1,)*2,
        crafter_modules=(Module.PRODUCTION_MODULE_1,)*4,
        drill_modules=(Module.PRODUCTION_MODULE_1,)*3
    )

    chemical_factory = ChemicalFactory(
        factory, iron_factory.output_belt, copper_factory.output_belt,
        pumpjack_bonus=resource_bonus,
        coal_rate=30,
        crude_oil_rates=[
            2.6, 2.6, 8.23, 6.88, 4.54, 3.42, 2.94,
            7.05, 33.0, 23.6, 10.1, 20.7, 11.4, 6.31, 22.4, 12.4, 27.6
            # 2, 2, 6, 5, 3, 2, 2,
            # 5, 25, 18, 7, 15, 8, 9, 17, 21, 4,
        ],
        input_caps={
            "iron_plate": 15,
            "copper_plate": 15,
        },
        output_caps={
            "coal": 15,
            "plastic": 45,
            "sulfur": 15,
            "explosives": 15,
            "battery": 15,
            "solid_fuel": 15,
        },
        chemical_plant_modules=(Module.PRODUCTION_MODULE_1,)*3,
        pumpjack_modules=(Module.SPEED_MODULE_1,)*2,
        oil_refinery_modules=(Module.PRODUCTION_MODULE_1,)*3
    )

    circuit_factory = CircuitFactory(
        factory, iron_factory.output_belt, copper_factory.output_belt, chemical_factory.output_line,
        crafter_level=3,
        output_caps={
            "circuit": 30,
            "red_circuit": 30,
            "blue_circuit": 7.5,
        },
        crafter_modules=(Module.PRODUCTION_MODULE_1,)*4,
    )

    lds_factory = LDSFactory(
        factory, copper_factory.output_belt, chemical_factory.output_line, iron_factory.output_belt,
        crafter_level=3,
        crafter_modules=(Module.PRODUCTION_MODULE_1,)*4,
        input_cap={
            "copper_plate": 60,
            "steel": 15,
            "plastic": 15,
        }
    )

    rail_factory = RailFactory(
        factory, iron_factory.output_belt, iron_factory.output_belt, stone_factory.output_line,
        crafter_level=3,
        rail_crafter_modules=(Module.SPEED_MODULE_1,) * 4,
        stick_crafter_modules=(Module.PRODUCTION_MODULE_1,) * 4,
        input_cap={
            "iron_plate": 15,
            "steel": 30,
            "stone": 30
        }
    )

    module_factory = ModuleFactory(
        factory, circuit_factory.output_line,
        ("speed", "productivity"),
        crafter_level=3,
        crafter_modules=(Module.SPEED_MODULE_1,)*4,
        input_caps={
            "circuit": 30,
            "red_circuit": 30,
            "blue_circuit": 7.5
        },
    )

    rocket_fuel_line = factory.add_buffer("rocket_fuel_line")
    nuclear_factory = NuclearFactory(
        factory, iron_factory.output_belt, chemical_factory.output_line, rocket_fuel_line,
        num_nuclear_reactors=10,
        resource_bonus=resource_bonus,
        num_drills=20,
        drill_modules=(Module.PRODUCTION_MODULE_1,)*3,
        centrifuge_modules=(Module.SPEED_MODULE_1,)*2,
        crafter_level=3,
        crafter_modules=(Module.PRODUCTION_MODULE_1,)*3,
        input_caps={
        },
        output_caps={
            "uranium-235": 7.5,
            "uranium-238": 1.,
            "nuclear_fuel": 1.,
            "uranium_fuel_cell": 0.05,
        }
    )

    # add misc factory
    immediate_outputs = [
        "iron_plate",
        "gear",
        "iron_stick",
        "steel",
        "copper_plate",
        "circuit",
        "red_circuit",
        "blue_circuit",
        "stone",
        "stone_brick",
        "concrete",
        "coal",
        "plastic",
        "sulfur",
        "explosives",
        "battery",
        "solid_fuel",
        "low_density_structure",
        "rail",
        "productivity_module_2",
        "speed_module_2",
        "productivity_module_3",
        "speed_module_3",
        "uranium-235",
        "uranium-238",
        "nuclear_fuel",
        "uranium_fuel_cell"
    ]
    stations = [
        "copper_wire",
        "iron_stick",
        "inserter",
        "belt",
        "ammo",
        "underground_belt",
        "splitter",
        "long_inserter",
        "medium_electric_pole",
        "big_electric_pole",
        "auto_crafter_1",
        "electric_drill",
        "wall",
        "steel_furnace",
        "auto_crafter_2",
        "gun_turret",
        "fast_inserter",
        "red_belt",
        "lab",
        "automation_science_pack",
        "logistic_science_pack",
        "pipe",
        "engine_unit",
        "steam_engine",
        "offshore_pump",
        "pipe_to_ground",
        "pump_jack",
        "chemical_plant",
        "oil_refinery",
        "gate",
        "slowdown_capsule",
        "poison_capsule",
        "grenade",
        "piercing_ammo",
        "military_science_pack",
        "rocket_fuel",
        "chemical_science_pack",
        "cannon_shell",
        "explosive_cannon_shell",
        "electric_furnace",
        "rocket",
        "explosive_rocket",
        "electric_engine_unit",
        "flying_robot_frame",
        "logistic_robot",
        "construction_robot",
        "utility_science_pack",
        "roboport",
        "repair_pack",
        "radar",
        "artillery_shell",
        "laser_turret",
        "substation",
        "accumulator",
        "solar_panel",
        "portable_solar_panel",
        "productivity_module_1",
        "production_science_pack",
        "steel_chest",
        "logistic_chest",
        "speed_module_1",
        "auto_crafter_3",
        "bulk_inserter",
        "red_splitter",
        "red_underground_belt",
        "landfill",
        "efficiency_module_1",
        "blue_belt",
        "blue_splitter",
        "blue_underground_belt",
    ]
    main_belt = add_misc_factory(
        factory,
        immediate_outputs=immediate_outputs,
        stations=stations,
        default_belt_cap=7.5,
        belt_caps={
            "iron_plate": 15,
            "gear": 15,
            "steel": 15,
            "copper_plate": 15,
            "stone_brick": 15,
            "concrete": 15,
            "plastic": 15,
            "coal": 15,
            "circuit": 15,
            "red_circuit": 15,
            "blue_circuit": 7.5,
            "rail": 30,
            "solid_fuel": 15,

            "belt": 15,
            "iron_stick": 15,
            "copper_wire": 15,
            "pipe": 15,
            "automation_science_pack": 15
        },
        crafter_caps={
            "asp": 30,
            "lsp": 30
        },
        non_productivity_crafter_level=2,
        non_productivity_crafter_modules=(),
        productivity_crafter_level=3,
        productivity_crafter_modules=(Module.PRODUCTION_MODULE_1,)*4
    )
    factory.connect(iron_factory.output_belt, main_belt, "iron_plate", "gear", "steel")
    factory.connect(copper_factory.output_belt, main_belt, "copper_plate")
    factory.connect(stone_factory.output_line, main_belt, "stone", "stone_brick", "concrete")
    factory.connect(chemical_factory.output_line, main_belt, "coal", "plastic", "sulfur", "sulfuric_acid",
                    "explosives", "battery", "solid_fuel", "light_oil", "lubricant")
    factory.connect(circuit_factory.output_line, main_belt, "circuit", "red_circuit", "blue_circuit")
    factory.connect(lds_factory.output_belt, main_belt, "low_density_structure")
    factory.connect(rail_factory.output_belt, main_belt, "rail")
    factory.connect(module_factory.output_line, main_belt, "productivity_module_2", "productivity_module_3",
                    "speed_module_2", "speed_module_3",)
    factory.connect(main_belt, rocket_fuel_line, "rocket_fuel")
    factory.connect(nuclear_factory.output_line, main_belt,
                    "uranium-235", "uranium-238", "nuclear_fuel", "uranium_fuel_cell")

    # add labs
    science_factory = ScienceFactory(
        factory, main_belt,
        max_time=60,
        speed_bonus=.6,
        lab_modules=(Module.PRODUCTION_MODULE_1,)*2,
        science_types=["al", "alm", "alc", "alcp", "alcm", "alcpu", "alcpum"]
    )

    # analyse the factory
    result = factory.full_analyse(print_progress=True)

    # print info
    print(result.display())

    print("\n\n\n")
    science_factory.print_info(result, "alcpum")
    print("")
    print(" --- productivity module 2")
    print(result.single_results[OutputPoint(main_belt, "productivity_module_2")].display())
    print(" --- productivity module 3")
    print(result.single_results[OutputPoint(main_belt, "productivity_module_3")].display())
    print("")
    iron_factory.print_info(result)
    print("")
    copper_factory.print_info(result)
    print("")
    stone_factory.print_info(result)
    print("")
    circuit_factory.print_info(result)
    print("")
    module_factory.print_info(result)
    print("")
    nuclear_factory.print_info(result)


if __name__ == '__main__':
    main()