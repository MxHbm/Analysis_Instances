import random
import numpy as np
import pandas as pd
import os 

def get_filtered_data(instance:str, df:pd.DataFrame, aggregate_demands:pd.DataFrame, single_demands:pd.DataFrame, items:pd.DataFrame):
    ''' Filter given datasets for particular instance
    Args:
        instance (str): Name of the instance
        df (pd.DataFrame): Instance dataset
        aggregate_demands (pd.DataFrame): Aggregate demands dataset
        single_demands (pd.DataFrame): Single demands dataset
        items (pd.DataFrame): Items dataset
    Returns:
        dict: Dictionary containing filtered datasets
    '''
    return {
        "instance": df[df["Instance Name"] == instance],
        "agg_demands": aggregate_demands[aggregate_demands["Instance Name"] == instance],
        "single_demands": single_demands[single_demands["Instance Name"] == instance],
        "items": items[items["Instance Name"] == instance]
    }

def calculate_bounds(filtered_instance: pd.Dataframe, lb_barrier = 0.25):
    ''' Calculate lower and upper bounds for number of customers
        LB and UB calculated based on vehicle volume and mass lower bounds 

    Args:
        filtered_instance (pd.DataFrame): Filtered instance dataset
        lb_barrier (float): Lower bound barrier - percentage of upper bound
    Returns:
        tuple: Lower bound, upper bound, and number of customers of instance
    '''

    max_customers = filtered_instance["Number of Customers"].values[0]
    volume_lb = filtered_instance["Vehicle LB Volume"].values[0]
    mass_lb = filtered_instance["Vehicle LB Mass"].values[0]

    #Calculate lb and ub
    upper_bound = max(np.ceil(max_customers / volume_lb), np.ceil(max_customers / mass_lb))
    lower_bound = int(lb_barrier * upper_bound)

    return lower_bound, upper_bound, max_customers

def write_header(file:any, filtered_instance:dict) -> None:
    '''
    Write header of the instance file
    Args:
        file (file): File object
        filtered_instance (pd.DataFrame): Filtered instance dataset
    Returns: 
        None
    '''
    for column in ["Number of Customers", "Number of Item Types", "Number of Vehicles", "Time Windows"]:
        value = filtered_instance[column].values[0]
        file.write(f"{column:<30}{value:>10}\n")
    file.write("\nVEHICLE\n")
    for column in ["Vehicle Capacity", "Cargo Length", "Cargo Width", "Cargo Height", "Cargo Volume"]:
        value = filtered_instance[column].values[0]
        file.write(f"{column:<30}{value:>10}\n")

def write_items(file:any, filtered_items: pd.DataFrame) -> None:
    '''
    Write items section of the instance file, all item types needed for tour 
    
    Args:
        file (file): File object
        filtered_items (pd.DataFrame): Filtered items dataset
    '''

    file.write("\nITEMS\n")
    file.write("Type\tLength\tWidth\tHeight\tMass\tFragility\tVolume\n")
    for _, row in filtered_items.iterrows():
        file.write(f"{row['Type']}\t{row['Length']}\t{row['Width']}\t{row['Height']}\t{row['Mass']}\t{row['Fragility']}\t{row['Volume']}\n")

def write_route_and_demand(file:any, perm:list[int], single_demands: pd.DataFrame) -> None:
    '''
        Write Route of Customers and Demand (Item Type and Quantity) per Customer in each row
    Args:
        file (file): File object
        perm (list): List of customers in the route
        single_demands (pd.DataFrame): Single demands dataset
    '''
    file.write("\nROUTE and DEMAND\n")
    for customer in perm:
        file.write(f"{customer}\t")
        customer_demands = single_demands[single_demands["Customer ID"] == str(customer)]
        for _, demand in customer_demands.iterrows():
            file.write(f"{demand['Type']}\t{demand['Quantity']}\t")
        file.write("\n")

def generate_instances(instance:str, df:pd.DataFrame, aggregate_demands:pd.DataFrame, single_demands:pd.DataFrame, items:pd.DataFrame) -> int:
    '''
        Generate train instances with specific customer routes and demands
    Args:       
        instance (str): Name of the instance
        df (pd.DataFrame): Instance dataset
        aggregate_demands (pd.DataFrame): Aggregate demands dataset
        single_demands (pd.DataFrame): Single demands dataset
        items (pd.DataFrame): Items dataset
    Returns:
        int: Number of instances created
    '''

    # Create dict with filtered dataframes
    filtered_data = get_filtered_data(instance, df, aggregate_demands, single_demands, items)

    # Calculate bounds for number of customers
    lower_bound, upper_bound, max_customers = calculate_bounds(filtered_data["instance"])

    #Create list with dummy values for customers
    numbers = list(range(1, max_customers + 1))

    #Counter for created instances
    total_created = 0

    #Define range of possible number of customers
    range_num = int(np.floor(upper_bound - lower_bound))

    #Create instances with random number of customers
    for i in range(range_num):
        random.seed(i)
        num_customers = int(random.uniform(lower_bound, upper_bound)) #Alternative consider all

        for j in range(num_customers):
            
            #Create random permutation of customers
            perm = random.sample(numbers, num_customers)
            #Define filename
            filename = f"Train_data/{instance}_{num_customers}_{j}.txt"

            #Write instance file
            with open(filename, "w") as file:
                write_header(file, filtered_data["instance"])
                write_items(file, filtered_data["items"])
                write_route_and_demand(file, perm, filtered_data["single_demands"])

            total_created += 1

    return total_created