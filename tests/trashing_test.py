from facalc.factories import Factory, OutputPoint
from facalc.factorio_machines import (OilRefinery, OilRefineryRecipe, Crafter, CrafterRecipe)

def main():
    factory = Factory()

    a_source = factory.add_source("A", 10)
    refineries = factory.add_machine_group(OilRefinery(OilRefineryRecipe(
        time=1.,
        name="A to B+C",
        inp={"A": 1.},
        outp={"B": 1., "C": 2., "E": 1.5},
        supports_prod_modules=False
    )))
    factory.connect(a_source, refineries)

    main_line = factory.add_buffer("main_line")
    factory.connect(refineries, main_line, "B", "C")
    factory.add_trash_point(main_line, "C")
    factory.add_trash_point(refineries, "E")
    # temp_buffer = factory.add_buffer("temp_buffer")
    # factory.connect(refineries, temp_buffer, "E")

    crafters = factory.add_machine_group(Crafter(CrafterRecipe(
        time=1.,
        outp="D",
        outp_count=1,
        inp={"B": 1, "C": 1},
        supports_prod_modules=False
    ), 1))
    factory.connect(main_line, crafters, "B", "C")
    factory.connect(crafters, main_line, "D")
    factory.add_output_point(OutputPoint(main_line, "D"))

    results = factory.full_analyse()
    print(results.display_full())

if __name__ == '__main__':
    main()