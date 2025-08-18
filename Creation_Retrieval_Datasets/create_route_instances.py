from helper_classes import Instance 
from helper_functions import get_filtered_data, get_vehicle_dataframe
import pandas as pd
import os
import random
import time
import json
from itertools import product, chain

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
                    file_path) -> None:
     
    filename = f"{file_path}/{instance}_{num_customers}_{j}.json"

    vehicles_json = get_vehicle_dataframe(filtered_data["instance"])

    nodes_json = []
    for customer in perm:
        
        node = extract_customer_information(filtered_data["customers"], customer)

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

        node.update({"Items": node_items})
        nodes_json.append(node)

    name_in_file = filename.split("/")[-1].split(".")[0]
    data = {
        "Name": name_in_file,
        "Vehicles": vehicles_json,
        "Nodes": nodes_json
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def generate_instances(instance:str,
                       df:pd.DataFrame,
                       aggregate_demands:pd.DataFrame,
                       single_demands:pd.DataFrame,
                       items:pd.DataFrame,
                       customers:pd.DataFrame,
                       file_path,
                       multiplierCustomerNumber:int = 2,
                       attemptLimit:int = 40, 
                       succesfulInstancesThreshold: int = 40) -> int:
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

    # Retrieve max customers
    max_customers = filtered_data["instance"]["Number of Customers"].values[0]

    #Create list with dummy values for customers
    numbers = list(range(1, max_customers + 1))

    #Upper Bounds limit for number of customers 
    max_weight = filtered_data["instance"]["Vehicle Capacity"].values[0]
    max_volume = filtered_data["instance"]["Cargo Length"].values[0] * filtered_data["instance"]["Cargo Width"].values[0] * filtered_data["instance"]["Cargo Height"].values[0] 

    #Counter for created instances
    total_created = 0
    total_duplicates = 0
    # Cache dicts for aggregated demand to avoid repeated lookups
    agg_volume_dict = dict(zip(filtered_data["agg_demands"]["Customer ID"].astype(int),
                           filtered_data["agg_demands"]["Agg Volume"]))
    agg_mass_dict = dict(zip(filtered_data["agg_demands"]["Customer ID"].astype(int),
                         filtered_data["agg_demands"]["Agg Mass"]))
    
    #Create instances with random number of customers
    exit_outer_loop = False

    for num_customers in numbers[1:]:

        if exit_outer_loop: break
        checked_routes_set = {(0,0)}

        exit_outer_loop_counter = 0

        for j in range(num_customers * multiplierCustomerNumber):

            succesful_instances = 0
            attempts = 0
            breakup = 0
            found_succesful_tour = False

            while(succesful_instances < succesfulInstancesThreshold):

                perm = random.sample(numbers, num_customers)
                if tuple(perm) in checked_routes_set: 
                    total_duplicates += 1
                    breakup += 1
                else:

                    checked_routes_set.add(tuple(perm))

                    total_volume = sum(agg_volume_dict.get(c, 0) for c in perm)
                    total_weight = sum(agg_mass_dict.get(c, 0) for c in perm)

                    if total_volume > max_volume or total_weight > max_weight:
                        attempts += 1
                    else:

                        perm.insert(0, 0) #Add depot at the beginning, if feasible

                        write_json_file(instance,num_customers, j * succesfulInstancesThreshold + succesful_instances, perm, filtered_data, file_path)

                        succesful_instances += 1
                        total_created += 1
                        attempts = 0
                        breakup = 0
                        found_succesful_tour = True
                        continue

                if(attempts >= attemptLimit):
                    attempts = 0
                    breakup += 1

                if(breakup >= succesfulInstancesThreshold):
                    if(not found_succesful_tour):
                        exit_outer_loop_counter += 1
                        #print(f"Current j: {j} - Exit outer loop: {exit_outer_loop_counter} with current breakups {breakup}")
                    break

        if exit_outer_loop_counter >= num_customers * multiplierCustomerNumber: 
            exit_outer_loop = True

    return total_created, total_duplicates

#Alternative create csv for dataframes to avoid loading all instances every time
def main(): 
    instances_data = []
    items = pd.DataFrame()
    single_demands = pd.DataFrame()
    aggregate_demands = pd.DataFrame()
    customers = pd.DataFrame()
    for folder_path in ["Data/Krebs_Ehmke_Koch_2021"]:
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


    instances = [file.split(".json")[0] for file in os.listdir("Data/RandomSet_krebs")]
    random.seed(8)
    save_file_path_base = r"H:\Data\RandomDataGeneration_Krebs"
    multiplierCustomerNumbers = [1,2,3]
    attemptLimits = [10,20]
    succesfulInstancesThresholds = [10,20]
    for multiplierCustomerNumber, attemptLimit, succesfulInstancesThreshold in product(multiplierCustomerNumbers, attemptLimits, succesfulInstancesThresholds):
        
        start_time = time.time()
        sub_folder_name = f"RandomData_{multiplierCustomerNumber}_{attemptLimit}_{succesfulInstancesThreshold}"
        os.makedirs(os.path.join(save_file_path_base,sub_folder_name),exist_ok=True)
        output_file_path = os.path.join(save_file_path_base,sub_folder_name,"input")
        os.makedirs(output_file_path,exist_ok=True)
        os.makedirs(os.path.join(save_file_path_base,sub_folder_name,"output"),exist_ok=True)

        total_instances = 0
        total_duplicates = 0
        for selected_instance in instances:
            success, duplicated = generate_instances(instance = selected_instance,
                                                    df = df,
                                                    aggregate_demands = aggregate_demands,
                                                    single_demands = single_demands,
                                                    items = items,
                                                    customers = customers,
                                                    file_path = output_file_path,
                                                    multiplierCustomerNumber = multiplierCustomerNumber,
                                                    attemptLimit = attemptLimit, 
                                                    succesfulInstancesThreshold = succesfulInstancesThreshold)
            
            total_instances += success
            total_duplicates += duplicated
            #print(f"{sub_folder_name} - Instance: {selected_instance} - Instances generated: {success} - Duplicates avoided: {duplicated}")
        end_time = time.time()
        worktime = round(end_time-start_time,2)
        print(f"{sub_folder_name} - Created instances: {total_instances} and avoided {total_duplicates} duplicates in {worktime} s")

if __name__ == "__main__":
    print("Creating instances...")
    main()
    print("Finished.")

