import random
import numpy as np
import pandas as pd
import os 
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
from datetime import datetime

def get_filtered_data(instance:str, df:pd.DataFrame, aggregate_demands:pd.DataFrame, single_demands:pd.DataFrame, items:pd.DataFrame, customers:pd.DataFrame) -> dict:
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

    filtered_customers =  customers[customers["Instance Name"] == instance].drop(columns=["Instance Name", "Folder Name"])

    return {
        "instance": df[df["Instance Name"] == instance],
        "agg_demands": aggregate_demands[aggregate_demands["Instance Name"] == instance],
        "single_demands": single_demands[single_demands["Instance Name"] == instance],
        "items": items[items["Instance Name"] == instance],
        "customers": filtered_customers
    }

def calculate_bounds(filtered_instance: pd.DataFrame, lb_barrier = 0.25):
    ''' Calculate lower and upper bounds for number of customers
        LB and UB calculated based on vehicle volume and mass lower bounds 

    Args:
        filtered_instance (pd.DataFrame): Filtered instance dataset
        lb_barrier (float): Lower bound barrier - percentage of upper bound
    Returns:
        tuple: Lower bound, upper bound, and number of customers of instance
    '''

    max_customers = filtered_instance["Number of Customers"].values[0]
    volume_lb = max(filtered_instance["Vehicle LB Volume"].values[0],1)
    mass_lb = max(filtered_instance["Vehicle LB Mass"].values[0],1)

    #Calculate lb and ub
    upper_bound = max(np.ceil(max_customers / volume_lb), np.ceil(max_customers / mass_lb))

    return upper_bound, max_customers

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


def write_txt_file(instance:str,
                   num_customers:int,
                   j:int,
                   perm:list[int],
                   filtered_data,
                   file_path,
                   date) -> None:
     
    filename = f"{file_path}/{instance}_{num_customers}_{j}_{date}.txt"

    #Write instance file
    with open(filename, "w") as file:
        write_header(file, filtered_data["instance"])
        write_items(file, filtered_data["items"])
        write_route_and_demand(file, perm, filtered_data["single_demands"])

def get_vehicle_dataframe(filtered_instance:pd.DataFrame) -> dict:
    '''
    Create a dataframe with vehicle information
    Args:
        filtered_instance (pd.DataFrame): Filtered instance dataset
    Returns:
        pd.DataFrame: Dataframe with vehicle information
    '''
    return pd.DataFrame([
            {
                "Capacity": int(filtered_instance["Vehicle Capacity"].values[0]),
                "Length": int(filtered_instance["Cargo Length"].values[0]),
                "Width": int(filtered_instance["Cargo Width"].values[0]),
                "Height": int(filtered_instance["Cargo Height"].values[0])
            } for _ in range(filtered_instance["Number of Vehicles"].values[0])
        ]).to_dict(orient="records")

def extract_customer_information(filtered_customers:pd.DataFrame, customer:int) -> dict:

    if "Customer ID" not in filtered_customers.columns:
        raise KeyError("Column 'Customer ID' is missing from the DataFrame")

    refiltered_customers = filtered_customers[filtered_customers["Customer ID"] == customer]

    nodes_list = refiltered_customers.to_dict(orient="records")
    
    if not nodes_list:
        raise ValueError("No customers found")
    nodes = nodes_list[0] 

    return nodes

def write_json_file(instance:str,
                    num_customers:int,
                    j:int,
                    perm:list[int],
                    filtered_data,
                    file_path,
                    date) -> None:
     
    filename = f"{file_path}/{instance}_{num_customers}_{j}_{date}.json"

    vehicles_json = get_vehicle_dataframe(filtered_data["instance"])

    nodes_json = []
    for customer in perm:
        
        nodes = extract_customer_information(filtered_data["customers"], customer)

        node_items = []
        for _, single_demand in filtered_data["single_demands"][filtered_data["single_demands"]["Customer ID"] == str(customer)].iterrows():
            refiltered_items = filtered_data["items"][filtered_data["items"]["Type"] == single_demand["Type"]]

            if not refiltered_items.empty:
                first_item = refiltered_items.iloc[0]  # Safe indexing

                fragile_output = "Fragile" if first_item["Fragility"] == 1 else "None"

                node_items.append({
                    "Quantity": int(single_demand["Quantity"]),
                    "Weight": float(first_item["Mass"]),
                    "Length": int(first_item["Length"]),
                    "Width": int(first_item["Width"]),
                    "Height": int(first_item["Height"]),
                    "Volume": int(first_item["Volume"]),
                    "Fragility": fragile_output,
                    "EnableHorizontalRotation": int(True),
                    "Rotated": "None"
                })

        nodes.update({"Items": node_items})
        nodes_json.append(nodes)

    name_in_file = filename.split("/")[-1].split(".")[0]
    data = {
        "Name": name_in_file,
        "Vehicles": vehicles_json,
        "Nodes": nodes_json
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)



