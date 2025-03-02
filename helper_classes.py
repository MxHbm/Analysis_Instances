import os
import pandas as pd
import numpy as np

class Item: 

    def __init__(self, folder_name:str, instance_name:str, type:str, length:float, width:float, height:float, mass:float):
        """ Initialize instance by reading the file and extracting data """
        self.folder_name = folder_name
        self.instance_name = instance_name
        self.type = type
        self.length = length
        self.width = width
        self.height = height
        self.mass = mass
        self.volume = length * width * height
        self.relative_width = 0
        self.relative_height = 0
        self.relative_length = 0
        self.relative_mass = 0
        self.relative_volume = 0

    def __print__(self): 
    
        print("Instance Name: ", self.instance_name)
        print("Type: ", self.type)
        print("Length: ", self.length)
        print("Width: ", self.width)
        print("Height: ", self.height)
        print("Mass: ", self.mass)
        print("Volume: ", self.volume)

    def caclulate_relative_values(self, cargoSpace_Length, cargoSpace_Width, cargoSpace_Height, vehicle_capacity):

        self.relative_width = self.width / cargoSpace_Width
        self.relative_height = self.height / cargoSpace_Height
        self.relative_mass = self.mass / vehicle_capacity
        self.relative_volume = self.volume / (cargoSpace_Length * cargoSpace_Width * cargoSpace_Height)
        self.relative_length = self.length / cargoSpace_Length

    def to_dict(self):
        """ Convert instance data to a dictionary for DataFrame storage """
        return {
            "Folder Name": self.folder_name,
            "Instance Name": self.instance_name,
            "Type": self.type,
            "Length": self.length,
            "Width": self.width,
            "Height": self.height,
            "Mass": self.mass,
            "Volume": self.volume,
            "Relative Width": self.relative_width,
            "Relative Height": self.relative_height,
            "Relative Length": self.relative_length,
            "Relative Mass": self.relative_mass,
            "Relative Volume": self.relative_volume
        }


class Demand: 

    def __init__(self, folder_name:str, instance_name:str, customer_id:int, type:str, quantity:int):
        
        self.folder_name = folder_name
        self.instance_name = instance_name
        self.customer_id = customer_id
        self.type = type
        self.quantity = quantity
    
    def __print__(self):    
        print("Instance Name: ", self.instance_name)
        print("Customer ID: ", self.customer_id)   
        print("Type: ", self.type)
        print("Quantity: ", self.quantity)

    def to_dict(self):
        """ Convert instance data to a dictionary for DataFrame storage """
    
        return {
            "Folder Name": self.folder_name,
            "Instance Name": self.instance_name,
            "Customer ID": self.customer_id,
            "Type": self.type,
            "Quantity": self.quantity
        }

