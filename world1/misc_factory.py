from itertools import chain
from facalc.factories import Factory, OutputPoint
from facalc.factorio_machines import Crafter, CRAFTER_RECIPES, Module

def add_misc_factory(
        factory: Factory,
        immediate_outputs: list[str],
        stations: list[str],
        productivity_crafter_level: int,
        non_productivity_crafter_level: int,
        productivity_crafter_modules: tuple[Module, ...] = (),
        non_productivity_crafter_modules: tuple[Module, ...] = (),
        crafter_caps: dict[str, float] | None = None,
        belt_caps: dict[str, float] | None = None,
        default_belt_cap: float | None = None
):

    if crafter_caps is None:
        crafter_caps = dict()
    if default_belt_cap is not None:
        if belt_caps is None:
            belt_caps = dict()
        for key in chain(immediate_outputs, stations):
            if key not in belt_caps:
                belt_caps[key] = default_belt_cap

    main_belt = factory.add_buffer("main belt", rate_caps=belt_caps)
    # add immediate outputs
    for material in immediate_outputs:
        factory.add_output_point(OutputPoint(main_belt, material))

    # add crafters
    for material in stations:
        recipe = CRAFTER_RECIPES[material]
        if recipe.supports_prod_modules:
            crafter_type = Crafter(recipe, productivity_crafter_level, productivity_crafter_modules)
        else:
            crafter_type = Crafter(recipe, non_productivity_crafter_level, non_productivity_crafter_modules)
        if material in crafter_caps:
            crafters = factory.add_machine_group(crafter_type, crafter_caps[material])
        else:
            crafters = factory.add_machine_group(crafter_type)
        factory.connect(crafters, main_belt, material)
        for inp in recipe.inp.keys():
            factory.connect(main_belt, crafters, inp)
        factory.add_output_point(OutputPoint(main_belt, material))

    return main_belt
