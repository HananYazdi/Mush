import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from scipy.stats import norm, multivariate_normal
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample

def analyze_mahzor_trends(logs_df):
    """Analyze trends and statistics for each Mahzor_id."""
    if logs_df is None or len(logs_df) == 0:
        return None
    
    # Group by Mahzor_id and Days_after_plant
    mahzor_stats = {}
    
    for mahzor_id, group in logs_df.groupby('Mahzor_id'):
        # Convert to Python int
        mahzor_id = ensure_int(mahzor_id)
        
        # Calculate daily statistics
        daily_stats = group.groupby('Days_after_plant').agg({
            'AIR_temp': ['mean', 'std', 'min', 'max'],
            'Substrate_temp': ['mean', 'std', 'min', 'max'],
            'RH_Humadity': ['mean', 'std', 'min', 'max'],
            'CO2': ['mean', 'std', 'min', 'max']
        }).reset_index()
        
        # Find the day when if_bagged becomes False
        bagged_days = group[group['if_bagged'] == True]['Days_after_plant'].max() if True in group['if_bagged'].values else 0
        # Convert to Python int
        bagged_days = ensure_int(bagged_days)
        
        # Find the first day when Katif appears and its pattern
        katif_data = group[group['Katif'] > 0]
        first_katif_day = katif_data['Days_after_plant'].min() if len(katif_data) > 0 else None
        # Convert to Python int if not None
        if first_katif_day is not None:
            first_katif_day = ensure_int(first_katif_day)
            
        katif_pattern = {}
        if len(katif_data) > 0:
            for index, row in katif_data.iterrows():
                # Convert to Python int and float
                day = ensure_int(row['Days_after_plant'])
                katif_val = ensure_float(row['Katif'])
                katif_pattern[day] = katif_val
        
        # Calculate trends with higher order polynomials for better fit
        trends = {}
        for col in ['AIR_temp', 'Substrate_temp', 'RH_Humadity', 'CO2']:
            if len(daily_stats) > 2:
                x = daily_stats['Days_after_plant'].apply(ensure_float).values
                y = daily_stats[col]['mean'].apply(ensure_float).values
                # Use quadratic fit for better trend matching
                z = np.polyfit(x, y, 2)
                # Convert coefficients to Python floats
                z = [ensure_float(coef) for coef in z]
                
                trends[col] = {
                    'coef': z,
                    'min': ensure_float(daily_stats[col]['min'].min()),
                    'max': ensure_float(daily_stats[col]['max'].max())
                }
            else:
                trends[col] = {
                    'coef': [0.0, 0.0, ensure_float(daily_stats[col]['mean'].iloc[0])],
                    'min': ensure_float(daily_stats[col]['min'].min()),
                    'max': ensure_float(daily_stats[col]['max'].max())
                }
        
        mahzor_stats[mahzor_id] = {
            'daily_stats': daily_stats,
            'trends': trends,
            'total_days': ensure_int(group['Days_after_plant'].max()),
            'bagged_days': bagged_days,
            'first_katif_day': first_katif_day,
            'katif_pattern': katif_pattern
        }
    
    return mahzor_stats

def generate_correlated_data(n_samples, means, cov_matrix):
    """Generate correlated data using multivariate normal distribution."""
    return multivariate_normal.rvs(mean=means, cov=cov_matrix, size=n_samples)

def bootstrap_data(existing_data, n_samples):
    """Generate new data using bootstrapping from existing data."""
    if existing_data is None or len(existing_data) == 0:
        return None
    
    # Resample with replacement
    bootstrapped = resample(existing_data, n_samples=n_samples, replace=True)
    return bootstrapped

