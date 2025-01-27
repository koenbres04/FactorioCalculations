from factories import Factory
from factorio_machines import Module
from iron_factory import IronFactory
from copper_factory import CopperFactory
from misc_factory import add_misc_factory
from stone_factory import StoneFactory
from circuit_factory import add_circuit_factory
from chemical_factory import add_chemical_factory
from science_factory import ScienceFactory

def main():
    factory = Factory()
    # global parameters
    resource_bonus = .3

    # add various factories
    iron_factory = IronFactory(
        factory,
        num_drills=96,
        drill_bonus=resource_bonus,
        crafter_level=2,
        output_caps={
            "iron_plate": 30,
            "gear": 15,
            "iron_stick": 7.5,
            "steel": 7.5
        },
        iron_ore_line_cap=7.5
    )

    copper_factory = CopperFactory(
        factory,
        num_drills=50,
        drill_bonus=resource_bonus,
        # output_caps={"copper_plate": 30}
    )

    stone_factory = StoneFactory(
        factory, iron_factory.iron_ore_line,
        num_drills=25,
        drill_bonus=resource_bonus,
        crafter_level=2,
        output_caps={
            "stone": 7.5,
            "stone_brick": 7.5,
            "concrete": 7.5
        }
    )

    chemical_output = add_chemical_factory(
        factory, iron_factory.output_belt, copper_factory.output_belt,
        pumpjack_bonus=resource_bonus,
        coal_rate=15,
        crude_oil_rates=[
            2.6, 2.6, 8.23, 6.88, 4.54, 3.42, 2.94,
            7.05, 33.0, 23.6, 10.1, 20.7, 11.4, 6.31, 22.4, 12.4, 27.6
            # 2, 2, 6, 5, 3, 2, 2,
            # 5, 25, 18, 7, 15, 8, 9, 17, 21, 4,
        ],
        output_caps={
            "coal": 15,
            "plastic": 15,
            "sulfur": 15,
            "explosives": 15,
            "battery": 15,
            "solid_fuel": 7.5
        },
        chemical_plant_modules=(Module.PRODUCTION_MODULE_1,)*3,
        pumpjack_modules=(Module.SPEED_MODULE_1,)*2,
        oil_refinery_modules=(Module.PRODUCTION_MODULE_1,)*3
    )

    circuit_factory_output = add_circuit_factory(
        factory, iron_factory.output_belt, copper_factory.output_belt, chemical_output,
        crafter_level=2,
        output_caps={
            "circuit": 15,
        },
    )

    # add misc factory
    main_belt = add_misc_factory(
        factory,
        crafter_level=2,
        belt_caps={
            "copper_wire": 15,
            "copper_plate": 15,
            "iron_plate": 15,
            "gear": 15,

            "belt": 15,
            "pipe": 15,
            "automation_science_pack": 7.5
        },
        crafter_caps={
            "asp": 20,
            "lsp": 20
        },
    )
    factory.connect(iron_factory.output_belt, main_belt, "iron_plate", "gear", "iron_stick", "steel")
    factory.connect(copper_factory.output_belt, main_belt, "copper_plate")
    factory.connect(stone_factory.output_line, main_belt, "stone", "stone_brick", "concrete")
    factory.connect(chemical_output, main_belt, "coal", "plastic", "sulfur", "sulfuric_acid", "explosives", "battery")
    factory.connect(circuit_factory_output, main_belt, "circuit", "red_circuit", "blue_circuit")

    # add labs
    science_factory = ScienceFactory(
        factory, main_belt,
        max_time=60,
        speed_bonus=.6,
        lab_modules=(Module.PRODUCTION_MODULE_1, Module.PRODUCTION_MODULE_1),
        science_types=["al", "alm", "alc", "alcp", "alcm", "alcpu", "alcpum"]
    )

    # analyse the factory
    result = factory.full_analyse(print_progress=True)

    # print info
    print(result.display())

    print("\n\n\n")
    science_factory.print_info(result, "alcpum")



if __name__ == '__main__':
    main()