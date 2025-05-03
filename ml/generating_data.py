import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class FarmDataGenerator:
    def __init__(self, farm_file, logs_file):
        self.farm_file = farm_file
        self.logs_file = logs_file
        
    def load_data(self):
        # Load farm data
        with open(self.farm_file, 'r') as f:
            self.farm_data = json.load(f)
            
        # Load logs data
        with open(self.logs_file, 'r') as f:
            logs_str = f.read().strip('"').replace('\\"', '"')
            self.logs_data = json.loads(logs_str)
        
        # Convert to DataFrames
        self.farm_df = pd.DataFrame.from_dict(self.farm_data, orient='index')
        self.logs_df = pd.DataFrame(self.logs_data)
        
        # Clean and convert data types
        self.farm_df = self.farm_df.apply(pd.to_numeric, errors='ignore')
        self.logs_df = self.logs_df.apply(pd.to_numeric, errors='ignore')

    def find_missing_log_days(self):
        """Find missing days for each Mahzor_id"""
        missing_combinations = []
        existing_combinations = set()
        
        # Create set of existing Mahzor_id and Days_after_plant combinations
        for log in self.logs_data:
            existing_combinations.add((log['Mahzor_id'], log['Days_after_plant']))
        
        # Only include farms that have 'MAHZOR_ID'
        mahzor_ids = sorted(list(set(
            farm['MAHZOR_ID'] for farm in self.farm_data.values() if 'MAHZOR_ID' in farm
        )))
        
        # Find missing combinations
        for mahzor_id in mahzor_ids:
            for day in range(26):  # 0-25 days
                if (mahzor_id, day) not in existing_combinations:
                    missing_combinations.append((mahzor_id, day))
        
        return missing_combinations, mahzor_ids, existing_combinations

    def generate_log_data(self, num_logs=10000):
        max_log_id = max(log['Log_id'] for log in self.logs_data)
        
        # Get statistical properties from existing data
        temp_mean = self.logs_df['AIR_temp'].mean()
        temp_std = self.logs_df['AIR_temp'].std()
        rh_mean = self.logs_df['RH_Humadity'].mean()
        rh_std = self.logs_df['RH_Humadity'].std()
        co2_mean = self.logs_df['CO2'].mean()
        co2_std = self.logs_df['CO2'].std()
        
        # Get missing combinations and valid Mahzor_ids
        missing_combinations, valid_mahzor_ids, existing_combinations = self.find_missing_log_days()
        
        new_logs = []
        log_id = max_log_id + 1
        
        # First, fill in missing combinations
        for mahzor_id, days_after_plant in missing_combinations:
            # Find corresponding farm
            farm = next((f for f in self.farm_data.values() 
                        if 'MAHZOR_ID' in f and f['MAHZOR_ID'] == mahzor_id), None)
            if not farm:
                continue
                
            # Generate environmental variables
            air_temp = np.random.normal(temp_mean, temp_std)
            substrate_temp = air_temp + np.random.normal(0, 0.5)
            if days_after_plant == 0:
                substrate_temp = np.random.uniform(-2.5, -0.8)
                
            rh = np.clip(np.random.normal(rh_mean, rh_std), 0.6, 0.99)
            co2 = np.clip(np.random.normal(co2_mean, co2_std), 450, 1500)
            
            # Determine bagging state
            if_bagged = 1.0 if days_after_plant <= 12 else 0.0
            
            # Generate Katif values
            katif = None
            if days_after_plant >= 15 and np.random.random() < 0.7:
                katif = np.clip(np.random.normal(20, 8), 0, 45)
            
            # Generate date
            start_date = datetime.strptime(farm['Start_date'], "%Y-%m-%d %H:%M:%S")
            log_date = start_date + timedelta(days=days_after_plant)
            
            new_log = {
                "Log_id": int(log_id),
                "Mahzor_id": int(mahzor_id),
                "Days_after_plant": int(days_after_plant),
                "Date": int(log_date.timestamp() * 1000),
                "Hour": f"{np.random.randint(8,20):02d}:00:00",
                "AIR_temp": float(round(air_temp, 1)),
                "Substrate_temp": float(round(substrate_temp, 1)),
                "RH_Humadity": float(round(rh, 3)),
                "CO2": float(round(co2, 1)),
                "day_hours": 8.0,
                "Katif": round(katif, 1) if katif is not None else None,
                "if_bagged": if_bagged
            }
            new_logs.append(new_log)
            log_id += 1
            
            if len(new_logs) >= num_logs:
                break
        
        # If we still need more logs, add additional ones for random valid Mahzor_ids
        while len(new_logs) < num_logs:
            mahzor_id = np.random.choice(valid_mahzor_ids)
            days_after_plant = np.random.randint(0, 26)
            
            # Skip if this combination already exists in original data
            if (mahzor_id, days_after_plant) in existing_combinations:
                continue
                
            # Find corresponding farm
            farm = next((f for f in self.farm_data.values() 
                        if 'MAHZOR_ID' in f and f['MAHZOR_ID'] == mahzor_id), None)
            if not farm:
                continue
            
            # Generate environmental variables
            air_temp = np.random.normal(temp_mean, temp_std)
            substrate_temp = air_temp + np.random.normal(0, 0.5)
            if days_after_plant == 0:
                substrate_temp = np.random.uniform(-2.5, -0.8)
                
            rh = np.clip(np.random.normal(rh_mean, rh_std), 0.6, 0.99)
            co2 = np.clip(np.random.normal(co2_mean, co2_std), 450, 1500)
            
            # Determine bagging state
            if_bagged = 1.0 if days_after_plant <= 12 else 0.0
            
            # Generate Katif values
            katif = None
            if days_after_plant >= 15 and np.random.random() < 0.7:
                katif = np.clip(np.random.normal(20, 8), 0, 45)
            
            # Generate date
            start_date = datetime.strptime(farm['Start_date'], "%Y-%m-%d %H:%M:%S")
            log_date = start_date + timedelta(days=days_after_plant)
            
            new_log = {
                "Log_id": int(log_id),
                "Mahzor_id": int(mahzor_id),
                "Days_after_plant": int(days_after_plant),
                "Date": int(log_date.timestamp() * 1000),
                "Hour": f"{np.random.randint(8,20):02d}:00:00",
                "AIR_temp": float(round(air_temp, 1)),
                "Substrate_temp": float(round(substrate_temp, 1)),
                "RH_Humadity": float(round(rh, 3)),
                "CO2": float(round(co2, 1)),
                "day_hours": 8.0,
                "Katif": round(katif, 1) if katif is not None else None,
                "if_bagged": if_bagged
            }
            new_logs.append(new_log)
            log_id += 1
        
        return new_logs

def main():
    try:
        # File paths
        farm_file = "ml/farm-management-86035-default-rtdb-FarmData-export.json"
        logs_file = "ml/farm-management-86035-default-rtdb-Logs-export.json"
        
        # Initialize and run generator
        generator = FarmDataGenerator(farm_file, logs_file)
        generator.load_data()
        
        # Generate new logs
        new_logs = generator.generate_log_data(10000)
        
        # Save logs data
        all_logs = generator.logs_data + new_logs
        
        # Sort by Mahzor_id and Days_after_plant
        all_logs.sort(key=lambda x: (x['Mahzor_id'], x['Days_after_plant']))
        
        with open("ml/farm-management-86035-default-rtdb-Logs-export-extended.json", 'w') as f:
            json.dump(all_logs, f, indent=2)
            
        print(f"Data generation completed successfully! Generated {len(new_logs)} new logs.")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()