def generate_iteration_data(existing_df, logs_df, target_count=500):
    """Generate iteration data with advanced statistical methods."""
    if existing_df is not None and len(existing_df) > 0:
        current_count = len(existing_df)
        new_count = target_count - current_count
        
        # Analyze existing data patterns
        mahzor_stats = analyze_mahzor_trends(logs_df)
        
        # Calculate room-specific patterns
        room_patterns = existing_df.groupby('Room_number').agg({
            'Substrate': ['mean', 'std', 'min', 'max'],
            'mushroom_type': 'first'
        })
        
        # Generate new data
        new_data = []
        for i in range(new_count):
            mahzor_id = current_count + i + 1
            iteration_id = current_count + i + 1
            
            # Random room selection with some preference for recent rooms
            recent_rooms = existing_df['Room_number'].tail(10).value_counts()
            room_weights = recent_rooms / recent_rooms.sum()
            room_number = np.random.choice(room_weights.index, p=room_weights) if len(room_weights) > 0 else random.choice([3, 4, 5])
            
            # Generate substrate with more variation
            if room_number in room_patterns.index:
                room_stats = room_patterns.loc[room_number]
                base_substrate = room_stats['Substrate']['mean']
                std_substrate = room_stats['Substrate']['std']
                # Add more variation while staying within bounds
                substrate = round(np.random.normal(base_substrate, std_substrate * 1.5), 1)
                substrate = max(room_stats['Substrate']['min'], min(room_stats['Substrate']['max'], substrate))
            else:
                substrate = random.choice([80.0, 160.0, 237.5, 240.0])
            
            # Generate start date with some randomness
            if i == 0:
                last_date = existing_df['Start_date'].max()
                # Random spacing between 5-9 days
                start_date = last_date + timedelta(days=random.randint(5, 9))
            else:
                # Random spacing between 5-9 days
                start_date = new_data[-1]['Start_date'] + timedelta(days=random.randint(5, 9))
            
            new_data.append({
                'MAHZOR_ID': mahzor_id,
                'mushroom_type': random.randint(1, 3),  # More variety in mushroom types
                'Iteration_ID': iteration_id,
                'Start_date': start_date,
                'Room_number': room_number,
                'Substrate': substrate
            })
        
        new_df = pd.DataFrame(new_data)
        return pd.concat([existing_df, new_df], ignore_index=True)
    else:
        # Generate initial data if no existing data
        new_data = []
        start_date = datetime.now() - timedelta(days=30)
        for i in range(target_count):
            mahzor_id = i + 1
            iteration_id = i + 1
            room_number = random.choice([3, 4, 5])
            substrate = random.choice([80.0, 160.0, 237.5, 240.0])
            # Random spacing between 5-9 days
            start_date = start_date + timedelta(days=random.randint(5, 9))
            
            new_data.append({
                'MAHZOR_ID': mahzor_id,
                'mushroom_type': random.randint(1, 3),
                'Iteration_ID': iteration_id,
                'Start_date': start_date,
                'Room_number': room_number,
                'Substrate': substrate
            })
        
        return pd.DataFrame(new_data)

def ensure_datetime(dt_value):
    """Convert various date formats to datetime objects."""
    if isinstance(dt_value, datetime):
        return dt_value
    elif isinstance(dt_value, str):
        # Try different common formats
        formats = [
            '%Y-%m-%d %H:%M:%S', 
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_value, fmt)
            except ValueError:
                continue
        
        # If all formats fail, try pandas to_datetime
        try:
            return pd.to_datetime(dt_value).to_pydatetime()
        except:
            raise ValueError(f"Unable to parse date: {dt_value}")
    else:
        # Try to convert pandas timestamp or other date-like objects
        try:
            return pd.to_datetime(dt_value).to_pydatetime()
        except:
            raise ValueError(f"Unable to convert to datetime: {dt_value} (type: {type(dt_value)})")

def ensure_int(value):
    """Convert numpy integer types to Python int."""
    if hasattr(value, 'dtype') and np.issubdtype(value.dtype, np.integer):
        return int(value)
    return value

def ensure_float(value):
    """Convert numpy float types to Python float."""
    if hasattr(value, 'dtype') and np.issubdtype(value.dtype, np.floating):
        return float(value)
    return value