def generate_instances(instance:str, df:pd.DataFrame,
                       aggregate_demands:pd.DataFrame,
                       single_demands:pd.DataFrame,
                       items:pd.DataFrame,
                       customers:pd.DataFrame,
                       write_txt_file_bool:bool,
                       file_path) -> int:
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

    # Generate today string
    today = datetime.today()
    formatted_date = today.strftime('%d%m%y')

    # Create dict with filtered dataframes
    filtered_data = get_filtered_data(instance, df, aggregate_demands, single_demands, items, customers)

    # Calculate bounds for number of customers
    upper_bound, max_customers = calculate_bounds(filtered_data["instance"])
    max_customers = filtered_data["instance"]["Number of Customers"].values[0]

    #Create list with dummy values for customers
    numbers = list(range(1, max_customers + 1))

    #Upper Bounds limit for number of customers 
    max_weight = filtered_data["instance"]["Vehicle Capacity"].values[0]
    max_volume = filtered_data["instance"]["Cargo Length"].values[0] * filtered_data["instance"]["Cargo Width"].values[0] * filtered_data["instance"]["Cargo Height"].values[0] 

    #Counter for created instances
    total_created = 0

    random.seed(42)

    # Cache dicts for aggregated demand to avoid repeated lookups
    agg_volume_dict = dict(zip(filtered_data["agg_demands"]["Customer ID"].astype(int),
                           filtered_data["agg_demands"]["Agg Volume"]))
    agg_mass_dict = dict(zip(filtered_data["agg_demands"]["Customer ID"].astype(int),
                         filtered_data["agg_demands"]["Agg Mass"]))

    #Define range of possible number of customers
    num_customers_list = random.sample(numbers, int(np.floor(upper_bound)))
    #Create instances with random number of customers
    for num_customers in num_customers_list:

        for j in range(num_customers):
            feasible = True
            attempts = 0

            while(feasible and attempts < 10):
                #Create random permutation of customers
                perm = random.sample(numbers, num_customers)

                total_volume = sum(agg_volume_dict.get(c, 0) for c in perm)
                total_weight = sum(agg_mass_dict.get(c, 0) for c in perm)


                if total_volume > max_volume or total_weight > max_weight:
                    attempts += 1
                    continue

                perm.insert(0, 0) #Add depot at the beginning, if feasible
                feasible = False
                
                if write_txt_file_bool:
                    write_txt_file(instance, num_customers, j, perm, filtered_data, file_path, formatted_date)
                else: 
                    write_json_file(instance,num_customers,j, perm, filtered_data, file_path, formatted_date)

                total_created += 1

    return total_created


def plot_boxplot(data:pd.DataFrame, column:str, order: list) -> None: 
    '''
    Create a boxplot consisting of three subplots for each level of the first order element [Number of Customers or Item Types !!!]

    Args: 
        data (pd.DataFrame): Dataframe containing the data
        column (str): Column to be plotted
        order (list): List of order of the elements
        title (str): Title of the plot
    '''
    # Set global style for a scientific look
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["axes.labelsize"] = 10
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["xtick.labelsize"] = 8
    plt.rcParams["ytick.labelsize"] = 10

    first_unique_list = sorted(list(data[order[0]].unique()))
    second_unique_list = sorted(list(data[order[1]].unique()))
    third_unique_list = sorted(list(data[order[2]].unique()))

    # Use blue-green shades for a professional look
    blue_palette = sns.color_palette("Blues", len(second_unique_list) + len(first_unique_list))
    colors = blue_palette

    # Create figure and subplots (3 rows for different item types)
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(10, 6), sharey=True)
    plt.subplots_adjust(hspace=0.4)  # Adjust spacing

    # Loop through each item type level (m)
    for i, m in enumerate(first_unique_list):
        ax = axes[i]  # Select subplot for this row
        box_data = []
        box_labels = []
        box_colors = []

        for n_idx, n in enumerate(second_unique_list):
            for k_idx, k in enumerate(third_unique_list):
                # Filter data
                filtered_data = data[
                    (data[order[0]] == m) &
                    (data[order[1]] == n) &
                    (data[order[2]] == k)
                ]

                if not filtered_data.empty:
                    box_data.append(filtered_data[column].values)
                    box_colors.append(colors[n_idx * len(third_unique_list) + k_idx])  # Assign color
                    #box_colors.append(colors[0])  # Assign color
                    box_labels.append(f"$n={n}$\n$k={k}$")  # Newline for better formatting

        # Plot boxplot for the current m level
        boxplot = ax.boxplot(
            box_data, patch_artist=True, labels=box_labels if i == len(first_unique_list) - 1 else None,
            medianprops={"color": "black", "linewidth": 2}
        )

        # Apply colors to each box
        for patch, color in zip(boxplot["boxes"], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.8)  # Add slight transparency
            patch.set_edgecolor("black")  # Add black borders

        # Grid and aesthetics
        ax.yaxis.grid(True, linestyle="--", alpha=0.4)
        ax.set_title(f"{order[0].split(' ')[-1]}: $m={m}$", fontsize=13)

        # Remove x labels for the first two rows
        if i < len(first_unique_list) - 1:
            ax.set_xticklabels([])  # Hide labels
            ax.set_xticks([])  # Remove ticks completely
        else:
            ax.tick_params(axis="x", rotation=0, labelsize=10)

    # Global title and layout
    plt.suptitle(f"{column} over instance types", fontsize=15)
    fig.text(0.06, 0.5, f"{column}", va="center", rotation="vertical", fontsize=14)

    # Show plot
    plt.show()