class Instance:
    def __init__(self, file_path: str,  standardize: bool):
        """ Initialize instance by reading the file and extracting data """
        self.file_path = file_path
        self.folder_name = os.path.basename(os.path.dirname(file_path))
        self.num_customers = 0
        self.num_items = 0
        self.num_item_types = 0
        self.num_vehicles = 0
        self.time_windows = 0
        self.vehicle_capacity = 0
        self.cargoSpace_Length = 0
        self.cargoSpace_Width = 0
        self.cargoSpace_Height = 0

        self.items = []  # Store item details for calculations
        self.demands = []  # Store customer demands
        self.aggregated_demands = []

        # Divider for unifiying units 
        if self.folder_name in ["Ceschia_et_al_2013","Moura_Oliveira_2009"]:
            self.divider = 10
        else: 
            self.divider = 1 # Default value is 1, no need to change for most instances

        self.parse_file()

        #Calculate cargo volume
        self.calculate_complete_volume()


        # Transform items and demands to DataFrames for easier manipulation
        self.items = pd.DataFrame([item.to_dict() for item in self.items])
        self.demands = pd.DataFrame([demand.to_dict() for demand in self.demands])
        self.aggregated_demands = pd.DataFrame(self.aggregated_demands)

        if standardize:
            self.standardize_data()

    def parse_file(self):
        """ Parses the instance file to extract relevant details """
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        section = None  # Keep track of the current section being read
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue

            # Identify sections based on keywords
            if "Name" in line:
                self.name = parts[1]
            elif "Number_of_Customers" in line:
                self.num_customers = int(parts[1])
            elif "Number_of_Items" in line:
                self.num_items = int(parts[1])
            elif "Number_of_ItemTypes" in line:
                self.num_item_types = int(parts[1])
            elif "Number_of_Vehicles" in line:
                self.num_vehicles = int(parts[1])
            elif "TimeWindows" in line:
                self.time_windows = int(parts[1])
            elif "VEHICLE" in line:
                section = "VEHICLE"
                flag = False
            elif "ITEMS" in line:
                section = "ITEMS"
                flag = True
            elif "DEMANDS PER CUSTOMER" in line:
                section = "DEMANDS"
                flag = True
            else:
                # Process each section accordingly
                if flag == True:
                    flag = False
                else:
                    if section == "VEHICLE":
                        if "Mass_Capacity" in line:
                            self.vehicle_capacity = int(parts[1])
                        elif "CargoSpace_Length" in line:
                            self.cargoSpace_Length = int(parts[1])/self.divider
                        elif "CargoSpace_Width" in line:
                            self.cargoSpace_Width = int(parts[1])/self.divider
                        elif "CargoSpace_Height" in line:
                            self.cargoSpace_Height = int(parts[1])/self.divider

                    elif section == "ITEMS":
                        # Extract item details
                        item = Item(self.folder_name, self.name, parts[0], float(parts[1])/self.divider, float(parts[2])/self.divider, float(parts[3])/self.divider, float(parts[4]))
                        item.caclulate_relative_values(self.cargoSpace_Length, self.cargoSpace_Width, self.cargoSpace_Height, self.vehicle_capacity)
                        self.items.append(item)

                    elif section == "DEMANDS":
                        self.cargo_volume = self.cargoSpace_Length * self.cargoSpace_Width * self.cargoSpace_Height
                        # Extract demand per customer
                        for i in range(1, len(parts), 2):
                            demand = Demand(self.folder_name, self.name, parts[0], parts[i], int(parts[i + 1]))
                            self.demands.append(demand)
                        
                        mass_aggregate = 0
                        volume_aggregate = 0
                        quantity_aggregate = 0
                        for i in range(1, len(parts), 2):
                                for item in self.items:
                                    if item.type == parts[i]:
                                        quantity_aggregate += int(parts[i + 1])
                                        mass_aggregate += item.mass * int(parts[i + 1])
                                        volume_aggregate += item.volume * int(parts[i + 1])

                        agg_demand = {"Folder Name": self.folder_name, 
                                      "Instance Name": self.name,
                                      "Customer ID": parts[0],
                                      "Agg Quantity": quantity_aggregate,
                                      "Agg Mass": mass_aggregate,
                                      "Agg Volume": volume_aggregate,
                                      "Agg Volume Ratio": volume_aggregate / self.cargo_volume,
                                      "Agg Mass Ratio": mass_aggregate / self.vehicle_capacity}
                        self.aggregated_demands.append(agg_demand)


    def calculate_complete_volume(self):

        self.vehicle_lower_bound_volume = 0
        self.vehicle_lower_bound_mass = 0

        for demand in self.demands:
            for item in self.items:
                if item.type == demand.type:
                    self.vehicle_lower_bound_volume  += item.volume * demand.quantity
                    self.vehicle_lower_bound_mass += item.mass * demand.quantity


        self.vehicle_lower_bound_volume = self.vehicle_lower_bound_volume / self.cargo_volume
        self.vehicle_lower_bound_mass = self.vehicle_lower_bound_mass / self.vehicle_capacity
        self.vehicle_coverage_mass = self.vehicle_lower_bound_volume / self.num_vehicles
        self.vehicle_coverage_volume = self.vehicle_lower_bound_volume / self.num_vehicles

    def standardize_data(self):

        for column in ['Length', 'Width', 'Height', 'Mass', 'Volume']:
            column_name = f"{column}_standardized"
            self.items[column_name] = (self.items[column] - self.items[column].mean()) / self.items[column].std()

    def to_dict(self):
        """ Convert instance data to a dictionary for DataFrame storage """
        return {
            "Folder Name": self.folder_name,
            "Instance Name": self.name,
            "Number of Customers": self.num_customers,
            "Number of Items": self.num_items,
            "Number of Item Types": self.num_item_types,
            "Number of Vehicles": self.num_vehicles,
            "Time Windows": self.time_windows,
            "Vehicle Capacity": self.vehicle_capacity,
            "Cargo Length": self.cargoSpace_Length,
            "Cargo Width": self.cargoSpace_Width,
            "Cargo Height": self.cargoSpace_Height,
            "Cargo Volume ": round(self.cargo_volume,2),
            "Vehicle LB Volume": round(self.vehicle_lower_bound_volume,2),
            "Vehicle LB Mass": round(self.vehicle_lower_bound_mass,2),
            "Vehicle Coverage Mass": round(self.vehicle_coverage_mass,2),
            "Vehicle Coverage Volume": round(self.vehicle_coverage_volume,2)
            #"Relative Volume": round(self.relative_volume, 2),s
            #"Packed Vehicle Volume": self.packed_volume
        }
