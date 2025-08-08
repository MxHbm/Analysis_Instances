import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


####################################################################################################################################################################
####################################################################################################################################################################
########################################## helper Functions - Generate Random Routes #############################################################################
####################################################################################################################################################################
####################################################################################################################################################################

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




####################################################################################################################################################################
####################################################################################################################################################################
########################################## Plot Functions #############################################################################
####################################################################################################################################################################
####################################################################################################################################################################

def plot_boxplot(data:pd.DataFrame, column:str, order: list) -> None: 
    '''
    Create a boxplot consisting of three subplots for each level of the first order element [Number of Customers or Item Types !!!]

    Args: 
        data (pd.DataFrame): Dataframe containing the data
        column (str): Column to be plotted
        order (list): List of order of the elements
        title (str): Title of the plot
    '''
    # Set global style for scientific look
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10
    plt.rcParams["grid.alpha"] = 0.3

    max_volume = 60*25*30

    first_unique_list = sorted(list(data[order[0]].unique()))
    second_unique_list = sorted(list(data[order[1]].unique()))
    third_unique_list = sorted(list(data[order[2]].unique()))

    # Use blue-green shades for a professional look
    blue_palette = sns.color_palette("Blues", len(second_unique_list) + len(first_unique_list))
    colors = blue_palette

    # Create figure and subplots (3 rows for different item types)
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 7), sharey=True)
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
                    if column == "Volume":
                        box_data.append(filtered_data[column].values/ max_volume)
                    else: 
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
        ax.yaxis.grid(True, linestyle="--", alpha=0.3)
        ax.set_title(f"{order[0].split(' ')[-1]}: $m={m}$", fontsize=13)

        # Remove x labels for the first two rows
        if i < len(first_unique_list) - 1:
            ax.set_xticklabels([])  # Hide labels
            ax.set_xticks([])  # Remove ticks completely
        else:
            ax.tick_params(axis="x", rotation=0, labelsize=10)

    # Global title and layout
    if column == "Volume": 
    
        plt.suptitle(f"Rel. {column} over instance types", fontsize=16)
        fig.text(0.07, 0.5, f"Rel. {column}", va="center", rotation="vertical", fontsize=14)

    else:
        plt.suptitle(f"{column} over instance types", fontsize=15)
        fig.text(0.06, 0.5, f"{column}", va="center", rotation="vertical", fontsize=14)
    # Show plot
    plt.show()