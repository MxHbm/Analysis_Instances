from helper_classes import Instance 
from helper_functions import generate_instances
import pandas as pd
import os
import random

#Alternative create csv for dataframes to avoid loading all instances every time
def main(): 
    instances_data = []
    items = pd.DataFrame()
    single_demands = pd.DataFrame()
    aggregate_demands = pd.DataFrame()
    customers = pd.DataFrame()
    for folder_path in ["Gendreau_et_al_2006"]:
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
    save_file_path = r"C:\Users\mahu123a\Documents\Data_Classifier_Old\4_Gendreau_New_Instances_NewRoutePseudocode/test_input"
    #random.seed(4) old run!
    #instances = random.choices(df["Instance Name"], k=1)
    instances = df["Instance Name"]
    total_instances = 0
    total_duplicates = 0
    for selected_instance in instances:
        success, duplicated = generate_instances(instance = selected_instance,
                                                df = df,
                                                aggregate_demands = aggregate_demands,
                                                single_demands = single_demands,
                                                items = items,
                                                customers = customers,
                                                write_txt_file_bool = False,
                                                file_path = save_file_path,
                                                multiplierCustomerNumber = 5,
                                                attemptLimit = 40, 
                                                succesfulInstancesThreshold = 40)
        
        total_instances += success
        total_duplicates += duplicated
        print(f"Instance: {selected_instance} - Instances generated: {success} - Duplicates avoided: {duplicated}")
       
    print(f"Created instances: {total_instances} and avoided {total_duplicates} duplicates")

if __name__ == "__main__":
    print("Creating instances...")
    main()
    print("Finished.")

