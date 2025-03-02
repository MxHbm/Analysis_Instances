import random
import numpy as np

def get_filtered_data(instance, df, aggregate_demands, single_demands, items):
    return {
        "instance": df[df["Instance Name"] == instance],
        "agg_demands": aggregate_demands[aggregate_demands["Instance Name"] == instance],
        "single_demands": single_demands[single_demands["Instance Name"] == instance],
        "items": items[items["Instance Name"] == instance]
    }

def calculate_bounds(filtered_instance):
    num_customers = filtered_instance["Number of Customers"].values[0]
    volume_lb = filtered_instance["Vehicle LB Volume"].values[0]
    mass_lb = filtered_instance["Vehicle LB Mass"].values[0]
    upper_bound = max(np.ceil(num_customers / volume_lb), np.ceil(num_customers / mass_lb))
    lower_bound = int(0.25 * upper_bound)
    return lower_bound, upper_bound, num_customers

def write_header(file, filtered_instance):
    for column in ["Number of Customers", "Number of Item Types", "Number of Vehicles", "Time Windows"]:
        value = filtered_instance[column].values[0]
        file.write(f"{column:<30}{value:>10}\n")
    file.write("\nVEHICLE\n")
    for column in ["Vehicle Capacity", "Cargo Length", "Cargo Width", "Cargo Height", "Cargo Volume"]:
        value = filtered_instance[column].values[0]
        file.write(f"{column:<30}{value:>10}\n")

def write_items(file, filtered_items):
    file.write("\nITEMS\n")
    file.write("Type\tLength\tWidth\tHeight\tMass\tFragility\tVolume\n")
    for _, row in filtered_items.iterrows():
        file.write(f"{row['Type']}\t{row['Length']}\t{row['Width']}\t{row['Height']}\t{row['Mass']}\t{row['Fragility']}\t{row['Volume']}\n")

def write_route_and_demand(file, perm, single_demands):
    file.write("\nROUTE and DEMAND\n")
    for customer in perm:
        file.write(f"{customer}\t")
        customer_demands = single_demands[single_demands["Customer ID"] == str(customer)]
        for _, demand in customer_demands.iterrows():
            file.write(f"{demand['Type']}\t{demand['Quantity']}\t")
        file.write("\n")

def generate_instances(instance, df, aggregate_demands, single_demands, items):
    filtered_data = get_filtered_data(instance, df, aggregate_demands, single_demands, items)
    lower_bound, upper_bound, max_customers = calculate_bounds(filtered_data["instance"])
    numbers = list(range(1, max_customers + 1))
    total_created = 0
    range_num = int(np.floor(upper_bound - lower_bound))

    for i in range(range_num):
        random.seed(i)
        num_customers = int(random.uniform(lower_bound, upper_bound))
        for j in range(num_customers):
            perm = random.sample(numbers, num_customers)
            filename = f"Train_data/{instance}_{num_customers}_{j}.txt"
            with open(filename, "w") as file:
                write_header(file, filtered_data["instance"])
                write_items(file, filtered_data["items"])
                write_route_and_demand(file, perm, filtered_data["single_demands"])
            total_created += 1

    return total_created