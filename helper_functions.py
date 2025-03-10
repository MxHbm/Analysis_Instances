import random
import numpy as np
import pandas as pd
import os 
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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