from helper_classes import Instance 
from helper_functions import get_filtered_data, get_vehicle_dataframe
import pandas as pd
import os
import random
import json



def extract_customer_information_new(filtered_customers:pd.DataFrame, customer:int) -> dict:

    if "Customer ID" not in filtered_customers.columns:
        raise KeyError("Column 'Customer ID' is missing from the DataFrame")
    

    renamed_df = filtered_customers.rename(columns={
        "Customer ID": "ID",
        "x": "X",
        "y": "Y",
        "Demanded Mass": "Demand"
    })

    selected_columns = ["ID", "X", "Y", "Demand"]
    selected_df = renamed_df[selected_columns]

    customer_row = selected_df[selected_df["ID"] == customer]

    nodes_list = customer_row.to_dict(orient="records")
    if not nodes_list:
        raise ValueError(f"No customer found with ID {customer}")

    return nodes_list[0]


def write_json_file_transformation(instance:str,
                                    perm:list[int],
                                    filtered_data,
                                    file_path)  -> None:
    
     
    filename = f"{file_path}/{instance}.json"

    vehicles_json = get_vehicle_dataframe(filtered_data["instance"])

    nodes_json = []
    for customer in perm:
        
        nodes = extract_customer_information_new(filtered_data["customers"], customer)

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
                    "Fragility": fragile_output,
                    "EnableHorizontalRotation": True,
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


def transform_instances(instance:str, df:pd.DataFrame,
                       aggregate_demands:pd.DataFrame,
                       single_demands:pd.DataFrame,
                       items:pd.DataFrame,
                       customers:pd.DataFrame,
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

    # Create dict with filtered dataframes
    filtered_data = get_filtered_data(instance, df, aggregate_demands, single_demands, items, customers)

    # Calculate bounds for number of customers
    max_customers = filtered_data["instance"]["Number of Customers"].values[0]

    #Create list with dummy values for customers
    numbers = list(range(1, max_customers + 1))

    #Define range of possible number of customers
    perm = numbers
    #Create instances with random number of customers

    perm.insert(0, 0) #Add depot at the beginning, if feasible
    

    write_json_file_transformation(instance, perm, filtered_data, file_path)

         

#Alternative create csv for dataframes to avoid loading all instances every time
def main(): 
    instances_data = []
    items = pd.DataFrame()
    single_demands = pd.DataFrame()
    aggregate_demands = pd.DataFrame()
    customers = pd.DataFrame()
    for folder_path in ["Data/Gendreau_et_al_2006"]:
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".txt"):
                if file_name != "Overview.txt":
                    file_path = os.path.join(folder_path, file_name)
                    instance = Instance(file_path, standardize = False, analyze_one_source=False)
                    instances_data.append(instance.to_dict())
                    items = pd.concat([items,instance.items])
                    single_demands = pd.concat([single_demands,instance.demands])
                    aggregate_demands = pd.concat([aggregate_demands,instance.aggregated_demands])
                    customers = pd.concat([customers,instance.customers])

    # Convert list to DataFrame
    df = pd.DataFrame(instances_data)

    random.seed(8)
    file_path = r"C:\Users\mahu123a\Documents\3l-cvrp\data\input\3l-cvrp\gendreau"
    #random.seed(4) old run!
    for instance in df["Instance Name"]:
        transform_instances(instance, df, aggregate_demands, single_demands, items, customers, file_path = file_path)

if __name__ == "__main__":
    print("Creating instances...")
    main()
    print("Finished.")



