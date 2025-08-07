from helper_classes import Instance 
import pandas as pd
import os


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
    prefix ="gendreau"


    file_path = r"H:\Data\CSV_Datasets_Route_Completion"

    df.to_csv(os.path.join(file_path, f"{prefix}_instance_data.csv"), index=False)
    aggregate_demands.to_csv(os.path.join(file_path, f"{prefix}_agg_demand.csv"), index=False)
    single_demands.to_csv(os.path.join(file_path, f"{prefix}_single_demands.csv"), index=False)
    items.to_csv(os.path.join(file_path, f"{prefix}_items.csv"), index=False)
    customers.to_csv(os.path.join(file_path, f"{prefix}_customers.csv"), index=False)
    

if __name__ == "__main__":
    print("Creating instances...")
    main()
    print("Finished.")

