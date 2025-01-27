from math import ceil


# constants
base_iron_rate_per_drill = 0.5
drill_multiplier = 1.2
yellow_belt_side_rate = 7.5
red_belt_side_rate = 15
base_iron_smelt_time = 3.2
smelter_crafting_speed = 2
drill_power_use = 9e4
smelter_power_use = 186e3
crafter_speed = 0.75
gear_craft_time = 0.5
rod_craft_time = 0.5
steel_smelt_time = 16



# apply multipliers
iron_rate_per_drill = base_iron_rate_per_drill * drill_multiplier
iron_smelt_rate_per_smelter = smelter_crafting_speed/base_iron_smelt_time

# see max number of drills per belt side
num_drills_per_yellow_belt_side = yellow_belt_side_rate / iron_rate_per_drill
print(f"{num_drills_per_yellow_belt_side = :.2f}")
num_drills_per_red_belt_side = red_belt_side_rate / iron_rate_per_drill
print(f"{num_drills_per_red_belt_side = :.2f}")


# goals
goal_plate_rate = 15
goal_gear_rate = 15
goal_rod_rate = 7.5
goal_steel_rate = 3.25

total_goal_rate = (
        goal_plate_rate +
        2*goal_gear_rate +
        0.5*goal_rod_rate +
        5*goal_steel_rate
)
print(f"{total_goal_rate = } = {total_goal_rate/15:.2f} red belt sides")

# factory specific constants
num_iron_drills = 96

# results
power_use = 0

raw_iron_rate = iron_rate_per_drill*num_iron_drills
power_use += drill_power_use*num_iron_drills
num_plate_smelters = raw_iron_rate/iron_smelt_rate_per_smelter
power_use += smelter_power_use*num_plate_smelters
print(f"number of smelters: {ceil(num_plate_smelters)}")
print(f"iron plate rate: {raw_iron_rate:.2f}")

gear_craft_rate_per_crafter = crafter_speed/gear_craft_time
num_gear_crafters = goal_gear_rate/gear_craft_rate_per_crafter
print(f"number of gear crafters: {ceil(num_gear_crafters)}")
rod_craft_rate_per_crafter = 2*crafter_speed/rod_craft_time
num_rod_crafters = goal_rod_rate/rod_craft_rate_per_crafter
print(f"number of rod crafters: {ceil(num_rod_crafters)}")

steel_rate_per_smelter = smelter_crafting_speed/steel_smelt_time
num_steel_smelters = goal_steel_rate/steel_rate_per_smelter
iron_for_steel_rate = 5*num_steel_smelters
print(f"rate of steel needed for iron: {iron_for_steel_rate:.2f}")
print(f"number of steel smelter: {ceil(num_steel_smelters)}")


print(f"power use: {power_use/1e6:.1f} MW")