def generate_logs_data(existing_df, iteration_df, target_count=10000):
    """Generate logs data with proper date correlation and natural variation."""
    if existing_df is not None and len(existing_df) > 0:
        current_count = len(existing_df)
        new_count = target_count - current_count
        
        # Analyze existing data patterns
        mahzor_stats = analyze_mahzor_trends(existing_df)
        
        # Get the last Mahzor_id from existing data
        last_mahzor_id = ensure_int(existing_df['Mahzor_id'].max())
        
        # Create lookup for iteration start dates (ensure case-sensitive matching)
        iteration_start_dates = {}
        for _, row in iteration_df.iterrows():
            # Convert to int for safe matching with Mahzor_id
            mahzor_id_key = int(row['MAHZOR_ID'])
            # Ensure proper date type
            start_date = ensure_datetime(row['Start_date'])
            iteration_start_dates[mahzor_id_key] = start_date
        
        # Generate new data
        new_data = []
        for i in range(new_count):
            # Use sequential Mahzor_id with 25 logs per batch
            mahzor_id = last_mahzor_id + (i // 25) + 1
            days_after_plant = i % 25
            
            # Get the start date for this mahzor from iteration table
            if mahzor_id in iteration_start_dates:
                base_date = iteration_start_dates[mahzor_id]
            else:
                # Fallback if not found - use the base date from a found mahzor or default
                found_keys = [k for k in iteration_start_dates.keys() if k <= mahzor_id]
                if found_keys:
                    closest_key = max(found_keys)
                    base_date = iteration_start_dates[closest_key] + timedelta(days=int(mahzor_id - closest_key) * 7)
                else:
                    base_date = datetime.now() - timedelta(days=30)
            
            # Calculate true date based on start date and days_after_plant (ensure int conversion)
            true_date = base_date + timedelta(days=int(days_after_plant))
            
            # Add hours within the day - create multiple logs per day
            hour_offset = (i % 12) * 2  # 12 readings per day, 2 hours apart
            
            # Add some randomness to hour offset (±30 minutes)
            hour_offset += random.uniform(-0.5, 0.5)
            
            # Final date with hours
            date = true_date + timedelta(hours=hour_offset)
            hour = date.strftime("%H:%M")
            
            if mahzor_id in mahzor_stats:
                stats = mahzor_stats[mahzor_id]
                
                # Generate values with more natural variation
                values = {}
                for col in ['AIR_temp', 'Substrate_temp', 'RH_Humadity', 'CO2']:
                    trend = stats['trends'][col]
                    
                    # Base value from trend - convert to Python types for safety
                    a = ensure_float(trend['coef'][0])
                    b = ensure_float(trend['coef'][1])
                    c = ensure_float(trend['coef'][2])
                    days = ensure_float(days_after_plant)
                    
                    base_value = a * (days ** 2) + b * days + c
                    
                    # Time of day variation - diurnal patterns
                    hour_num = date.hour
                    if col == 'AIR_temp':
                        # Air temp varies more during the day
                        time_variation = -2 + 4 * np.sin(np.pi * (hour_num - 6) / 12)
                    elif col == 'Substrate_temp':
                        # Substrate follows air with lag and dampening
                        time_variation = -1 + 2 * np.sin(np.pi * (hour_num - 8) / 12)
                    elif col == 'RH_Humadity':
                        # Humidity is opposite to temperature
                        time_variation = 0.05 - 0.1 * np.sin(np.pi * (hour_num - 6) / 12)
                    else:  # CO2
                        # CO2 rises in evening/night when photosynthesis stops
                        time_variation = 100 - 200 * np.sin(np.pi * (hour_num - 6) / 12)
                    
                    # Convert to Python float
                    time_variation = ensure_float(time_variation)
                    
                    # Day-to-day variation
                    daily_variation = np.sin(days_after_plant * 0.4) * random.uniform(0.5, 1.5)
                    daily_variation = ensure_float(daily_variation)
                    
                    # Random noise component
                    noise_scale = 0.8 if col != 'RH_Humadity' else 0.03
                    noise = random.normalvariate(0, noise_scale)
                    
                    value = base_value + time_variation + daily_variation + noise
                    
                    # Ensure within reasonable bounds
                    min_val = ensure_float(trend['min'])
                    max_val = ensure_float(trend['max'])
                    value = max(min_val, min(max_val, value))
                    
                    # Round appropriately
                    values[col] = round(value, 1 if col != 'RH_Humadity' else 3)
                
                # Determine if_bagged with some randomness
                bagged_days = ensure_int(stats['bagged_days'])
                if_bagged = days_after_plant <= bagged_days
                
                # Handle edge cases around bag removal day
                if days_after_plant == bagged_days:
                    # 70% chance bag is removed on expected day
                    if_bagged = random.random() < 0.7
                elif days_after_plant == bagged_days + 1:
                    # 20% chance bag is still on one day after
                    if_bagged = random.random() < 0.2
                elif days_after_plant == bagged_days - 1:
                    # 10% chance bag is removed one day early
                    if_bagged = random.random() < 0.9
                
                # Generate Katif with realistic patterns
                if days_after_plant in stats['katif_pattern']:
                    base_katif = stats['katif_pattern'][days_after_plant]
                    # Add some noise to observed values
                    katif = round(base_katif * random.uniform(0.9, 1.1), 3)
                elif stats['first_katif_day'] is not None and days_after_plant >= stats['first_katif_day']:
                    # Realistic Katif growth curve after first appearance
                    # Start with initial value and grow non-linearly
                    days_since_first = days_after_plant - stats['first_katif_day']
                    
                    # Sigmoid growth curve for more realism
                    growth_factor = 1 / (1 + np.exp(-0.5 * (days_since_first - 2)))
                    
                    # Base starting value
                    base_katif = random.choice([19, 21.2, 25, 34.445, 44.5])
                    
                    # Apply growth with some randomness
                    max_growth = random.uniform(1.5, 2.5)  # Maximum multiplier
                    katif = round(base_katif * (1 + (max_growth - 1) * growth_factor), 3)
                    
                    # Add random variation
                    katif = round(katif * random.uniform(0.95, 1.05), 3)
                else:
                    katif = 0
            else:
                # Generate values with realistic patterns
                # Time-of-day effect
                hour_num = date.hour
                time_effect_temp = -2 + 4 * np.sin(np.pi * (hour_num - 6) / 12)
                time_effect_humidity = 0.05 - 0.1 * np.sin(np.pi * (hour_num - 6) / 12)
                time_effect_co2 = 100 - 200 * np.sin(np.pi * (hour_num - 6) / 12)
                
                # Growth stage effect (days)
                day_effect_temp = np.sin(days_after_plant * 0.4) * random.uniform(1, 2)
                day_effect_humidity = -np.sin(days_after_plant * 0.3) * random.uniform(0.05, 0.1)
                day_effect_co2 = np.cos(days_after_plant * 0.3) * random.uniform(200, 300)
                
                values = {
                    'AIR_temp': round(15.5 + time_effect_temp + day_effect_temp + random.normalvariate(0, 0.8), 1),
                    'Substrate_temp': round(14.5 + (time_effect_temp * 0.5) + (day_effect_temp * 0.3) + random.normalvariate(0, 0.4), 1),
                    'RH_Humadity': round(0.8 + time_effect_humidity + day_effect_humidity + random.normalvariate(0, 0.02), 3),
                    'CO2': round(700 + time_effect_co2 + day_effect_co2 + random.normalvariate(0, 50), 0)
                }
                
                # Realistic bag patterns - bags stay on for 10-14 days
                bag_days = random.randint(10, 14)
                if_bagged = days_after_plant <= bag_days
                
                # Handle edge cases
                if days_after_plant == bag_days:
                    if_bagged = random.random() < 0.7  # 70% chance bag removed on target day
                
                # Realistic Katif patterns
                first_katif_day = random.randint(18, 22)
                if days_after_plant < first_katif_day:
                    katif = 0
                else:
                    days_since_first = days_after_plant - first_katif_day
                    # Initial values with some variation
                    base_values = [19, 21.2, 25, 34.445, 44.5]
                    # Weight toward smaller values at first
                    weights = [5-min(days_since_first, 4), 4-min(days_since_first, 3), 
                               3, 2+min(days_since_first, 2), 1+min(days_since_first, 3)]
                    base_katif = random.choices(base_values, weights=weights, k=1)[0]
                    
                    # Growth curve
                    growth_factor = 1 / (1 + np.exp(-0.5 * (days_since_first - 2)))
                    max_growth = random.uniform(1.5, 2.5)
                    katif = round(base_katif * (1 + (max_growth - 1) * growth_factor), 3)
            
            new_data.append({
                'Log_id': current_count + i + 1,
                'Mahzor_id': mahzor_id,
                'Days_after_plant': days_after_plant,
                'Date': date,
                'Hour': hour,
                'AIR_temp': values['AIR_temp'],
                'Substrate_temp': values['Substrate_temp'],
                'RH_Humadity': values['RH_Humadity'],
                'CO2': values['CO2'],
                'day_hours': 8,
                'Katif': katif,
                'if_bagged': if_bagged
            })
        
        new_df = pd.DataFrame(new_data)
        return pd.concat([existing_df, new_df], ignore_index=True)
    else:
        # Generate initial data if no existing data
        new_data = []
        
        # Verify we have iteration data
        if iteration_df is not None and len(iteration_df) > 0:
            # Create lookup for iteration start dates
            mahzor_start_dates = {}
            for _, row in iteration_df.iterrows():
                mahzor_id_key = int(row['MAHZOR_ID'])
                # Ensure proper date type
                start_date = ensure_datetime(row['Start_date'])
                mahzor_start_dates[mahzor_id_key] = start_date
        else:
            # Generate reasonable start dates if no iteration data
            mahzor_count = target_count // 25 + 1
            mahzor_start_dates = {}
            base_date = datetime.now() - timedelta(days=60)
            
            for mahzor_id in range(1, mahzor_count + 1):
                mahzor_start_dates[mahzor_id] = base_date + timedelta(days=mahzor_id * random.randint(5, 9))
        
        for i in range(target_count):
            mahzor_id = (i // 25) + 1
            days_after_plant = i % 25
            
            # Get base date for this mahzor
            if mahzor_id in mahzor_start_dates:
                base_date = mahzor_start_dates[mahzor_id]
            else:
                # Fallback if not found - use the base date from a found mahzor or default
                found_keys = [k for k in mahzor_start_dates.keys() if k <= mahzor_id]
                if found_keys:
                    closest_key = max(found_keys)
                    base_date = mahzor_start_dates[closest_key] + timedelta(days=(mahzor_id - closest_key) * 7)
                else:
                    base_date = datetime.now() - timedelta(days=30)
            
            # Calculate true date based on start date and days_after_plant
            true_date = base_date + timedelta(days=days_after_plant)
            
            # Multiple logs per day with some randomness
            hour_offset = (i % 12) * 2 + random.uniform(-0.5, 0.5)
            date = true_date + timedelta(hours=hour_offset)
            hour = date.strftime("%H:%M")
            
            # Time-of-day effect
            hour_num = date.hour
            time_effect_temp = -2 + 4 * np.sin(np.pi * (hour_num - 6) / 12)
            time_effect_humidity = 0.05 - 0.1 * np.sin(np.pi * (hour_num - 6) / 12)
            time_effect_co2 = 100 - 200 * np.sin(np.pi * (hour_num - 6) / 12)
            
            # Growth stage effect (days)
            day_effect_temp = np.sin(days_after_plant * 0.4) * random.uniform(1, 2)
            day_effect_humidity = -np.sin(days_after_plant * 0.3) * random.uniform(0.05, 0.1)
            day_effect_co2 = np.cos(days_after_plant * 0.3) * random.uniform(200, 300)
            
            # Generate values with realistic patterns
            values = {
                'AIR_temp': round(15.5 + time_effect_temp + day_effect_temp + random.normalvariate(0, 0.8), 1),
                'Substrate_temp': round(14.5 + (time_effect_temp * 0.5) + (day_effect_temp * 0.3) + random.normalvariate(0, 0.4), 1),
                'RH_Humadity': round(0.8 + time_effect_humidity + day_effect_humidity + random.normalvariate(0, 0.02), 3),
                'CO2': round(700 + time_effect_co2 + day_effect_co2 + random.normalvariate(0, 50), 0)
            }
            
            # Realistic bag and Katif patterns
            bag_days = random.randint(10, 14)
            if_bagged = days_after_plant <= bag_days
            
            # Handle edge cases
            if days_after_plant == bag_days:
                if_bagged = random.random() < 0.7
                
            # Katif patterns
            first_katif_day = random.randint(18, 22)
            if days_after_plant < first_katif_day:
                katif = 0
            else:
                days_since_first = days_after_plant - first_katif_day
                base_values = [19, 21.2, 25, 34.445, 44.5]
                weights = [5-min(days_since_first, 4), 4-min(days_since_first, 3), 
                           3, 2+min(days_since_first, 2), 1+min(days_since_first, 3)]
                base_katif = random.choices(base_values, weights=weights, k=1)[0]
                
                # Growth curve
                growth_factor = 1 / (1 + np.exp(-0.5 * (days_since_first - 2)))
                max_growth = random.uniform(1.5, 2.5)
                katif = round(base_katif * (1 + (max_growth - 1) * growth_factor), 3)
            
            new_data.append({
                'Log_id': i + 1,
                'Mahzor_id': mahzor_id,
                'Days_after_plant': days_after_plant,
                'Date': date,
                'Hour': hour,
                'AIR_temp': values['AIR_temp'],
                'Substrate_temp': values['Substrate_temp'],
                'RH_Humadity': values['RH_Humadity'],
                'CO2': values['CO2'],
                'day_hours': 8,
                'Katif': katif,
                'if_bagged': if_bagged
            })
        
        return pd.DataFrame(new_data)

def main():
    try:
        # Try to read existing file
        existing_file = 'ml/data_logs.xlsx'
        try:
            iteration_df = pd.read_excel(existing_file, sheet_name='Iteration_table')
            logs_df = pd.read_excel(existing_file, sheet_name='LOGS')
            
            # Ensure date columns are datetime objects
            if 'Start_date' in iteration_df.columns:
                iteration_df['Start_date'] = iteration_df['Start_date'].apply(ensure_datetime)
            if 'Date' in logs_df.columns:
                logs_df['Date'] = logs_df['Date'].apply(ensure_datetime)
                
            print(f"Successfully loaded existing data: {len(iteration_df)} iterations, {len(logs_df)} logs")
        except FileNotFoundError:
            print("No existing data found. Starting from scratch.")
            iteration_df = None
            logs_df = None
        except Exception as e:
            print(f"Error loading existing data: {str(e)}")
            print("Starting from scratch.")
            iteration_df = None
            logs_df = None
        
        # Generate new data
        print("Generating new data...")
        iteration_df = generate_iteration_data(iteration_df, logs_df)
        logs_df = generate_logs_data(logs_df, iteration_df)
        
        # Verify date correlation
        if logs_df is not None and iteration_df is not None and len(logs_df) > 0 and len(iteration_df) > 0:
            # Create a sample to check
            sample_size = min(5, len(logs_df))
            sample_indices = random.sample(range(len(logs_df)), sample_size)
            
            print("Verifying date correlation for sample logs:")
            all_correct = True
            
            for idx in sample_indices:
                log_row = logs_df.iloc[idx]
                mahzor_id = ensure_int(log_row['Mahzor_id'])
                days_after_plant = ensure_int(log_row['Days_after_plant'])
                log_date = ensure_datetime(log_row['Date'])
                
                # Find corresponding iteration
                iter_row = iteration_df[iteration_df['MAHZOR_ID'] == mahzor_id]
                if len(iter_row) > 0:
                    start_date = ensure_datetime(iter_row.iloc[0]['Start_date'])
                    # Convert days_after_plant to int to avoid numpy type errors
                    expected_date = start_date + timedelta(days=int(days_after_plant))
                    
                    # Check if the log date is approximately correct (same day)
                    log_date_only = log_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    expected_date_only = expected_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    match = log_date_only == expected_date_only
                    if not match:
                        all_correct = False
                        
                    print(f"Mahzor {mahzor_id}, Day {days_after_plant}:")
                    print(f"  Start date: {start_date.date()}")
                    print(f"  Expected: {expected_date.date()}")
                    print(f"  Actual: {log_date.date()}")
                    print(f"  Correct: {match} {'✓' if match else '✗'}")
            
            if all_correct:
                print("\nAll date correlations correct! ✓")
            else:
                print("\nSome date correlations are incorrect! Please check the data. ✗")
        
        # Save to new file
        output_file = 'data_logs_extended.xlsx'
        with pd.ExcelWriter(output_file) as writer:
            iteration_df.to_excel(writer, sheet_name='Iteration_table', index=False)
            logs_df.to_excel(writer, sheet_name='LOGS', index=False)
        
        print(f"\nSuccessfully generated extended data in {output_file}")
        print(f"Total iterations: {len(iteration_df)}")
        print(f"Total logs: {len(logs_df)}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 