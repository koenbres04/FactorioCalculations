from math import ceil


# constants
base_copper_rate_per_drill = 0.5
drill_multiplier = 1.2
yellow_belt_side_rate = 7.5
red_belt_side_rate = 15
base_copper_smelt_time = 3.2
smelter_crafting_speed = 2

# apply multipliers
copper_rate_per_drill = base_copper_rate_per_drill * drill_multiplier
copper_smelt_rate_per_smelter = smelter_crafting_speed/base_copper_smelt_time

# see max number of drills per belt side
num_drills_per_yellow_belt_side = yellow_belt_side_rate / copper_rate_per_drill
print(f"{num_drills_per_yellow_belt_side = :.2f}")
num_drills_per_red_belt_side = red_belt_side_rate / copper_rate_per_drill
print(f"{num_drills_per_red_belt_side = :.2f}")

# factory specific constants
num_copper_drills = 4*6+5+4+2

# results
raw_copper_rate = copper_rate_per_drill*num_copper_drills
num_smelters = raw_copper_rate/copper_smelt_rate_per_smelter
print(f"number of smelters: {ceil(num_smelters)}")
print(f"copper plate rate: {raw_copper_rate:.2f}")