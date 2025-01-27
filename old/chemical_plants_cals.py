from math import ceil

pumpjack_rates = [
    4.67, 4.2, 27.0, 14.8, 14.3, 8.16, 6.17,
    35.7, 16.9, 28.1, 18.5, 25.4, 18.8, 30.8, 14.4, 26.6, 19.7
]
total_oil_rate = sum(pumpjack_rates)
oil_use_rate_per_refinery = 100/5
gas_rate_per_refinery = 55/5
oil2gas = 55 / 100
oil2heavy_oil = 25/100
oil2light_oil = 45/100
lubricant_rate_per_plant = 10
heavy_oil2lubricant = 1

print("-------- flamethrower ammo")
oil_in = 20
steel_in = 1
flamethrower_ammo_out = 2
craft_time = 6
num_plants = total_oil_rate/(oil_in/craft_time)
print(f"plant count: {ceil(num_plants)}")
print(f"steel rate: {num_plants*steel_in/craft_time:.2f}")
print(f"flamethrower ammo out rate: {num_plants*flamethrower_ammo_out/craft_time:.2f}")


print("-------- oil refining")
num_refineries = total_oil_rate/oil_use_rate_per_refinery
print(f"{ceil(num_refineries) = }")
total_gas_rate = oil2gas * total_oil_rate
total_heavy_oil_rate = oil2heavy_oil*total_oil_rate
total_light_oil_rate = oil2light_oil*total_oil_rate
print(f"gas rate: {total_gas_rate:.2f}")
print(f"light oil rate: {total_light_oil_rate:.2f}")
num_gas_fuel_plants = total_gas_rate/20
print(f"gas fuel plants: {ceil(num_gas_fuel_plants)}")
num_heavy_oil_fuel_plants = total_heavy_oil_rate/20
print(f"heavy oil fuel plants: {ceil(num_heavy_oil_fuel_plants)}")
num_light_oil_fuel_plants = total_light_oil_rate/20
print(f"light oil fuel plants: {ceil(num_light_oil_fuel_plants)}")

print("-------- plastic")
gas_in = 20
coal_in = 1
plastic_out = 2
craft_time = 1
num_plants = total_gas_rate/(gas_in/craft_time)
print(f"plant count: {ceil(num_plants)}")
print(f"coal rate: {num_plants*coal_in/craft_time:.2f}")
print(f"plastic out rate: {num_plants*plastic_out/craft_time:.2f}")

print("-------- sulfur")
gas_in = 30
water_in = 30
sulfur_out = 2
craft_time = 1
num_plants = total_gas_rate/(gas_in/craft_time)
print(f"plant count: {ceil(num_plants)}")
print(f"water rate: {num_plants*water_in/craft_time:.2f}")
sulfur_out_rate = num_plants*sulfur_out/craft_time
print(f"sulfur out rate: {sulfur_out_rate:.2f}")

print("-------- explosives")
coal_in = 1
sulfur_in = 1
water_in = 10
explosives_out = 2
craft_time = 4
num_plants = sulfur_out_rate/(sulfur_in/craft_time)
print(f"plant count: {ceil(num_plants)}")
print(f"coal rate: {num_plants*coal_in/craft_time:.2f}")
print(f"water rate: {num_plants*water_in/craft_time:.2f}")
print(f"explosives rate: {num_plants*explosives_out/craft_time:.2f}")


print("-------- sulfuric acid")
iron_plate_in = 1
sulfur_in = 5
water_in = 100
sulfuric_acid_out = 50
craft_time = 1
num_plants = sulfur_out_rate/(sulfur_in/craft_time)
print(f"plant count: {ceil(num_plants)}")
print(f"iron plate rate: {num_plants*iron_plate_in/craft_time:.2f}")
print(f"water rate: {num_plants*water_in/craft_time:.2f}")
sulfuric_acid_out_rate = num_plants*sulfuric_acid_out/craft_time
print(f"sulfuric acid rate: {sulfuric_acid_out_rate:.2f}")

print("--------- battery rate")
iron_plate_in = 1
copper_plate_in = 1
sulfuric_acid_in = 20
battery_out = 1
craft_time = 4
num_plants = sulfuric_acid_out_rate/(sulfuric_acid_in/craft_time)
print(f"plant count: {ceil(num_plants)}")
print(f"iron plate rate: {num_plants*iron_plate_in/craft_time:.2f}")
print(f"copper plate rate: {num_plants*copper_plate_in/craft_time:.2f}")
print(f"battery rate: {num_plants*battery_out/craft_time:.2f}")


print("--------- lubricant")
num_plants = total_oil_rate/(lubricant_rate_per_plant/heavy_oil2lubricant)
total_lubricant_rate = num_plants*lubricant_rate_per_plant
print(f"plant count: {ceil(num_plants)}")
print(f"lubrican rate: {total_lubricant_rate:.2f}")


